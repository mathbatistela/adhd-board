"""Unit tests for note renderer service."""

from app.services.note_renderer import NoteRendererService


class TestNoteRendererService:
    """Tests for note renderer service."""

    def test_resolve_category_icon(self):
        """Test category icon resolution."""
        service = NoteRendererService()

        assert service.resolve_category_icon("casa") == "🏠"
        assert service.resolve_category_icon("trabalho") == "💼"
        assert service.resolve_category_icon("estudos") == "📚"
        assert service.resolve_category_icon("saude") == "💊"
        assert service.resolve_category_icon("unknown") == "⭐"
        assert service.resolve_category_icon("") == "⭐"

    def test_resolve_category_icon_case_insensitive(self):
        """Test category icon resolution is case-insensitive."""
        service = NoteRendererService()

        assert service.resolve_category_icon("CASA") == "🏠"
        assert service.resolve_category_icon("Trabalho") == "💼"

    def test_build_html(self):
        """Test HTML building with placeholders."""
        service = NoteRendererService()

        template = """
        <div class="note">
            <span>{{ ticket_id }}</span>
            <span>{{ category_icon|safe }}</span>
            <p>{{ text }}</p>
            <span>{{ date }}</span>
            <style>body { width: {{ width }}px; }</style>
        </div>
        """

        svg_icon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>'
        html = service.build_html(
            template_html=template,
            category_icon=svg_icon,
            ticket_id="#42",
            text="Test note\nwith newline",
            date="16 Nov 2024",
            width=384,
        )

        assert "#42" in html
        assert svg_icon in html
        assert "Test note<br />with newline" in html
        assert "16 Nov 2024" in html
        assert "384px" in html

    def test_build_html_escapes_content(self):
        """Test that HTML special characters are escaped in user content."""
        service = NoteRendererService()

        template = "<div>{{ text }}</div>"

        svg_icon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>'
        html = service.build_html(
            template_html=template,
            category_icon=svg_icon,
            ticket_id="#1",
            text="<script>alert('xss')</script>",
            date="16 Nov 2024",
            width=384,
        )

        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_render_to_png(self, app, tmp_path):
        """Test rendering HTML to PNG."""
        service = NoteRendererService(default_width=384)

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { width: 384px; margin: 0; padding: 10px; }
                .note { background: white; padding: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="note">
                <h1>Test Note</h1>
                <p>This is a test note for rendering.</p>
            </div>
        </body>
        </html>
        """

        output_path = tmp_path / "test_render.png"

        result = service.render_to_png(html, output_path, width=384)

        assert result.exists()
        assert result.suffix == ".png"
        assert result.stat().st_size > 0

    def test_render_note_complete(self, app, tmp_path):
        """Test complete note rendering."""
        service = NoteRendererService(default_width=384)

        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { width: {{ width }}px; margin: 0; }
                .note { padding: 20px; text-align: center; background: white; }
                .category-icon { width: 32px; height: 32px; display: inline-flex; }
                .category-icon svg { width: 100%; height: 100%; }
            </style>
        </head>
        <body>
            <div class="note">
                <div>{{ ticket_id }}</div>
                <div class="category-icon">{{ category_icon|safe }}</div>
                <div>{{ text }}</div>
                <div>{{ date }}</div>
            </div>
        </body>
        </html>
        """

        output_path = tmp_path / "complete_note.png"

        svg_icon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9h18v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/></svg>'
        image_path, html_content = service.render_note(
            template_html=template,
            category_icon=svg_icon,
            ticket_id="#5",
            text="Complete test note",
            date="16 Nov 2024",
            output_path=output_path,
            width=384,
        )

        assert image_path.exists()
        assert svg_icon in html_content
        assert "#5" in html_content
        assert "Complete test note" in html_content
