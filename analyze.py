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

# raw_pages = [z for x,y in block_table.items() for z in y if x != "0" and x != '65535']
valid_pages = [y for x in validdump for y in x]

matches = []
no_match = []
matched_page_nums = []

def find_exact_match(in_page, blocks, already_matched):
    for block_num, block in blocks.items():
        for idx, compare_page in enumerate(block):
            if (block_num, idx) in already_matched:
                continue
            if compare_page == in_page:
                return (block_num, idx, in_page)

    return None


def find_partial_match(in_page, blocks, percent, already_matched):
    matched = []
    not_matched = []

    for block_num, block in blocks.items():
        for idx, compare_page in enumerate(block):
            if (block_num, idx) in already_matched:
                continue

            total_byte_matches = 0

            for b1, b2 in zip(in_page, compare_page):
                if b1 == b2:
                    total_byte_matches += 1

            percent_same = total_byte_matches / len(in_page)
            if percent_same >= percent:
                matched.append((percent_same, block_num, idx, compare_page))
            else:
                not_matched.append((percent_same, block_num, idx, compare_page))

    def compare_matches(a):
        return a[0]

    if len(matched) == 0:
        # biggum = max(not_matched, key=compare_matches)
        return None

    return max(matched, key=compare_matches)[1]


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
unmatched = [(block_num, idx, page) for block_num, block in block_table.items() for idx, page in enumerate(block)]
for idx, valid_page in enumerate(valid_pages):
    match = find_exact_match(valid_page, block_table, matched_page_nums)
    if match:
        matches.append(match)
        matched_page_nums.append((match[0], match[1]))
    else:
        percent = 0.9
        while not match and percent > 0.5:
            percent = percent - 0.1
            match = find_partial_match(valid_page, block_table, percent, matched_page_nums)
        if match:
            matches.append(match)
            matched_page_nums.append((match[0], match[1]))
        else:
            no_match.append(valid_page)

    print(f'{idx*100/len(valid_pages)}')
    match = None

# with open("C:\\_temp\\validblocks_compare.bin", "wb") as outfile:
#    for page in matches:
#        outfile.write(page)

reordered_blocks = []
# for validblock in validdump:
#     for block_id, block in block_table.items():
#         if block_id in reordered_blocks:
#             break
#
#         all_match = True
#         for valid_page, nand_page in zip(validblock, block):
#             if valid_page != nand_page:
#                 all_match = False
#                 break
#
#         if all_match:
#             reordered_blocks.append(block_id)
#             break
print()

# with open("C:\\_temp\\validblocks_ordered.bin", "wb") as outfile:
#     keys_sort = [int(x) for x in block_table.keys()]
#     keys_sort.sort()
#     keys_sort = [str(x) for x in keys_sort]
#     with open("C:\\_temp\\blocknums.txt", "w") as blockfile:
#         for block_num in keys_sort:
#             blockfile.write(f'{block_num}\n')
#
#             # Skip the root block as it's not visible from the application side
#             if block_num != "0" and block_num != '65535':
#                 for page in block_table[block_num]:
#                     outfile.write(page)

print(f'Valid blocks: {len(block_table.keys())}')
print(f'Invalid blocks: {len(invalid_block_nums)}')

pages = []
for key, block in block_table.items():
    pages = pages + block

print(f'Pages: {len(pages)}')
