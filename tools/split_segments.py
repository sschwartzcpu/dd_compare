import sys

segments = (
    (         0x0,       0x7dff),
    (      0x7e00,  0x3ffac4fff),
    ( 0x3ffac5000,  0x3ffaccdff),
    ( 0x3ffacce00,  0xbff8271ff),
    ( 0xbff827200,  0xbff82efff),
    ( 0xbff82f000, 0x2bff587bff),
    (0x2bff587c00, 0x2bff58f9ff),
    (0x2bff58fa00, 0x2e93bb81ff),
    (0x2e93bb8200, 0x2e93d35fff)
)

in_file = open(sys.argv[1], 'r')

current_segment = -1
out_file = None

try:
    for in_line in in_file.readlines():
        in_line = in_line.rstrip()
        elements = in_line.split(':')
        index = elements[0].find(' ')
        elements = [elements[0][:index], elements[0][index + 1:]]
        offset = int(elements[0], 16)

        for candidate_segment in range(len(segments)):
            if segments[candidate_segment][0] <= offset and segments[candidate_segment][1] >= offset:
                if candidate_segment != current_segment:
                    if out_file is not None:
                        out_file.close()
                    current_segment = candidate_segment
                    out_filename = 'segment%d.txt' % current_segment
                    out_file = open(out_filename, 'a')
                    print('Writing \'%s\'...' % out_filename)
                out_line = '%012x [' % (offset - segments[current_segment][0])
                subelements = elements[1][1:-1].split(' ')
                for subelement in subelements:
                    if len(subelement) == 12:
                        try:
                            offset = int(subelement, 16)
                        except ValueError:
                            pass
                        else:
                            subelement = '%012x' % (offset - segments[current_segment][0])
                    out_line += ' %s' % subelement
                out_line = out_line[1:] + ']\n'
                out_file.write(out_line)
                break

finally:
    if out_file is not None:
        out_file.close()
