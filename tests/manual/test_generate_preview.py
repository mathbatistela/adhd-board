"""Manual test to render the default template into a PNG for visual inspection."""

from datetime import date
from pathlib import Path

from app.services.note_renderer import NoteRendererService


def test_generate_default_template_preview():
    """Render the default note template and persist PNG/HTML previews."""
    template_path = Path("app/templates/default_note.html")
    assert template_path.exists(), "Default template file not found"

    template_html = template_path.read_text(encoding="utf-8")
    renderer = NoteRendererService()

    output_png = Path("tmp_preview.png")
    output_html = Path("tmp_preview.html")

    _, html_content = renderer.render_note(
        template_html=template_html,
        category="trabalho",
        ticket_id="#123",
        text="Priorizar sprint backlog\nValidar blocos de foco",
        date=date.today().strftime("%d %b %Y"),
        output_path=output_png,
        width=384,
    )

    output_html.write_text(html_content, encoding="utf-8")

    assert output_png.exists(), "Preview PNG was not generated"
    assert output_html.exists(), "Preview HTML was not generated"
