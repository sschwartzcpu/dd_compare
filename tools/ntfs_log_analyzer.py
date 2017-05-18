import re
import sys

NTFS_SECTOR_SIZE = 0x200
NTFS_CLUSTER_SIZE = 0x1000

REGEX_REPL_ENTRY = re.compile('^([0-9a-fA-F]{12}) \[REPL ([0-9a-fA-F]{2}) ([0-9a-fA-F]{2})\]')
REGEX_FILL_ENTRY = re.compile('^([0-9a-fA-F]{12}) \[FILL ([0-9a-fA-F]{12}) ([0-9a-fA-F]{2})\]')


class LogAnalyzer:

    def __init__(self, image_file, partition_base_offset):
        """
        @type image_file: file
        @type partition_base_offset: int
        """
        self.image_file = image_file
        self.partition_base_offset = partition_base_offset

    def handle_indx_record(self, lines, last_line_reached):
        indx_record_sector_cnt = NTFS_CLUSTER_SIZE // NTFS_SECTOR_SIZE
        usn_words_in_header_cnt = 1 + indx_record_sector_cnt
        usn_words_in_header_relative_start_offset = 0x28
        usn_words_in_header_relative_end_offset = usn_words_in_header_relative_start_offset + (2 * usn_words_in_header_cnt) - 1
        usn_word_in_sector_relative_offsets = [NTFS_SECTOR_SIZE * (i + 1) - 2 for i in range(indx_record_sector_cnt)]

        relative_offset_mask = NTFS_CLUSTER_SIZE - 1
        base_offset_mask = ((2 ** 64) - 1) ^ relative_offset_mask
        aligned_word_mask = relative_offset_mask ^ 0x1

        line_num = 0
        base_offset = 0
        lowest_allowable_offset = 0
        usn_mask = 0
        old_usn_words = [0 for _ in range(usn_words_in_header_cnt)]
        new_usn_words = [0 for _ in range(usn_words_in_header_cnt)]
        fills = []

        while line_num < len(recent_lines):
            line = lines[line_num]
            repl_match = REGEX_REPL_ENTRY.match(line)
            match = (None, repl_match)[repl_match is not None]
            fill_match = REGEX_FILL_ENTRY.match(line)
            match = (match, fill_match)[fill_match is not None]
            if match is None:
                return 0, 0

            offset = int(match.group(1), 16)
            relative_offset = offset & relative_offset_mask

            if line_num == 0:
                base_offset = offset & base_offset_mask
                lowest_allowable_offset = base_offset

            if offset < lowest_allowable_offset:
                print('[LOG ERROR] Offsets don''t monotonically increase!')
                return 0, 0

            if offset & base_offset_mask != base_offset:
                return 0, 0

            if repl_match is not None:
                old_byte = int(repl_match.group(2), 16)
                new_byte = int(repl_match.group(3), 16)
                lowest_allowable_offset = offset + 1

            if fill_match is not None:
                end_offset = int(fill_match.group(2), 16)
                new_byte = int(fill_match.group(3), 16)
                lowest_allowable_offset = end_offset + 1

            if line_num == 0 and repl_match is None:
                return 0, 0

            if not usn_mask == (1 << (2 * usn_words_in_header_cnt)) - 1:
                if line_num == 0 and relative_offset & aligned_word_mask != usn_words_in_header_relative_start_offset:
                    return 0, 0

                if relative_offset >= usn_words_in_header_relative_start_offset and relative_offset <= usn_words_in_header_relative_end_offset:
                    usn_byte_index = relative_offset - usn_words_in_header_relative_start_offset
                    usn_word_index = usn_byte_index >> 1
                    usn_mask |= 1 << usn_byte_index
                    old_usn_words[usn_word_index] |= int(repl_match.group(2), 16) << (8 * (usn_byte_index & 0x1))
                    new_usn_words[usn_word_index] |= int(repl_match.group(3), 16) << (8 * (usn_byte_index & 0x1))

                # if relative_offset >= usn_words_in_header_relative_offset + 1:
                #     if not usn_mask & 0x00ff:
                #         self.image_file.seek(self.partition_base_offset + base_offset + usn_word_header_relative_offset)
                #         usn_byte = ord(self.image_file.read(1))
                #         usn_mask |= 0x00ff
                #         old_usn_word |= usn_byte
                #         new_usn_word |= usn_byte
                #     if not usn_mask & 0xff00:
                #         self.image_file.seek(self.partition_base_offset + base_offset + usn_word_header_relative_offset + 1)
                #         usn_byte = ord(self.image_file.read(1))
                #         usn_mask |= 0xff00
                #         old_usn_word |= usn_byte << 8
                #         new_usn_word |= usn_byte << 8

                if relative_offset <= usn_words_in_header_relative_end_offset:
                        line_num += 1
                        continue

            if repl_match is not None:
                if not relative_offset & aligned_word_mask == usn_word_in_sector_relative_offsets[relative_offset // NTFS_SECTOR_SIZE]:
                    return 0, 0

            if fill_match is not None:
                fills.append(line)

            line_num += 1

        print('Found INDX USN change at %012x (0x%04x -> 0x%04x)' % (base_offset, old_usn_words[0], new_usn_words[0]))
        if len(fills) > 0:
            print('Includes the following FILL records:')
            print('****>')
            for x in fills:
                print(x)
            print('****>')
        return 0, line_num


        # expected_offsets = []
        # if is_mft_file_usn_change:
        #     if old_usn_bytes[0] != -1:
        #         expected_offsets = [0x30, 0x1fe, 0x3fe]
        #     if old_usn_bytes[1] != -1:
        #         expected_offsets = [0x31, 0x1ff, 0x3ff]
        # elif is_indx_usn_change:
        #     if old_usn_bytes[0] != -1:
        #         expected_offsets = [0x28, 0x1fe, 0x3fe, 0x5fe, 0x7fe, 0x9fe, 0xbfe, 0xdfe, 0xffe]
        #     if old_usn_bytes[1] != -1:
        #         expected_offsets = [0x29, 0x1ff, 0x3ff, 0x5ff, 0x7ff, 0x9ff, 0xbff, 0xdff, 0xfff]
        # expected_offsets = [e + base_offset for e in expected_offsets]
        # if len(recent_lines) < len(expected_offsets):
        #     continue
        # for i in range(len(expected_offsets)):
        #     primary_elements = recent_lines[i].split(':')
        #     candidate_offset = int(primary_elements[0], 16)
        #     try:
        #         values = [int(e, 16) for e in primary_elements[1].split(' ')[-2:]]
        #     except ValueError:
        #         discard_least_recent_line = True
        #         break
        #     if candidate_offset != expected_offsets[i]:
        #         discard_least_recent_line = True
        #         break
        #     if values[0] != old_usn_bytes[expected_offsets[i] % 2]:
        #         discard_least_recent_line = True
        #         break
        #     if values[1] != new_usn_bytes[expected_offsets[i] % 2]:
        #         discard_least_recent_line = True
        #         break
        #
        # if discard_least_recent_line:
        #      continue
        #
        # byte_string = ('xx', '%02x' % (old_usn_bytes[1]))[old_usn_bytes[1] != -1]
        # byte_string += ('xx', '%02x' % (old_usn_bytes[0]))[old_usn_bytes[0] != -1]
        # byte_string += ' -> '
        # byte_string += ('xx', '%02x' % (new_usn_bytes[1]))[new_usn_bytes[1] != -1]
        # byte_string += ('xx', '%02x' % (new_usn_bytes[0]))[new_usn_bytes[0] != -1]
        #
        # message = '%016x: Found %s USN change (%s)' % (base_offset, ('MFT FILE', 'INDX')[is_indx_usn_change], byte_string)
        # print(message)
        # del recent_lines[:len(expected_offsets)]

    def handle_other(self, lines):
        print(lines[0])
        return 0, 1


log_file = open(sys.argv[1], 'r')
image_file = open(sys.argv[2], 'rb')
partition_base_offset = int(sys.argv[3], 16)

analyzer = LogAnalyzer(image_file, partition_base_offset)

recent_lines = []
lines_pinned_cnt_list = [0]
lines_consumed_cnt = 0
while True:
    for _ in range(lines_consumed_cnt):
        del recent_lines[0]
        lines_pinned_cnt_list = [0]

    max_lines_pinned_cnt = max(lines_pinned_cnt_list)
    next_series = max_lines_pinned_cnt == 0
    if next_series and len(recent_lines) > 0:
        analyzer.handle_other(recent_lines)
        del recent_lines[0]

    if not next_series or len(recent_lines) == 0:
        line = log_file.readline()
        line = line.rstrip()
        recent_lines.append(line)

    if next_series or lines_pinned_cnt_list[0] > 0:
        (lines_pinned_cnt_list[0], lines_consumed_cnt) = analyzer.handle_indx_record(recent_lines, False)
        if lines_consumed_cnt > 0:
            continue
