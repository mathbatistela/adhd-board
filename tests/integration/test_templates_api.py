"""Integration tests for templates API."""

import json


class TestTemplatesAPI:
    """Tests for template endpoints."""

    def test_list_templates_empty(self, client):
        """Test listing templates when none exist."""
        response = client.get("/api/templates/")

        assert response.status_code == 200
        data = response.get_json()

        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_template(self, client):
        """Test creating a template."""
        payload = {
            "name": "test-template",
            "template_html": "<html><body>{{ text }}</body></html>",
            "is_active": True,
        }

        response = client.post(
            "/api/templates/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["name"] == "test-template"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_template_duplicate_name(self, client, sample_template):
        """Test creating a template with duplicate name."""
        payload = {
            "name": sample_template.name,
            "template_html": "<html>test</html>",
        }

        response = client.post(
            "/api/templates/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_get_template(self, client, sample_template):
        """Test getting a specific template."""
        response = client.get(f"/api/templates/{sample_template.id}")

        assert response.status_code == 200
        data = response.get_json()

        assert data["id"] == sample_template.id
        assert data["name"] == sample_template.name

    def test_get_template_not_found(self, client):
        """Test getting a non-existent template."""
        response = client.get("/api/templates/99999")

        assert response.status_code == 404

    def test_update_template(self, client, sample_template):
        """Test updating a template."""
        payload = {
            "name": "updated-template",
            "is_active": False,
        }

        response = client.put(
            f"/api/templates/{sample_template.id}",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["name"] == "updated-template"
        assert data["is_active"] is False

    def test_list_templates(self, client, sample_template):
        """Test listing all templates."""
        response = client.get("/api/templates/")

        assert response.status_code == 200
        data = response.get_json()

        assert len(data) >= 1
        assert any(t["id"] == sample_template.id for t in data)
