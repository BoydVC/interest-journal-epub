#!/usr/bin/env python3
"""Build EPUB from chapters.json + offline dist/interest-journal-epub.html."""
import html
import json
import os
import re
import zipfile
from xml.sax.saxutils import escape as xml_esc

HERE = os.path.dirname(os.path.abspath(__file__))


def rd(rel):
    with open(os.path.join(HERE, rel), encoding="utf-8") as f:
        return f.read()


def md_to_xhtml(body: str) -> str:
    """Minimal markdown → XHTML fragments (stdlib only)."""
    lines = body.replace("\r\n", "\n").split("\n")
    out = []
    in_list = None
    in_pre = False
    pre_buf = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append(f"</{in_list}>")
            in_list = None

    def inline(s):
        t = html.escape(s)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(
            r"\[([^\]]+)\]\((https?:[^)\s]+)\)",
            r'<a href="\2">\1</a>',
            t,
        )
        return t

    for line in lines:
        if line.startswith("```"):
            if in_pre:
                out.append("<pre><code>" + html.escape("\n".join(pre_buf)) + "</code></pre>")
                pre_buf, in_pre = [], False
            else:
                close_list()
                in_pre = True
            continue
        if in_pre:
            pre_buf.append(line)
            continue
        if not line.strip():
            close_list()
            continue
        if re.match(r"^---+\s*$", line) or re.match(r"^\*\*\*+\s*$", line):
            close_list()
            out.append("<hr/>")
            continue
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            close_list()
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
            continue
        m = re.match(r"^\s*[-*]\s+(.+)$", line)
        if m:
            if in_list != "ul":
                close_list()
                out.append("<ul>")
                in_list = "ul"
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue
        m = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if m:
            if in_list != "ol":
                close_list()
                out.append("<ol>")
                in_list = "ol"
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue
        close_list()
        out.append(f"<p>{inline(line)}</p>")
    close_list()
    if in_pre:
        out.append("<pre><code>" + html.escape("\n".join(pre_buf)) + "</code></pre>")
    return "\n".join(out)


def chapter_xhtml(ch, title):
    note = ""
    if ch.get("truncated"):
        note = (
            '<p><em>Excerpt truncated for EPUB size — full source: '
            + html.escape(ch.get("source_path", ""))
            + "</em></p>"
        )
    body = md_to_xhtml(ch.get("body", ""))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Georgia, serif; line-height: 1.55; margin: 1.2em; color: #111; }}
    h1,h2,h3 {{ font-family: system-ui, sans-serif; }}
    code, pre {{ font-family: ui-monospace, monospace; font-size: 0.9em; }}
    pre {{ background: #f4f4f5; padding: 0.8em; overflow-x: auto; }}
    a {{ color: #0369a1; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <p><small>{html.escape(ch.get('date') or '')} · {html.escape(ch.get('filename') or '')} · {html.escape(ch.get('kind') or '')}</small></p>
  {note}
  {body}
</body>
</html>
"""


def build_epub(meta, out_path):
    chapters = meta.get("chapters", [])
    book_title = meta.get("title", "Interest Journal")
    author = meta.get("author", "Christopher Boyd")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # EPUB requires mimetype first, stored (no compression)
    with zipfile.ZipFile(out_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        )

        # nav
        nav_items = []
        manifest = [
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        ]
        spine = []
        ncx_nav = []

        for i, ch in enumerate(chapters):
            cid = f"ch{i+1:03d}"
            href = f"{cid}.xhtml"
            title = ch.get("title") or ch.get("filename") or cid
            zf.writestr(f"OEBPS/{href}", chapter_xhtml(ch, title))
            manifest.append(
                f'<item id="{cid}" href="{href}" media-type="application/xhtml+xml"/>'
            )
            spine.append(f'<itemref idref="{cid}"/>')
            nav_items.append(
                f'<li><a href="{href}">{xml_esc(title)}</a></li>'
            )
            ncx_nav.append(
                f"""<navPoint id="{cid}" playOrder="{i+1}">
  <navLabel><text>{xml_esc(title)}</text></navLabel>
  <content src="{href}"/>
</navPoint>"""
            )

        nav_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head><meta charset="utf-8"/><title>Contents</title></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Contents</h1>
    <ol>
      {''.join(nav_items)}
    </ol>
  </nav>
</body>
</html>
"""
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml)

        ncx = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="interest-journal-epub-2026"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{xml_esc(book_title)}</text></docTitle>
  <navMap>
    {''.join(ncx_nav)}
  </navMap>
</ncx>
"""
        zf.writestr("OEBPS/toc.ncx", ncx)

        opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">interest-journal-epub-2026</dc:identifier>
    <dc:title>{xml_esc(book_title)}</dc:title>
    <dc:creator>{xml_esc(author)}</dc:creator>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">2026-10-11T00:00:00Z</meta>
  </metadata>
  <manifest>
    {chr(10).join(manifest)}
  </manifest>
  <spine toc="ncx">
    {chr(10).join(spine)}
  </spine>
</package>
"""
        zf.writestr("OEBPS/content.opf", opf)

    return len(chapters)


def main():
    data_path = os.path.join(HERE, "data", "chapters.json")
    with open(data_path, encoding="utf-8") as f:
        meta = json.load(f)

    dist = os.path.join(HERE, "dist")
    os.makedirs(dist, exist_ok=True)
    epub_path = os.path.join(dist, "interest-journal.epub")
    n = build_epub(meta, epub_path)

    # slim payload for HTML (keep bodies)
    chapters_js = json.dumps(meta, ensure_ascii=False)
    html_doc = rd("web/index.html")
    html_doc = html_doc.replace("/*__CSS__*/", rd("web/app.css"))
    html_doc = html_doc.replace("/*__CHAPTERS__*/ null /*__/CHAPTERS__*/", chapters_js)
    app = rd("web/app.js").replace("</script", "<\\/script")
    html_doc = html_doc.replace("/*__APP__*/", app)

    out = os.path.join(dist, "interest-journal-epub.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(
        f"built {out} ({os.path.getsize(out):,} bytes) · "
        f"epub={epub_path} ({os.path.getsize(epub_path):,} bytes) · chapters={n}"
    )


if __name__ == "__main__":
    main()
