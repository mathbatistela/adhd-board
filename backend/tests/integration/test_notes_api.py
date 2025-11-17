"""Integration tests for notes API."""

import json


class TestNotesAPI:
    """Tests for note endpoints."""

    def test_create_note(self, client, sample_template, sample_category):
        """Test creating a note."""
        payload = {
            "category_id": sample_category.id,
            "text": "Complete project documentation",
            "should_print": False,
        }

        response = client.post(
            "/api/notes/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["category_id"] == sample_category.id
        assert data["category"]["name"] == "trabalho"
        assert "<svg" in data["category"]["icon"]  # Check that icon contains SVG markup
        assert data["text"] == "Complete project documentation"
        assert data["ticket_id"] == f"#{data['id']}"
        assert data["printed"] is False
        assert "id" in data
        assert "image_path" in data

    def test_create_note_with_print(self, client, sample_template, sample_category, mock_printer):
        """Test creating a note with immediate printing."""
        payload = {
            "category_id": sample_category.id,
            "text": "Review algorithms",
            "should_print": True,
        }

        response = client.post(
            "/api/notes/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["printed"] is True
        assert len(mock_printer.printed_images) == 1

    def test_create_note_no_template(self, client, sample_category):
        """Test creating a note when no templates exist."""
        payload = {
            "category_id": sample_category.id,
            "text": "Test note",
        }

        response = client.post(
            "/api/notes/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_create_note_invalid_category(self, client, sample_template):
        """Test creating a note with invalid category_id."""
        payload = {
            "category_id": 99999,
            "text": "Test note",
        }

        response = client.post(
            "/api/notes/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_get_note(self, client, sample_note):
        """Test getting a specific note."""
        response = client.get(f"/api/notes/{sample_note.id}")

        assert response.status_code == 200
        data = response.get_json()

        assert data["id"] == sample_note.id
        assert data["text"] == sample_note.text

    def test_get_note_not_found(self, client):
        """Test getting a non-existent note."""
        response = client.get("/api/notes/99999")

        assert response.status_code == 404

    def test_list_notes(self, client, sample_template, sample_category):
        """Test listing notes with pagination."""
        # Create a few notes
        for i in range(3):
            payload = {"category_id": sample_category.id, "text": f"Note {i}", "should_print": False}
            client.post(
                "/api/notes/",
                data=json.dumps(payload),
                content_type="application/json",
            )

        response = client.get("/api/notes/")

        assert response.status_code == 200
        data = response.get_json()

        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) == 3
        assert data["pagination"]["total"] == 3

    def test_list_notes_with_pagination(self, client, sample_template, sample_category):
        """Test listing notes with pagination parameters."""
        # Create multiple notes
        for i in range(25):
            payload = {"category_id": sample_category.id, "text": f"Note {i}", "should_print": False}
            client.post(
                "/api/notes/",
                data=json.dumps(payload),
                content_type="application/json",
            )

        # Get first page
        response = client.get("/api/notes/?page=1&per_page=10")

        assert response.status_code == 200
        data = response.get_json()

        assert len(data["items"]) == 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["pages"] == 3
        assert data["pagination"]["has_next"] is True

    def test_list_notes_filter_by_category(self, client, sample_template, sample_categories):
        """Test filtering notes by category."""
        trabalho_cat = sample_categories[0]
        casa_cat = sample_categories[1]

        # Create notes with different categories
        client.post(
            "/api/notes/",
            data=json.dumps({"category_id": trabalho_cat.id, "text": "Work note"}),
            content_type="application/json",
        )
        client.post(
            "/api/notes/",
            data=json.dumps({"category_id": casa_cat.id, "text": "Home note"}),
            content_type="application/json",
        )

        response = client.get(f"/api/notes/?category_id={trabalho_cat.id}")

        assert response.status_code == 200
        data = response.get_json()

        assert len(data["items"]) == 1
        assert data["items"][0]["category"]["name"] == "trabalho"

    def test_preview_note_html(self, client, sample_note):
        """Test previewing note as HTML."""
        # Need to add HTML content to sample note
        from app.models import db

        sample_note.html_content = "<html><body>Test</body></html>"
        db.session.commit()

        response = client.get(f"/api/notes/{sample_note.id}/preview?format=html")

        assert response.status_code == 200
        assert response.content_type == "text/html; charset=utf-8"
        assert b"<html>" in response.data

    def test_preview_note_image(self, client, sample_template, sample_category):
        """Test previewing note as image."""
        # Create a note (which generates an image)
        payload = {"category_id": sample_category.id, "text": "Test preview", "should_print": False}
        create_response = client.post(
            "/api/notes/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Get image preview
        response = client.get(f"/api/notes/{note_id}/preview?format=image")

        assert response.status_code == 200
        assert response.content_type == "image/png"

    def test_print_note(self, client, sample_template, sample_category, mock_printer):
        """Test printing an existing note."""
        # Create a note
        payload = {"category_id": sample_category.id, "text": "Print me later", "should_print": False}
        create_response = client.post(
            "/api/notes/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        note_id = create_response.get_json()["id"]

        # Print the note
        response = client.post(f"/api/notes/{note_id}/print")

        assert response.status_code == 200
        assert len(mock_printer.printed_images) == 1

        # Verify note is marked as printed
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.get_json()["printed"] is True

    def test_print_note_not_found(self, client):
        """Test printing a non-existent note."""
        response = client.post("/api/notes/99999/print")

        assert response.status_code == 404

    def test_update_note(self, client, sample_note):
        """Test updating a note."""
        # Create a second category for updating
        from app.models import Category, db

        new_category = Category(
            name="casa",
            label="Casa",
            icon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
            color="#10B981",
            is_active=True,
        )
        db.session.add(new_category)
        db.session.commit()

        payload = {
            "category_id": new_category.id,
            "text": "Updated note text",
        }

        response = client.patch(
            f"/api/notes/{sample_note.id}",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["category_id"] == new_category.id
        assert data["category"]["name"] == "casa"
        assert data["text"] == "Updated note text"

    def test_update_note_not_found(self, client):
        """Test updating a non-existent note."""
        payload = {"text": "Updated text"}

        response = client.patch(
            "/api/notes/99999",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_delete_note(self, client, sample_note):
        """Test deleting a note."""
        note_id = sample_note.id

        response = client.delete(f"/api/notes/{note_id}")

        assert response.status_code == 204

        # Verify note is deleted
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == 404

    def test_delete_note_not_found(self, client):
        """Test deleting a non-existent note."""
        response = client.delete("/api/notes/99999")

        assert response.status_code == 404
