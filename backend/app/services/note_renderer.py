"""Note rendering service using Playwright."""

import logging
from html import escape
from pathlib import Path

from playwright.sync_api import Browser, sync_playwright

from app.enums import CategoryMetadata, get_category_metadata

logger = logging.getLogger(__name__)


class NoteRendererService:
    """Service for rendering HTML notes to PNG images."""

    def __init__(self, default_width: int = 384):
        self.default_width = default_width

    @staticmethod
    def _normalize_category(category: str) -> str:
        """Normalize category name for lookups."""
        normalized = category.strip().lower()
        return normalized or ""

    def _get_category_metadata(self, category: str) -> CategoryMetadata:
        """Get metadata (emoji/label/svg) for a category."""
        normalized = self._normalize_category(category)
        return get_category_metadata(normalized)

    def resolve_category_icon(self, category: str) -> str:
        """Resolve category name to emoji icon (legacy compatibility)."""
        return self._get_category_metadata(category).emoji

    def resolve_category_label(self, category: str) -> str:
        """Resolve category name to human-friendly label."""
        return self._get_category_metadata(category).label

    def resolve_category_icon_svg(self, category: str) -> str:
        """Resolve category name to inline SVG."""
        return self._get_category_metadata(category).svg

    def build_html(
        self,
        template_html: str,
        category_icon: str,
        ticket_id: str,
        text: str,
        date: str,
        width: int,
    ) -> str:
        """Build final HTML by replacing template placeholders."""
        return (
            template_html.replace("{{ category_icon_svg }}", category_icon)
            .replace("{{ category_icon|safe }}", category_icon)
            .replace("{{ category_icon }}", category_icon)
            .replace("{{ ticket_id }}", escape(ticket_id))
            .replace("{{ text }}", escape(text).replace("\n", "<br />"))
            .replace("{{ date }}", escape(date))
            .replace("{{ width }}", str(width))
        )

    def render_to_png(
        self,
        html: str,
        output_path: str | Path,
        width: int | None = None,
        clip_padding: int = 6,
    ) -> Path:
        """Render HTML to PNG using Playwright."""
        if width is None:
            width = self.default_width

        output_path = Path(output_path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                try:
                    page = browser.new_page(
                        viewport={"width": width, "height": 600},
                        device_scale_factor=2.0,
                    )

                    # Load HTML and wait for rendering
                    page.set_content(html, wait_until="networkidle")

                    # Measure content height
                    height = int(page.evaluate("document.documentElement.scrollHeight"))
                    page.set_viewport_size({"width": width, "height": height})

                    # Find .note element and get its bounding box
                    note = page.locator(".note").first
                    box = note.bounding_box()
                    if box is None:
                        raise RuntimeError("Unable to determine bounding box for .note element")

                    # Calculate clip region with padding
                    viewport = page.viewport_size or {"width": width, "height": height}
                    clip = {
                        "x": max(0, box["x"] - clip_padding),
                        "y": max(0, box["y"] - clip_padding),
                        "width": box["width"] + clip_padding * 2,
                        "height": box["height"] + clip_padding * 2,
                    }
                    clip["width"] = min(viewport["width"] - clip["x"], clip["width"])
                    clip["height"] = min(viewport["height"] - clip["y"], clip["height"])

                    # Take screenshot
                    page.screenshot(path=str(output_path), type="png", clip=clip)

                    logger.info(f"Rendered note to {output_path}")
                    return output_path
                finally:
                    browser.close()

        except Exception as exc:
            logger.error(f"Failed to render note: {exc}")
            raise

    def render_note(
        self,
        template_html: str,
        category_icon: str,
        ticket_id: str,
        text: str,
        date: str,
        output_path: str | Path,
        width: int | None = None,
    ) -> tuple[Path, str]:
        """
        Render a complete note from template.

        Args:
            template_html: HTML template with placeholders
            category_icon: SVG icon markup for the category
            ticket_id: Ticket identifier (e.g., "#1")
            text: Note text content
            date: Formatted date string
            output_path: Path where the PNG will be saved
            width: Render width in pixels

        Returns:
            Tuple of (image_path, html_content)
        """
        html = self.build_html(
            template_html=template_html,
            category_icon=category_icon,
            ticket_id=ticket_id,
            text=text,
            date=date,
            width=width or self.default_width,
        )
        image_path = self.render_to_png(
            html=html,
            output_path=output_path,
            width=width,
        )
        return image_path, html
