"""Build a static homepage with a preview of the shared publication list."""

import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


PREVIEW_SIZE = 20


def publication_preview(match):
    disclosure, items = match.groups()
    if not items:
        return ""

    # jemdoc starts each top-level bibliography entry on a new line.
    starts = [entry.start() for entry in re.finditer(r"^<li>", items, re.MULTILINE)]
    if len(starts) <= PREVIEW_SIZE:
        return f"<ol>{items}</ol>"

    split = starts[PREVIEW_SIZE]
    return (
        f"<ol>{items[:split]}</ol>\n{disclosure}\n"
        f'<ol start="{PREVIEW_SIZE + 1}">\n{items[split:]}</ol>\n</details>'
    )


def build(source, config, target):
    with TemporaryDirectory(dir=target.parent) as directory:
        page = Path(directory) / target.name
        subprocess.run(["./jemdoc", "-c", config, "-o", page, source], check=True)
        html, count = re.subn(
            r'(<details class="publication-archive">\s*<summary>[^<]*</summary>)'
            r'\s*(?:<ol>(.*?)</ol>)?\s*</details>',
            publication_preview, page.read_text(encoding="utf-8"), flags=re.DOTALL,
        )
        if count != 1:
            raise ValueError(f"Expected one publication archive in {source}")
        page.write_text(html, encoding="utf-8")
        page.replace(target)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
