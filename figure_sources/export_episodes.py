"""Export the mechanism SVG and its transparent page at publication width."""

from base64 import b64encode
from pathlib import Path
from xml.etree import ElementTree

import cairosvg


def main():
    source = Path(__file__).resolve().parent
    drawing = ElementTree.parse(source / "episodes.svg")
    svg = "{http://www.w3.org/2000/svg}"
    href = "{http://www.w3.org/1999/xlink}href"
    page = drawing.find(f".//{svg}image[@id='block-a-page']")
    component = source / page.attrib[href]
    encoded_page = b64encode(component.read_bytes()).decode("ascii")
    page.set(href, f"data:image/png;base64,{encoded_page}")

    output = source.parent / "figures" / "episodes.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(
        bytestring=ElementTree.tostring(drawing.getroot(), encoding="utf-8"),
        write_to=str(output),
    )


if __name__ == "__main__":
    main()
