import sys

from npo_start_sub_converter.converter import convert_subtitle

if len(sys.argv) != 2:
    print("Usage: python -m npo_start_sub_converter <filename>")
    exit(1)

status = convert_subtitle(sys.argv[1], suffix="_styled", with_styling=True)
status += convert_subtitle(sys.argv[1], suffix="_unstyled", with_styling=False)
exit(status)
