"""Build the bilingual homepage from the shared bibliography and highlights."""

import json
import re
import subprocess
import sys
from html import escape, unescape
from pathlib import Path
from tempfile import TemporaryDirectory


PREVIEW_SIZE = 20
HIGHLIGHTS_FILE = Path(__file__).with_name("publication-highlights.json")
HIGHLIGHTS_MARKER = "<!-- publication highlights -->"


def highlight_article(item, entries, language):
    # Pick the formal title and any award from the same entry shown in Papers.
    prefix = item["paper"]
    matches = [(title, body) for title, body in entries if title.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one bibliography title starting with {prefix!r}, found {len(matches)}")
    title, body = matches[0]
    lines = [
        '<article class="publication-highlight">',
        f'<h4 class="highlight-title"><a href="{escape(item["url"])}">{escape(title)}</a></h4>',
        f'<p class="highlight-venue">{escape(item["venue"])}</p>',
        f'<p class="highlight-description">{escape(item[language])}</p>',
    ]
    award = re.search(r'<span class="paper-award">([^<]+)</span>', body)
    if award:
        lines.append(f'<p class="highlight-award">{award[1]}</p>')
    if "citations" in item:
        citations = item["citations"]
        count = f'{citations["count"]:,}'
        label = f'被引 {count} 次' if language == "zh" else f'Cited by {count}'
        lines.append(f'<p class="highlight-citations"><a href="{escape(citations["url"])}">{label}</a></p>')
    lines.append('</article>')
    return "\n".join(lines)


def publication_highlights(bibliography, language):
    entries = [
        (unescape(title), body) for title, body in
        re.findall(r'^<li><p><b>([^<]+)</b>(.*?)</li>', bibliography, re.M | re.S)
    ]
    highlights = json.loads(HIGHLIGHTS_FILE.read_text(encoding="utf-8"))
    sections = []
    for group in highlights["groups"]:
        sections.append('<section class="highlight-group">')
        sections.append(f'<h3>{escape(group[language])}</h3>')
        sections.extend(highlight_article(item, entries, language) for item in group["papers"])
        sections.append('</section>')
    date = escape(highlights["citation_date"])
    time = f'<time datetime="{date}">{date}</time>'
    note = (f'引用量来自 Google Scholar，统计于 {time}。' if language == "zh"
            else f'Citation counts from Google Scholar as of {time}.')
    sections.append(f'<p class="meta">{note}</p>')
    return "\n".join(sections)


def publication_list(year, entries):
    return f'<ul role="list" aria-labelledby="pub-{year}">\n' + "".join(entries) + "</ul>"


def publication_preview(match, colon):
    disclosure, bibliography = match.groups()
    if not bibliography.strip():
        return ""

    visible, archived = [], []
    remaining = PREVIEW_SIZE
    years = re.split(r"<h3>(\d{4})</h3>", bibliography.strip())
    if years[0]:
        raise ValueError("Expected a year heading before the first publication")

    for year, group in zip(years[1::2], years[2::2]):
        listing = re.fullmatch(r"\s*<ul>\s*(<li>.*?)</ul>\s*", group, re.DOTALL)
        if not listing:
            raise ValueError(f"Expected a publication list for {year}")
        # jemdoc starts each entry on a new line. A year can span the disclosure.
        entries = re.split(r"(?=^<li>)", listing[1], flags=re.MULTILINE)[1:]
        shown, hidden = entries[:remaining], entries[remaining:]
        heading = f'<h3 id="pub-{year}">{year}{colon}</h3>'
        (visible if shown else archived).append(heading)
        if shown:
            visible.append(publication_list(year, shown))
            remaining -= len(shown)
        if hidden:
            archived.append(publication_list(year, hidden))

    if archived:
        visible.extend([disclosure, *archived, "</details>"])
    return "\n".join(visible)


def build(source, config, target):
    with TemporaryDirectory(dir=target.parent) as directory:
        page = Path(directory) / target.name
        subprocess.run(["./jemdoc", "-c", config, "-o", page, source], check=True)
        html = page.read_text(encoding="utf-8")
        language = "zh" if '<html lang="zh-CN">' in html else "en"
        archives = list(re.finditer(
            r'(<details class="publication-archive">\s*<summary>[^<]*</summary>)'
            r'(.*?)</details>',
            html, flags=re.DOTALL,
        ))
        if len(archives) != 1:
            raise ValueError(f"Expected one publication archive in {source}")
        if html.count(HIGHLIGHTS_MARKER) != 1:
            raise ValueError(f"Expected one highlights placeholder in {source}")
        archive = archives[0]
        preview = publication_preview(archive, "：" if language == "zh" else ":")
        highlights = publication_highlights(archive[2], language)
        html = html[:archive.start()] + preview + html[archive.end():]
        html = html.replace(HIGHLIGHTS_MARKER, highlights)
        page.write_text(html, encoding="utf-8")
        page.replace(target)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
