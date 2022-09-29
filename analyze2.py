from binascii import hexlify
from hashlib import sha1, sha256, sha512, md5, sha3_512
from zlib import crc32

filename = "C:\\_temp\\gba_am3_pikachus_winter_vacation_smartmedia.bin"

valid_block_nums = set()
invalid_block_nums = set()
block_table = {}
with open(filename, "rb") as infile:
    with open("C:\\_temp\\blocknums_raw.txt", "w") as blockraw:
        global_block_num = 0
        page_num = 0
        previous_block = 0

        block_num = -1
        while True:
            page = infile.read(512)
            if not page:
                break

            page_num += 1
            spare_array = infile.read(16)
            invalid_block_marker = spare_array[5]
            # if spare_array != b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff':

            # else:
            # print(block_num)
            # new_block = int.from_bytes(spare_array[6:8], byteorder="big")
            # if new_block != previous_block and new_block != 65535:
            #    previous_block = block_num

            block_num = int.from_bytes(spare_array[6:8], byteorder="big")

            if invalid_block_marker == 255:
                # Block is valid
                if str(block_num) not in block_table.keys():
                    # global_block_num += 1
                    valid_block_nums.add(block_num)
                    blockraw.write(f'{block_num}\n')
                    block_table[str(block_num)] = [page]
                else:
                    block_table[str(block_num)].append(page)
                # if spare_array == b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff':
                #    print(f'WARNING: FF block! #{block_num}({len(block_table[str(block_num)])}), current={global_block_num}, previous={previous_block}({len(block_table[str(previous_block)])}), offset {hexlify(infile.tell().to_bytes(4, "big", signed=False))}')
            else:
                invalid_block_nums.add(block_num)

validdump = []
with open("C:\\_temp\\[am3-00066-2499]pikachu_fuyuyasumi.am3", "rb") as infile:
    page_counter = 0
    current_block = []
    while True:
        page = infile.read(512)
        if not page:
            if 0 < page_counter < 65:
                validdump.append(current_block)
            break

        if page_counter > 63:
            validdump.append(current_block)
            page_counter = 0
            current_block = []

        page_counter += 1
        current_block.append(page)

raw_pages = [(block_num, idx, z) for block_num,y in block_table.items() for idx, z in enumerate(y) if block_num != "0" and block_num != '65535']
valid_pages = [y for x in validdump for idx, y in enumerate(x)]

matches = []
no_match = []
matched_page_nums = []


def find_exact_match(in_page, pages_, in_page_num):
    for block_num, page_num, compare_page in pages_:
        if compare_page == in_page:
            return (block_num, page_num, in_page_num, in_page)

    return None


def find_partial_match(in_page, pages_, in_page_num, percent):
    matched = []
    not_matched = []

    for block_num, page_num, compare_page in pages_:

        total_byte_matches = 0

        for b1, b2 in zip(in_page, compare_page):
            if b1 == b2:
                total_byte_matches += 1

        percent_same = total_byte_matches / len(in_page)
        if percent_same >= percent:
            matched.append((percent_same, block_num, page_num, in_page_num, compare_page))
        else:
            not_matched.append((percent_same, block_num, page_num, in_page_num, compare_page))

    def compare_matches(a):
        return a[0]

    if len(matched) == 0:
        # biggum = max(not_matched, key=compare_matches)
        return None

    return max(matched, key=compare_matches)[1:]


# for valid_page in valid_pages:
#     match = find_exact_match(valid_page, raw_pages)
#     if match:
#         matches.append(match)
#         raw_pages.remove(match)
#     else:
#         percent = 0.9
#         while not match and percent > 0.5:
#             percent = percent - 0.1
#             match = find_partial_match(valid_page, raw_pages, percent)
#         if match:
#             matches.append(match)
#             raw_pages.remove(match)
#         else:
#             no_match.append(valid_page)
#
#     match = None
#unmatched = [(block_num, idx, page) for block_num, block in block_table.items() for idx, page in enumerate(block)]
for idx, valid_page in enumerate(valid_pages):
    match = find_exact_match(valid_page, raw_pages, idx)
    if match:
        matches.append(match)
        raw_pages.remove((match[0], match[1], match[3]))
    else:
        percent = 0.9
        while not match and percent > 0.5:
            percent = percent - 0.1
            match = find_partial_match(valid_page, raw_pages, idx, percent)
        if match:
            matches.append(match)
            raw_pages.remove((match[0], match[1], match[3]))
        else:
            no_match.append(valid_page)

    print(f'{idx*100/len(valid_pages)}', end="\r")
    match = None

# with open("C:\\_temp\\validblocks_compare.bin", "wb") as outfile:
#    for page in matches:
#        outfile.write(pagye)

# Reorder identical pages (all 0xff)
reordered_pages = []
previous_block = -1
all_xff = b"".join([b"\xff" for x in range(512)])
for page in matches:
    if page[3] == all_xff and page[0] != previous_block:
        print(f"{page[0]} {page[1]} {previous_block}\n")

    previous_block = page[0]

with open("C:\\_temp\\block_inspect.txt", "w") as outfile:
    outfile.write("block_num, page_num, in_page_num\n")
    for page in matches:
        line = f"{page[0]} {page[1]} {page[2]}\n"
        outfile.write(line)

with open("C:\\_temp\\block_inspect_bl.txt", "w") as outfile:
    outfile.write("block_num, page_num, in_page_num\n\n")
    for page in matches:
        line = f"{page[0]} {page[1]} {page[2]}\n"
        outfile.write(line)

        rawpage = block_table[page[0]][page[1]]

        idx = 0
        while True:
            if idx >= 510:
                break

            byt = rawpage[idx:idx+16]
            outfile.write(hexlify(byt, ' ', 2).decode())
            outfile.write("\n")

            idx = idx + 15

        outfile.write("\n")


print(f'Valid blocks: {len(block_table.keys())}')
print(f'Invalid blocks: {len(invalid_block_nums)}')

pages = []
for key, block in block_table.items():
    pages = pages + block

print(f'Pages: {len(pages)}')
