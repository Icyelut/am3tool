import shutil
import fs
import os
from binascii import hexlify
import am3.hashtools as hashtools
import re


def get_bytes_at_pos(filepath, pos_hex, num_bytes):
    pos_int = int.from_bytes(bytes.fromhex(pos_hex), "big")

    result_byte_array = bytearray()
    with open(filepath, mode='rb') as read_stream:
        # Advance the read cursor to the desired starting place
        read_stream.read(pos_int)

        for i in range(num_bytes):
            one_byte_raw = read_stream.read(1)
            result_byte_array.append(int.from_bytes(one_byte_raw, "big"))

    return result_byte_array


def output_dump_info(image_file, key, filelist, out_dir):
    template = """[OPTIONAL] DoM URL GOES HERE
Dumped with [DUMPING TOOL] on [DUMPING OS] on [DUMP DATE].
Suspected bad full card dump: {}

Title: [REQUIRED]
Title (native): [OPTIONAL]
Card Serial: [REQUIRED, if available]
Was the card sealed before dumping: [YES/NO]
Has the card been overwritten with new content: [YES/NO]

Key: 
[code]
{}
[/code]

Card image hash: 
[code]
{}
[/code]
    
Content hashes:
[code]
{}
[/code]
    """
    print("Key: {}".format(key))
    image_hash = hashtools.generate_single_file(image_file)
    file_hashes = hashtools.generate(out_dir)
    bad_dump = False

    pattern = re.compile(r"/AM3/.*\.AM3", re.IGNORECASE)
    badfiles = [x for x in filelist if not pattern.match(x)]
    if len(badfiles) > 0:
        print("WARNING: This image contains non-am3 files. The image file will be marked as BADDUMP")
        bad_dump = True

    with open(os.path.join(out_dir, "dump_info.txt"), "w") as outfile:
        outfile.write(template.format(bad_dump, key, image_hash, "\n\n".join(file_hashes)))


def generate(parsed_args):
    image = parsed_args.infile
    working_dir = os.path.dirname(image)
    out_dir = os.path.join(working_dir, "out")
    shutil.copy2(image, f'{image}.original')

    filelist = []

    # Get the start location of the FAT volume (Volume Boot Record)
    partition_start = int.from_bytes(get_bytes_at_pos(image, "01C6", 4), "little") * 512
    print(f'FAT12 partition starts at byte {partition_start} (base 10)')
    blank_lock_file_header = b"SMID\x80\x00\x00\x00"

    with fs.open_fs(f"fat://{image}?offset={partition_start}") as am3fatfs:
        filelist = [path for path in am3fatfs.walk.files()]
        # Extract the key and format it for text output
        key = ""
        with am3fatfs.open("/AM3/00.AM3", "rb") as lockfile:
            key = hexlify(lockfile.read()[8:]).decode()

        # THIS DIRECTLY WRITES TO THE DISC IMAGE
        with am3fatfs.open("/AM3/00.AM3", "wb") as lockfile:
            lockfile.write(blank_lock_file_header)

            # FF-fill the 128-bit DES key
            for i in range(128):
                lockfile.write(b"\xff")

        # Extract all files from the filesystem
        for path in am3fatfs.walk.files():
            print(path)
            with am3fatfs.open(path, "rb") as infile:
                filename = os.path.join(out_dir, path[1:])
                try:
                    os.makedirs(os.path.split(filename)[0])
                except:
                    pass

                with open(filename, "wb") as outfile:
                    outfile.write(infile.read())


    output_dump_info(image, key, filelist, out_dir)