"""Unit tests for printer service."""

import pytest

from app.services.printer import MockPrinterService, PrinterService


class TestMockPrinterService:
    """Tests for mock printer service."""

    def test_print_image(self, tmp_path):
        """Test printing an image."""
        service = MockPrinterService()

        # Create a test image file
        image_path = tmp_path / "test.png"
        image_path.write_text("fake image data")

        result = service.print_image(str(image_path))

        assert result is True
        assert str(image_path) in service.printed_images
        assert len(service.printed_images) == 1

    def test_print_text(self):
        """Test printing text."""
        service = MockPrinterService()

        result = service.print_text("Test message")

        assert result is True
        assert "Test message" in service.printed_texts
        assert len(service.printed_texts) == 1

    def test_is_available(self):
        """Test printer availability check."""
        service = MockPrinterService()

        assert service.is_available() is True

        service.set_available(False)
        assert service.is_available() is False

    def test_reset(self):
        """Test resetting mock state."""
        service = MockPrinterService()

        service.print_text("Test 1")
        service.print_text("Test 2")
        service.set_available(False)

        service.reset()

        assert len(service.printed_texts) == 0
        assert len(service.printed_images) == 0
        assert service.is_available() is True


class TestPrinterService:
    """Tests for real printer service (mocked USB connection)."""

    def test_initialization(self):
        """Test printer service initialization."""
        service = PrinterService(
            vendor_id=0x6868,
            product_id=0x0200,
            interface=0,
            in_endpoint=0x81,
            out_endpoint=0x03,
        )

        assert service.vendor_id == 0x6868
        assert service.product_id == 0x0200
        assert service.encoding == "utf-8"
        assert service.max_width == 384

    def test_is_available_no_printer(self):
        """Test availability check when no printer is connected."""
        service = PrinterService(
            vendor_id=0xFFFF,  # Non-existent device
            product_id=0xFFFF,
            interface=0,
            in_endpoint=0x81,
            out_endpoint=0x03,
        )

        # Should return False when printer is not available
        assert service.is_available() is False

    @pytest.mark.skipif(
        True,  # Skip by default unless running with real hardware
        reason="Requires actual thermal printer hardware connected via USB",
    )
    def test_print_with_real_printer(self):
        """
        Integration test with real printer hardware.

        To run this test:
        1. Connect your thermal printer via USB
        2. Update vendor_id and product_id
        3. Run: pytest -m real_printer tests/unit/test_printer_service.py
        """
        service = PrinterService(
            vendor_id=0x6868,
            product_id=0x0200,
            interface=0,
            in_endpoint=0x81,
            out_endpoint=0x03,
        )

        # Test text printing
        result = service.print_text("Test print from pytest")
        assert result is True

        # Test availability
        assert service.is_available() is True
