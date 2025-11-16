"""Unit tests for template service."""

import pytest

from app.services.template_service import TemplateService


class TestTemplateService:
    """Tests for template service."""

    def test_create_template(self, app):
        """Test creating a template."""
        service = TemplateService()

        template = service.create_template(
            name="test-template",
            template_html="<html>{{ text }}</html>",
            is_active=True,
        )

        assert template.id is not None
        assert template.name == "test-template"
        assert template.is_active is True

    def test_create_duplicate_template(self, app, sample_template):
        """Test creating a template with duplicate name."""
        service = TemplateService()

        with pytest.raises(ValueError, match="already exists"):
            service.create_template(
                name=sample_template.name,
                template_html="<html>test</html>",
            )

    def test_get_template(self, app, sample_template):
        """Test getting a template by ID."""
        service = TemplateService()

        template = service.get_template(sample_template.id)

        assert template is not None
        assert template.id == sample_template.id
        assert template.name == sample_template.name

    def test_get_template_not_found(self, app):
        """Test getting a non-existent template."""
        service = TemplateService()

        template = service.get_template(99999)

        assert template is None

    def test_get_template_by_name(self, app, sample_template):
        """Test getting a template by name."""
        service = TemplateService()

        template = service.get_template_by_name(sample_template.name)

        assert template is not None
        assert template.name == sample_template.name

    def test_list_templates(self, app, sample_template):
        """Test listing all templates."""
        service = TemplateService()

        # Create another template
        service.create_template(
            name="another-template",
            template_html="<html>another</html>",
            is_active=False,
        )

        templates = service.list_templates()

        assert len(templates) == 2

    def test_list_active_templates_only(self, app, sample_template):
        """Test listing only active templates."""
        service = TemplateService()

        # Create inactive template
        service.create_template(
            name="inactive-template",
            template_html="<html>inactive</html>",
            is_active=False,
        )

        templates = service.list_templates(active_only=True)

        assert len(templates) == 1
        assert templates[0].is_active is True

    def test_update_template(self, app, sample_template):
        """Test updating a template."""
        service = TemplateService()

        updated = service.update_template(
            sample_template.id,
            name="updated-name",
            is_active=False,
        )

        assert updated is not None
        assert updated.name == "updated-name"
        assert updated.is_active is False

    def test_update_template_not_found(self, app):
        """Test updating a non-existent template."""
        service = TemplateService()

        result = service.update_template(99999, name="test")

        assert result is None

    def test_get_default_template(self, app, sample_template):
        """Test getting default template."""
        service = TemplateService()

        # Create a template named "default"
        default = service.create_template(
            name="default",
            template_html="<html>default</html>",
            is_active=True,
        )

        template = service.get_default_template()

        assert template.name == "default"

    def test_get_default_template_fallback(self, app, sample_template):
        """Test getting default template when no 'default' exists."""
        service = TemplateService()

        template = service.get_default_template()

        # Should return any active template
        assert template is not None
        assert template.is_active is True

    def test_get_default_template_none_available(self, app):
        """Test getting default template when none exist."""
        service = TemplateService()

        with pytest.raises(ValueError, match="No active templates available"):
            service.get_default_template()
