"""Integration tests for categories API."""

import json


class TestCategoriesAPI:
    """Tests for category endpoints."""

    def test_list_categories(self, client, sample_categories):
        """Test listing all categories."""
        response = client.get("/api/categories/")

        assert response.status_code == 200
        data = response.get_json()

        assert len(data) == 3
        assert all("name" in cat for cat in data)
        assert all("icon" in cat for cat in data)
        assert all("color" in cat for cat in data)

    def test_create_category(self, client):
        """Test creating a new category."""
        svg_icon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/></svg>'
        payload = {
            "name": "urgente",
            "label": "Urgente",
            "icon": svg_icon,
            "color": "#DC2626",
            "is_active": True,
        }

        response = client.post(
            "/api/categories/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["name"] == "urgente"
        assert data["label"] == "Urgente"
        assert data["icon"] == svg_icon
        assert data["color"] == "#DC2626"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_category_duplicate_name(self, client, sample_category):
        """Test creating a category with duplicate name."""
        payload = {
            "name": "trabalho",  # Already exists
            "label": "Another Work",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9h18v10a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/></svg>',
            "color": "#000000",
        }

        response = client.post(
            "/api/categories/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 409

    def test_create_category_invalid_color(self, client):
        """Test creating a category with invalid color format."""
        payload = {
            "name": "test",
            "label": "Test",
            "icon": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>',
            "color": "invalid-color",  # Invalid format
        }

        response = client.post(
            "/api/categories/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 422  # Validation error

    def test_get_category(self, client, sample_category):
        """Test getting a specific category."""
        response = client.get(f"/api/categories/{sample_category.id}")

        assert response.status_code == 200
        data = response.get_json()

        assert data["id"] == sample_category.id
        assert data["name"] == "trabalho"
        assert "<svg" in data["icon"]  # Check that icon contains SVG markup

    def test_get_category_not_found(self, client):
        """Test getting a non-existent category."""
        response = client.get("/api/categories/99999")

        assert response.status_code == 404

    def test_update_category(self, client, sample_category):
        """Test updating a category."""
        payload = {
            "label": "Work Updated",
            "color": "#1E40AF",
            "is_active": False,
        }

        response = client.put(
            f"/api/categories/{sample_category.id}",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["label"] == "Work Updated"
        assert data["color"] == "#1E40AF"
        assert data["is_active"] is False
        # Name should not change
        assert data["name"] == "trabalho"

    def test_update_category_not_found(self, client):
        """Test updating a non-existent category."""
        payload = {"label": "Updated"}

        response = client.put(
            "/api/categories/99999",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_delete_category(self, client, sample_category):
        """Test deleting a category without notes."""
        category_id = sample_category.id

        response = client.delete(f"/api/categories/{category_id}")

        assert response.status_code == 204

        # Verify category is deleted
        get_response = client.get(f"/api/categories/{category_id}")
        assert get_response.status_code == 404

    def test_delete_category_with_notes(self, client, sample_note):
        """Test deleting a category that has associated notes."""
        category_id = sample_note.category_id

        response = client.delete(f"/api/categories/{category_id}")

        # Should fail because category has notes
        assert response.status_code == 409

    def test_delete_category_not_found(self, client):
        """Test deleting a non-existent category."""
        response = client.delete("/api/categories/99999")

        assert response.status_code == 404

    def test_filter_active_categories(self, client):
        """Test that only active categories are typically shown."""
        # Create active and inactive categories
        from app.models import Category, db

        active_cat = Category(
            name="active",
            label="Active",
            icon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
            color="#00FF00",
            is_active=True,
        )
        inactive_cat = Category(
            name="inactive",
            label="Inactive",
            icon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
            color="#FF0000",
            is_active=False,
        )

        db.session.add_all([active_cat, inactive_cat])
        db.session.commit()

        response = client.get("/api/categories/")

        assert response.status_code == 200
        data = response.get_json()

        # All categories are returned (filtering happens on frontend)
        assert len(data) == 2

        # But we can verify the is_active field
        active_cats = [cat for cat in data if cat["is_active"]]
        assert len(active_cats) == 1
        assert active_cats[0]["name"] == "active"
