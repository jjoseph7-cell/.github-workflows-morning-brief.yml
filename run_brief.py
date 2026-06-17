#!/usr/bin/env python3
"""
Morning Brief runner.

Loads the agent instructions from morning-brief-agent-prompt.md, runs them through
the Claude Agent SDK to produce a dated Markdown brief, then emails it via Resend.

Required environment variables:
  ANTHROPIC_API_KEY   your Anthropic API key
  RESEND_API_KEY      your Resend API key
  EMAIL_FROM          sender address (e.g. onboarding@resend.dev, or you@yourdomain.com)
  EMAIL_TO            recipient address (your inbox)
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import markdown as md
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
)

TZ = ZoneInfo("America/Chicago")
PROMPT_FILE = Path("morning-brief-agent-prompt.md")
BRIEFS_DIR = Path("briefs")


async def generate_brief(system_prompt: str, out_path: Path) -> None:
    """Run the agent autonomously and have it write the finished brief to out_path."""
    user_prompt = (
        "Generate today's morning brief now, following your instructions exactly.\n"
        f"Save the finished brief as Markdown to this exact path: {out_path}\n"
        "Complete the full search -> fetch -> verify loop before writing a single line. "
        "Every story must carry a real, retrieved link. When finished, confirm the file path."
    )

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=["WebSearch", "WebFetch", "Bash", "Read", "Write"],
        permission_mode="bypassPermissions",  # fully autonomous, trusted CI sandbox
        model="opus",  # highest-quality analysis; change to "sonnet" to cut cost
    )

    async for message in query(prompt=user_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text, flush=True)          # the agent's reasoning
                elif hasattr(block, "name"):
                    print(f"[tool] {block.name}", flush=True)  # a tool being called
        elif isinstance(message, ResultMessage):
            print(f"[agent done] {message.subtype}", flush=True)


# Email-safe "intelligence dossier" template: deep ink-navy + brass + serif.
# Built for real mail clients — table chrome with inline colors, system fonts
# (Georgia / Courier), no CSS variables / gradients / flexbox / grid. The .doc
# container also carries inline color+font so the body stays readable even if a
# client strips the <style> block. Element selectors style the agent's Markdown
# (h1/h2/h3/p/ul/li/a/em/strong/hr).
HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<meta name="supported-color-schemes" content="dark light">
<style>
  body {{ margin:0; padding:0; background:#0b0f17; }}
  .doc h1 {{ font-family:Georgia,'Times New Roman',serif; text-align:center; font-weight:bold;
             letter-spacing:.5px; font-size:27px; line-height:1.22; margin:6px 0 2px; color:#efeadf; }}
  .doc h2 {{ font-family:Georgia,'Times New Roman',serif; font-size:19px; font-weight:bold;
             letter-spacing:.5px; text-transform:uppercase; color:#efeadf; margin:30px 0 12px;
             padding:0 0 8px 12px; border-bottom:1px solid #6c5d33; border-left:3px solid #c4a85f; }}
  .doc h3 {{ font-family:'Courier New',Courier,monospace; font-size:12px; font-weight:bold;
             letter-spacing:2px; text-transform:uppercase; color:#c4a85f; margin:24px 0 8px;
             padding-bottom:6px; border-bottom:1px solid #1e2838; }}
  .doc p {{ margin:11px 0; }}
  .doc ul, .doc ol {{ margin:9px 0; padding-left:20px; }}
  .doc li {{ margin:7px 0; }}
  .doc a {{ color:#7ea3cf; text-decoration:none; }}
  .doc strong {{ color:#f6f4ed; font-weight:bold; }}
  .doc em {{ color:#9aa6b8; font-style:italic; }}
  .doc hr {{ border:0; border-top:1px solid #1e2838; margin:22px 0; }}
  .doc blockquote {{ margin:11px 0; padding:4px 14px; border-left:3px solid #6c5d33; color:#cdcabf; }}
  .doc code {{ background:#0b0f17; color:#c4a85f; padding:1px 5px; border-radius:3px;
               font-size:13px; font-family:'Courier New',Courier,monospace; }}
  .bar {{ font-family:'Courier New',Courier,monospace; font-size:10px; letter-spacing:3px;
          color:#c4a85f; text-transform:uppercase; }}
</style>
</head>
<body style="margin:0;padding:0;background:#0b0f17;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0b0f17;">
<tr><td align="center" style="padding:16px 12px 40px;">

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:700px;">
    <tr><td align="center" class="bar" style="padding:10px 8px;border-bottom:1px solid #6c5d33;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:3px;color:#c4a85f;">CONFIDENTIAL &bull; DESK DISTRIBUTION ONLY &bull; NOT FOR REDISTRIBUTION</td></tr>
  </table>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:700px;background:#0f1521;">
    <tr><td style="padding:24px 28px 6px;">
      <div align="center" class="bar" style="text-align:center;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:4px;color:#c4a85f;padding-bottom:2px;">DAILY MACRO &amp; MARKETS INTELLIGENCE</div>
      <div class="doc" style="font-family:Georgia,'Times New Roman',serif;color:#e9e7df;font-size:16px;line-height:1.62;">
        {body}
      </div>
    </td></tr>
    <tr><td style="padding:0 28px 26px;">
      <div style="border-top:1px solid #1e2838;padding-top:12px;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1px;color:#7c8699;">
        MACRO &amp; MARKETS STRATEGY DESK &bull; GENERATED AUTONOMOUSLY &amp; SOURCE-VERIFIED
      </div>
    </td></tr>
  </table>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:700px;">
    <tr><td align="center" class="bar" style="padding:10px 8px;border-top:1px solid #6c5d33;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:3px;color:#c4a85f;">CONFIDENTIAL &bull; DESK DISTRIBUTION ONLY &bull; NOT FOR REDISTRIBUTION</td></tr>
  </table>

</td></tr>
</table>
</body>
</html>
"""


def send_email(subject: str, markdown_text: str) -> None:
    """Render the Markdown brief to HTML and send it via the Resend API."""
    body_html = md.markdown(markdown_text, extensions=["extra", "sane_lists"])
    html = HTML_TEMPLATE.format(body=body_html)
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
        json={
            "from": os.environ["EMAIL_FROM"],
            "to": [os.environ["EMAIL_TO"]],
            "subject": subject,
            "html": html,
            "text": markdown_text,  # plain-text fallback
        },
        timeout=30,
    )
    if resp.status_code >= 300:
        print(f"[email ERROR] {resp.status_code}: {resp.text}", flush=True)
        resp.raise_for_status()
    print(f"[email sent] id={resp.json().get('id')}", flush=True)


async def main() -> None:
    if not PROMPT_FILE.exists():
        sys.exit(f"Missing {PROMPT_FILE}. Commit it to the repo root.")

    today = datetime.now(TZ).date()
    BRIEFS_DIR.mkdir(exist_ok=True)
    out_path = (BRIEFS_DIR / f"brief-{today.isoformat()}.md").resolve()
    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

    print(f"[run] generating brief for {today} -> {out_path}", flush=True)
    await generate_brief(system_prompt, out_path)

    # Verify the agent actually produced a brief before emailing.
    if not out_path.exists() or not out_path.read_text(encoding="utf-8").strip():
        send_email(
            f"Morning Brief FAILED - {today}",
            "The agent did not produce a brief today. Check the GitHub Actions logs.",
        )
        sys.exit("Brief file was not created or is empty.")

    brief = out_path.read_text(encoding="utf-8")
    subject = f"Morning Brief - {today.strftime('%A, %b %d, %Y')}"
    send_email(subject, brief)
    print("[run] complete.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
