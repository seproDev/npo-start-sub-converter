import re
import pysubs2
import pysrt


VIDEO_HEIGHT = 1080
VIDEO_WIDTH = 1920
DEFAULT_MARGINV = 90  # Percentage of screen
MARGINV_OFFSET = -30


def generate_empty_ass() -> pysubs2.SSAFile:
    ass = pysubs2.SSAFile()

    # Define Deafult style
    ass.styles["Default"].fontname = "Clear Sans Medium"
    ass.styles["Default"].fontsize = 73
    ass.styles["Default"].bold = True
    ass.styles["Default"].primarycolor = pysubs2.Color(255, 255, 255, 0)
    ass.styles["Default"].outlinecolor = pysubs2.Color(0, 0, 0, 0)
    ass.styles["Default"].backcolor = pysubs2.Color(0, 0, 0, 160)
    ass.styles["Default"].outline = 3.5
    ass.styles["Default"].shadow = 2.1
    ass.styles["Default"].marginl = 100
    ass.styles["Default"].marginr = 100
    ass.styles["Default"].marginv = round(
        (1 - DEFAULT_MARGINV / 100) * VIDEO_HEIGHT + MARGINV_OFFSET
    )

    # Add different color styles
    ass.styles["White"] = ass.styles["Default"].copy()
    ass.styles["White"].primarycolor = pysubs2.Color(255, 255, 255, 0)
    ass.styles["Lime"] = ass.styles["Default"].copy()
    ass.styles["Lime"].primarycolor = pysubs2.Color(0, 255, 0, 0)
    ass.styles["Cyan"] = ass.styles["Default"].copy()
    ass.styles["Cyan"].primarycolor = pysubs2.Color(0, 255, 255, 0)
    ass.styles["Red"] = ass.styles["Default"].copy()
    ass.styles["Red"].primarycolor = pysubs2.Color(255, 0, 0, 0)
    ass.styles["Yellow"] = ass.styles["Default"].copy()
    ass.styles["Yellow"].primarycolor = pysubs2.Color(255, 255, 0, 0)
    ass.styles["Magenta"] = ass.styles["Default"].copy()
    ass.styles["Magenta"].primarycolor = pysubs2.Color(255, 0, 255, 0)
    ass.styles["Blue"] = ass.styles["Default"].copy()
    ass.styles["Blue"].primarycolor = pysubs2.Color(0, 0, 255, 0)
    ass.styles["Black"] = ass.styles["Default"].copy()
    ass.styles["Black"].primarycolor = pysubs2.Color(0, 0, 0, 0)
    ass.styles["Black"].outlinecolor = pysubs2.Color(255, 255, 255, 0)

    # Set info segment and metadata
    ass.info.update({"YCbCr Matrix": "TV.709"})
    ass.info.update({"PlayResX": VIDEO_WIDTH})
    ass.info.update({"PlayResY": VIDEO_HEIGHT})

    return ass


def convert_line(line: pysrt.SubRipItem) -> pysubs2.SSAEvent:
    text = line.text
    # Convert Line Breaks
    text = text.replace("\n", "\\N")

    # Convert Class closing tags
    text = text.replace("</c>", "{\\r}")

    # Convert different style classes
    text = text.replace("<c.white>", "{\\rWhite}")
    text = text.replace("<c.S1>", "{\\rWhite}")
    text = text.replace("<c.green>", "{\\rLime}")  # Their css is missing green
    text = text.replace("<c.lime>", "{\\rLime}")
    text = text.replace("<c.S2>", "{\\rLime}")
    text = text.replace("<c.cyan>", "{\\rCyan}")
    text = text.replace("<c.S3>", "{\\rCyan}")
    text = text.replace("<c.red>", "{\\rRed}")
    text = text.replace("<c.S4>", "{\\rRed}")
    text = text.replace("<c.yellow>", "{\\rYellow}")
    text = text.replace("<c.S5>", "{\\rYellow}")
    text = text.replace("<c.magenta>", "{\\rMagenta}")
    text = text.replace("<c.S6>", "{\\rMagenta}")
    text = text.replace("<c.blue>", "{\\rBlue}")
    text = text.replace("<c.S7>", "{\\rBlue}")
    text = text.replace("<c.black>", "{\\rBlack}")
    text = text.replace("<c.S8>", "{\\rBlack}")

    # Catch missing conversions
    if "<c." in text:
        print(f"WARNING: Unrecognized style class: {text}")

    # Remove redundant tags
    text = text.replace("{\\r}{\\r", "{\\r")
    text = text.replace("{\\r}\\N{\\r", "\\N{\\r")
    if text.endswith("{\\r}"):
        text = text[:-4]

    # Extract default stlye
    starting_style = re.search(r"^{\\r(.+?)}", text)
    if starting_style:
        style = starting_style.group(1)
        # Remove inital style tag
        text = text.replace(f"{{\\r{style}}}", "", 1)

        # Remove next styletag if it is the same
        next_style = re.search(r"{\\r(.+?)}", text)
        if next_style and next_style.group(1) == style:
            text = text.replace(f"{{\\r{style}}}", "", 1)
    else:
        style = "Default"

    # Parse position data
    pos_tags = ""
    if "position:50%" in line.position and (
        "align:middle" in line.position or "align:center" in line.position
    ):
        pass  # Don't add \an2
    elif "position:30%" in line.position and "align:start" in line.position:
        pos_tags += "\\an1"
    elif "position:70%" in line.position and "align:end" in line.position:
        pos_tags += "\\an1"
    else:
        print("WARNING: Unsported position and align combination: " + line.position)

    marginv = 0
    if "line:" in line.position and not f"line:{DEFAULT_MARGINV}%" in line.position:
        line_vertical = re.search(r"line:(\d+)%", line.position)
        if line_vertical:
            line_vertical_percentage = int(line_vertical.group(1))
            marginv = round(
                (1 - line_vertical_percentage / 100) * VIDEO_HEIGHT + MARGINV_OFFSET
            )
        else:
            print("WARNING: Couldn't parse vertical pos: " + line.position)

    if "vertical:" in line.position or "size:" in line.position:
        print("WARNING: Unaccounted for position data present: " + line.position)

    if pos_tags != "":
        pos_tags = "{" + pos_tags + "}"

    # Create new line
    ass_line = pysubs2.SSAEvent()
    ass_line.start = line.start.ordinal
    ass_line.end = line.end.ordinal
    ass_line.style = style
    ass_line.text = pos_tags + text
    ass_line.marginv = marginv

    return ass_line


def convert_subtitle(filename: str) -> int:
    try:
        vtt = pysrt.open(filename)
    except Exception:
        print(f"ERROR: Couldn't open {filename}")
        return 1
    ass = generate_empty_ass()
    for line in vtt:
        ass.events.append(convert_line(line))
    ass.sort()
    ass.save(filename + ".ass", header_notice="")
    return 0
