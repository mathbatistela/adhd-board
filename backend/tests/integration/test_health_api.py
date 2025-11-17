"""Integration tests for health API."""


class TestHealthAPI:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.get_json()

        assert "status" in data
        assert "database" in data
        assert "printer" in data
        assert data["database"] == "up"
