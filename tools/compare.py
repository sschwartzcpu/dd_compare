# This is a change

import sys

start_offset = 0x000000000000
max_block_count = 0
discarded_run_min_len = 64

#@profile
def do_work():
    f1 = open(sys.argv[1], 'rb')
    f1.seek(start_offset)
    f2 = open(sys.argv[2], 'rb')
    f2.seek(start_offset)

    block_size = 16 * 65536
    if start_offset % block_size != 0:
        print('ERROR: Invalid start offset 0x%12x!' % (start_offset))
        sys.exit(-1)
    block_num = start_offset // block_size

    discarded_run_len = 0
    discarded_run_new_byte = -1
    discarded_run_old_bytes = ['\0'] * discarded_run_min_len

    b1 = bytearray(block_size)
    b2 = bytearray(block_size)
    while True:
        if block_num % 64 == 0:
            message = '@0x%012x' % (block_num * block_size)
            if block_num != start_offset // block_size:
                sys.stderr.write('\b' * len(message))
            sys.stderr.write(message)
            sys.stderr.flush()

        if max_block_count > 0 and block_num == max_block_count:
            return

        f1.readinto(b1)
        f2.readinto(b2)

        if len(b1) != len(b2):
            print('ERROR: Block size mismatch!')
            sys.exit(-1)

        if len(b1) == 0:
            sys.exit(0)

        for i in range(block_size):
            byte1 = b1[i]
            byte2 = b2[i]
            offset = (block_num * block_size) + i
            if discarded_run_len > 0 and byte2 != discarded_run_new_byte:
                discarded_run_end_offset = offset - 1
                if discarded_run_new_byte != '\0':
                    if discarded_run_len < discarded_run_min_len:
                        for j in range(discarded_run_len):
                            if discarded_run_old_bytes[j] != discarded_run_new_byte:
                                print('%012x: %02x %02x' \
                                    % (discarded_run_start_offset + j, discarded_run_old_bytes[j], discarded_run_new_byte))
                    else:
                        print('%012x: Discarding run of %d bytes with value %02x ending at %012x' \
                            % (discarded_run_start_offset, discarded_run_len, discarded_run_new_byte, discarded_run_end_offset))
                discarded_run_len = 0
            if discarded_run_len == 0 and byte2 != byte1:
                discarded_run_len = 1
                discarded_run_new_byte = byte2
                discarded_run_old_bytes[0] = byte1
                discarded_run_start_offset = offset
            elif discarded_run_len > 0 and (byte2 != byte1 or byte2 == discarded_run_new_byte):
                discarded_run_len += 1
                if discarded_run_len < discarded_run_min_len:
                    discarded_run_old_bytes[discarded_run_len - 1] = byte1
        block_num += 1

if __name__ == '__main__':
    #import cProfile
    #cProfile.run('do_work()')
    do_work()