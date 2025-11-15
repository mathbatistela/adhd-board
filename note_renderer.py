#!/usr/bin/env python3
"""Render the note template to PNG via Playwright and optionally print it."""

from __future__ import annotations

import argparse
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Sequence

try:
    from playwright.sync_api import Browser, sync_playwright
except ImportError as exc:  # pragma: no cover - runtime dependency
    raise SystemExit(
        "Playwright is required. Install with `pip install playwright` "
        "and run `playwright install chromium`."
    ) from exc

from print_message import MAX_THERMAL_WIDTH_PX, print_image

DEFAULT_TEMPLATE_PATH = Path("note_template.html")
CATEGORY_ICON_MAP = {
    "casa": "🏠",
    "lar": "🏡",
    "trabalho": "💼",
    "estudo": "📚",
    "estudos": "📚",
    "estudar": "📚",
    "saude": "💊",
    "saúde": "💊",
    "lazer": "🎉",
    "compras": "🛒",
    "familia": "👨‍👩‍👧‍👦",
    "família": "👨‍👩‍👧‍👦",
    "financas": "💰",
    "finanças": "💰",
}
DEFAULT_CATEGORY_ICON = "⭐"


def load_template(template_path: Path) -> str:
    path = template_path.expanduser()
    if not path.is_file():
        raise FileNotFoundError(
            f"Template not found at {path}. Provide --template or create note_template.html."
        )
    return path.read_text(encoding="utf-8")


def resolve_category(raw_category: str) -> str:
    normalized = raw_category.strip().lower()
    if not normalized:
        return DEFAULT_CATEGORY_ICON
    return CATEGORY_ICON_MAP.get(normalized, DEFAULT_CATEGORY_ICON)


def build_note_html(
    *,
    category_icon: str,
    ticket_id: str,
    text: str,
    date: str,
    width: int,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
) -> str:
    html = load_template(template_path)
    return (
        html.replace("{{ category_icon }}", escape(category_icon))
        .replace("{{ ticket_id }}", escape(ticket_id))
        .replace("{{ text }}", escape(text).replace("\n", "<br />"))
        .replace("{{ date }}", escape(date))
        .replace("{{ width }}", str(width))
    )


def render_html_to_png(
    html: str,
    output_path: Path,
    *,
    width: int,
    clip_padding: int = 6,
) -> Path:
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser: Browser | None = None
        try:
            browser = playwright.chromium.launch(
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = browser.new_page(
                viewport={"width": width, "height": 600},
                device_scale_factor=2.0,
            )
            page.set_content(html, wait_until="networkidle")
            height = int(page.evaluate("document.documentElement.scrollHeight"))
            page.set_viewport_size({"width": width, "height": height})

            note = page.locator(".note").first
            box = note.bounding_box()
            if box is None:
                raise RuntimeError("Unable to determine bounding box for .note in template.")

            viewport = page.viewport_size or {"width": width, "height": height}
            clip = {
                "x": max(0, box["x"] - clip_padding),
                "y": max(0, box["y"] - clip_padding),
                "width": box["width"] + clip_padding * 2,
                "height": box["height"] + clip_padding * 2,
            }
            clip["width"] = min(viewport["width"] - clip["x"], clip["width"])
            clip["height"] = min(viewport["height"] - clip["y"], clip["height"])
            page.screenshot(path=str(output_path), type="png", clip=clip)
        finally:
            if browser is not None:
                browser.close()

    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render the thermal note PNG and optionally print it."
    )
    parser.add_argument("--category", default="FOCUS", help="Category badge text.")
    parser.add_argument(
        "--date",
        default=None,
        help="Date label; defaults to today's date when omitted.",
    )
    parser.add_argument(
        "--text",
        help="Explicit note text. Falls back to joined positional MESSAGE args.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE_PATH,
        help="Path to the HTML template (default: note_template.html).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("note.png"),
        help="Destination PNG path.",
    )
    parser.add_argument(
        "--print",
        dest="should_print",
        action="store_true",
        help="Send the rendered PNG to the thermal printer.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=MAX_THERMAL_WIDTH_PX,
        help="Pixel width of the rendered ticket.",
    )
    parser.add_argument(
        "--ticket-id",
        default="1",
        help="Identifier displayed on the left (e.g. '3' will render as #3).",
    )
    parser.add_argument(
        "message",
        nargs="*",
        help="Optional words used as the note text when --text is not given.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    text = args.text or " ".join(args.message).strip() or "Stay on target. You got this."
    date_value = args.date or datetime.now().strftime("%d %b %Y")
    ticket_id = f"#{args.ticket_id.strip()}" if args.ticket_id.strip() else "#1"

    category_icon = resolve_category(args.category)

    html = build_note_html(
        category_icon=category_icon,
        ticket_id=ticket_id,
        text=text,
        date=date_value,
        width=args.width,
        template_path=args.template,
    )
    image_path = render_html_to_png(html, args.output, width=args.width)
    print(f"Saved note to {image_path}")

    if args.should_print:
        print("Sending note to printer...")
        print_image(str(image_path), max_width=args.width)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
