"""Manual test that renders and prints a note through the service layer.

Run with:
    source .venv/bin/activate && pytest tests/manual/test_print_note.py

By default this uses the mock printer so you can verify the image that would be
sent to hardware without actually printing. To use the real printer, set the
`MANUAL_PRINT_USE_PRINTER=1` environment variable before running the test.
"""

from __future__ import annotations

import os
from pathlib import Path

from app import create_app
from app.config import Settings
from app.models import db
from app.services.printer import MockPrinterService


def test_manual_print_note():
    """Render a note and send it to the configured printer service."""
    template_path = Path("app/templates/default_note.html")
    assert template_path.exists(), "Default template not found"
    template_html = template_path.read_text(encoding="utf-8")

    upload_folder = Path("uploads")
    upload_folder.mkdir(exist_ok=True)

    db_path = Path("tmp_manual_print.db")
    if db_path.exists():
        db_path.unlink()

    use_real_printer = os.getenv("MANUAL_PRINT_USE_PRINTER") == "1"

    settings = Settings(
        flask_env="testing",
        secret_key="manual-print-secret",
        debug=True,
        database_url=f"sqlite:///{db_path}",
        printer_enabled=use_real_printer,
        upload_folder=upload_folder,
    )

    app = create_app(settings)

    with app.app_context():
        db.create_all()

        template = app.template_service.create_template(
            name="manual-print-template",
            template_html=template_html,
            is_active=True,
        )

        note = app.note_service.create_note(
            category="trabalho",
            text="Teste manual de impressão\nConfirme o novo tamanho do ticket",
            template_id=template.id,
            should_print=False,
        )

        # Ensure the renderer generated an asset we can inspect
        assert note.image_path is not None
        rendered_image = Path(note.image_path)
        assert rendered_image.exists(), f"Rendered image not found: {rendered_image}"

        success = app.note_service.print_note(note.id)
        assert success is True, "Printer service reported a failure"

        printer_service = app.printer_service
        if isinstance(printer_service, MockPrinterService):
            assert (
                printer_service.printed_images
            ), "Mock printer did not record any printed images"

            latest_print = Path(printer_service.printed_images[-1])
            assert latest_print.exists(), "Mock printer image path is missing on disk"

            # Copy to repo root for quick inspection
            preview_copy = Path("tmp_printed_note.png")
            preview_copy.write_bytes(latest_print.read_bytes())

        db.session.remove()
        db.drop_all()

    if db_path.exists():
        db_path.unlink()
