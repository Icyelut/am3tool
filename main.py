import argparse
import pathlib
import sys

from am3 import am3

def is_valid_new_file_location(file_path):

    path_maybe = pathlib.Path(file_path)
    path_resolved = None

    # try and resolve the path
    try:
        path_resolved = path_maybe.resolve(strict=False).expanduser()

    except Exception as e:
        raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(file_path, e))

    if not path_resolved.parent.exists():
        raise argparse.ArgumentTypeError("The parent directory of `{}` doesn't exist!".format(path_resolved))

    return path_resolved


def is_file(strict=True):
    def _is_file(file_path):

        path_maybe = pathlib.Path(file_path)
        path_resolved = None

        # try and resolve the path
        try:
            path_resolved = path_maybe.resolve(strict=strict).expanduser()

        except Exception as e:
            raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(file_path, e))

        # double check to see if its a file
        if strict:
            if not path_resolved.is_file():
                raise argparse.ArgumentTypeError("The path `{}` is not a file!".format(path_resolved))

        return path_resolved
    return _is_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="am3tool v0.1: Tool to assist in preserving am3 Advance Movie cards and content",
        epilog="Copyright 2022-09-26 - Icyelut. GPLv3",
        fromfile_prefix_chars='@')

    parser.set_defaults(func_to_run=am3.generate)

    parser.add_argument("infile", metavar="file", help="the raw am3 card dump")

    parsed_args = parser.parse_args()

    if "func_to_run" in parsed_args:

        parsed_args.func_to_run(parsed_args)

    else:
        print("No function to run. Quitting.")
        parser.print_help()
        sys.exit(0)