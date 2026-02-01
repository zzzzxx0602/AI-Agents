from __future__ import annotations
import datetime as dt
import html
from pathlib import Path
import markdown as md

def save_md_html(md_text: str, out_dir: Path, basename: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{basename}.md"
    html_path = out_dir / f"{basename}.html"
    md_path.write_text(md_text, encoding="utf-8")
    body = md.markdown(md_text, extensions=["tables", "fenced_code"])
    html_doc = (
        "<!doctype html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n"
        f"<title>{html.escape(basename)}</title>\n"
        "<style>"
        "body{font-family:Arial, sans-serif; max-width: 920px; margin: 40px auto; line-height:1.6;}"
        "code, pre{background:#f6f6f6; padding:2px 4px;}"
        "pre{padding:12px; overflow:auto;}"
        "h1,h2,h3{margin-top:28px;}"
        "</style>\n</head>\n<body>\n"
        + body +
        "\n</body>\n</html>"
    )
    html_path.write_text(html_doc, encoding="utf-8")
    return md_path, html_path

def build_readme_memo_excerpt(path_to_memo_md: Path, max_words: int = 350) -> str:
    if not path_to_memo_md.exists():
        return "_Run `python run_demo.py` to generate the AI memo._"
    text = path_to_memo_md.read_text(encoding="utf-8")
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "\n\n*(Excerpt truncated — see reports/ai_investment_memo.md for full text.)*\n"
