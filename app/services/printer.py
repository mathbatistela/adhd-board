"""Printer service abstraction for testability."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from PIL import Image

try:
    import usb.core
except ImportError:  # pragma: no cover
    usb = None

logger = logging.getLogger(__name__)


class IPrinterService(Protocol):
    """Printer service interface."""

    def print_image(self, image_path: str | Path) -> bool:
        """Print an image file."""
        ...

    def print_text(self, text: str) -> bool:
        """Print raw text."""
        ...

    def is_available(self) -> bool:
        """Check if printer is available."""
        ...


class BasePrinterService(ABC):
    """Abstract base class for printer services."""

    @abstractmethod
    def print_image(self, image_path: str | Path) -> bool:
        """Print an image file. Returns True if successful."""
        pass

    @abstractmethod
    def print_text(self, text: str) -> bool:
        """Print raw text. Returns True if successful."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if printer is available and ready."""
        pass


class PrinterService(BasePrinterService):
    """Real printer service using python-escpos."""

    def __init__(
        self,
        vendor_id: int,
        product_id: int,
        interface: int,
        in_endpoint: int,
        out_endpoint: int,
        encoding: str = "utf-8",
        max_width: int = 384,
        bottom_margin_mm: float = 15.0,
        thermal_dpi: int = 203,
    ):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.interface = interface
        self.in_endpoint = in_endpoint
        self.out_endpoint = out_endpoint
        self.encoding = encoding
        self.max_width = max_width
        self.bottom_margin_mm = bottom_margin_mm
        self.thermal_dpi = thermal_dpi

    def _device_present(self) -> bool:
        """Check if the USB device is present using pyusb."""
        if usb is None:
            # pyusb not available; fall back to legacy behavior
            return True
        try:
            device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
            return device is not None
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Unable to query USB device: {exc}")
            return False

    def _open_printer(self):
        """Open connection to USB printer."""
        try:
            from escpos.printer import Usb

            return Usb(
                idVendor=self.vendor_id,
                idProduct=self.product_id,
                interface=self.interface,
                in_ep=self.in_endpoint,
                out_ep=self.out_endpoint,
            )
        except ImportError as exc:
            logger.error("python-escpos not installed")
            raise RuntimeError("python-escpos is required for printer support") from exc
        except Exception as exc:
            logger.error(f"Failed to open printer: {exc}")
            raise

    def _advance_paper(self, printer) -> None:
        """Feed paper to create bottom margin."""
        if self.bottom_margin_mm <= 0:
            return

        dots_remaining = int(round((self.bottom_margin_mm * self.thermal_dpi) / 25.4))
        while dots_remaining > 0:
            chunk = min(255, dots_remaining)
            printer._raw(bytes((0x1B, 0x4A, chunk)))
            dots_remaining -= chunk

    def _prepare_image(self, image_path: str | Path) -> Image.Image:
        """Prepare image for thermal printing."""
        path = Path(image_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")

        image = Image.open(path).convert("L")  # Grayscale

        # Resize if too wide
        if image.width > self.max_width:
            ratio = self.max_width / image.width
            new_height = max(1, int(image.height * ratio))
            resample = getattr(Image, "LANCZOS", Image.BICUBIC)
            image = image.resize((self.max_width, new_height), resample=resample)

        # Pad width to multiple of 8
        padded_width = ((image.width + 7) // 8) * 8
        if padded_width != image.width:
            padded = Image.new("L", (padded_width, image.height), color=255)
            padded.paste(image, (0, 0))
            image = padded

        return image.convert("1")  # 1-bit monochrome

    def print_image(self, image_path: str | Path) -> bool:
        """Print an image file."""
        printer = None
        try:
            printer = self._open_printer()
            image = self._prepare_image(image_path)
            printer.image(image, impl="bitImageRaster")
            printer.ln()
            self._advance_paper(printer)
            logger.info(f"Successfully printed image: {image_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to print image {image_path}: {exc}")
            return False
        finally:
            if printer is not None:
                try:
                    printer.close()
                except Exception:
                    pass

    def print_text(self, text: str) -> bool:
        """Print raw text."""
        printer = None
        try:
            printer = self._open_printer()
            if not text.endswith("\n"):
                text += "\n"
            printer._raw(text.encode(self.encoding, errors="replace"))
            self._advance_paper(printer)
            logger.info(f"Successfully printed text: {text[:50]}...")
            return True
        except Exception as exc:
            logger.error(f"Failed to print text: {exc}")
            return False
        finally:
            if printer is not None:
                try:
                    printer.close()
                except Exception:
                    pass

    def is_available(self) -> bool:
        """Check if printer is available."""
        if not self._device_present():
            return False
        try:
            printer = self._open_printer()
            printer.close()
            return True
        except Exception as exc:
            logger.warning(f"Printer not available: {exc}")
            return False


class MockPrinterService(BasePrinterService):
    """Mock printer service for testing."""

    def __init__(self):
        self.printed_images: list[str] = []
        self.printed_texts: list[str] = []
        self._available = True

    def print_image(self, image_path: str | Path) -> bool:
        """Mock print image."""
        logger.info(f"[MOCK] Printing image: {image_path}")
        self.printed_images.append(str(image_path))
        return self._available

    def print_text(self, text: str) -> bool:
        """Mock print text."""
        logger.info(f"[MOCK] Printing text: {text[:50]}...")
        self.printed_texts.append(text)
        return self._available

    def is_available(self) -> bool:
        """Mock availability check."""
        return self._available

    def set_available(self, available: bool) -> None:
        """Set mock availability for testing."""
        self._available = available

    def reset(self) -> None:
        """Reset mock state."""
        self.printed_images.clear()
        self.printed_texts.clear()
        self._available = True


def get_printer_service(
    enabled: bool,
    vendor_id: int,
    product_id: int,
    interface: int,
    in_endpoint: int,
    out_endpoint: int,
    encoding: str = "utf-8",
    max_width: int = 384,
    bottom_margin_mm: float = 15.0,
    thermal_dpi: int = 203,
) -> BasePrinterService:
    """Factory function to get appropriate printer service."""
    if not enabled:
        logger.info("Printer disabled, using mock service")
        return MockPrinterService()

    return PrinterService(
        vendor_id=vendor_id,
        product_id=product_id,
        interface=interface,
        in_endpoint=in_endpoint,
        out_endpoint=out_endpoint,
        encoding=encoding,
        max_width=max_width,
        bottom_margin_mm=bottom_margin_mm,
        thermal_dpi=thermal_dpi,
    )
