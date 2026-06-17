#!/usr/bin/env python3
"""
Local email-preview helper — NO API, NO email sent.

Renders a Markdown brief through the exact HTML_TEMPLATE in run_brief.py (the same
template send_email() uses) so you can see what the emailed brief will look like and
keep tuning the styling before you push.

Usage:
    python preview.py path/to/brief.md          # writes email-preview.html next to it
    python preview.py path/to/brief.md out.html  # custom output path

Requires only:  pip install markdown
"""
import re
import sys
import webbrowser
from pathlib import Path

import markdown


def load_template() -> str:
    """Extract HTML_TEMPLATE from run_brief.py without importing it (avoids needing
    the Claude SDK / requests just to preview)."""
    src = Path(__file__).with_name("run_brief.py").read_text(encoding="utf-8")
    m = re.search(r'HTML_TEMPLATE = """\\\n.*?\n"""', src, re.S)
    if not m:
        sys.exit("Could not find HTML_TEMPLATE in run_brief.py")
    ns: dict = {}
    exec(m.group(0), ns)
    return ns["HTML_TEMPLATE"]


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python preview.py <brief.md> [out.html]")
    md_path = Path(sys.argv[1])
    if not md_path.exists():
        sys.exit(f"No such file: {md_path}")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else md_path.with_name("email-preview.html")

    body = markdown.markdown(
        md_path.read_text(encoding="utf-8"),
        extensions=["extra", "sane_lists"],  # identical to send_email()
    )
    html = load_template().format(body=body)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path}")
    try:
        webbrowser.open(out_path.resolve().as_uri())
    except Exception:
        pass


if __name__ == "__main__":
    main()
