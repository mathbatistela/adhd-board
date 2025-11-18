"""Printer service abstraction for testability."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from PIL import Image

try:
    import usb.core
    import usb.util
except ImportError:  # pragma: no cover
    usb = None

logger = logging.getLogger(__name__)

# Module-level cache for auto-detected printer config (persists until server restart)
_PRINTER_CONFIG_CACHE: dict | None = None

# Thermal printer vendor to search for
THERMAL_PRINTER_VENDOR = 0x6868  # gxmc and generic thermal printers


def auto_detect_printer() -> dict | None:
    """
    Automatically detect a thermal printer from vendor 0x6868 using pyusb.
    Results are cached until server restart.

    Returns:
        Dictionary with vendor_id, product_id, interface, in_endpoint, out_endpoint
        or None if not found.
    """
    global _PRINTER_CONFIG_CACHE

    # Return cached config if available
    if _PRINTER_CONFIG_CACHE is not None:
        logger.debug("Using cached printer configuration")
        return _PRINTER_CONFIG_CACHE

    if usb is None:
        logger.warning("pyusb not available, cannot auto-detect printer")
        return None

    try:
        # Find device with vendor ID 0x6868
        device = usb.core.find(idVendor=THERMAL_PRINTER_VENDOR)

        if device is None:
            logger.warning(f"No printer found with vendor ID {hex(THERMAL_PRINTER_VENDOR)}")
            return None

        logger.info(f"Found printer: VID={hex(device.idVendor)}, PID={hex(device.idProduct)}")

        # Extract USB configuration
        cfg = device[0]
        intf = cfg[(0, 0)]  # First interface

        in_endpoint = None
        out_endpoint = None

        for ep in intf:
            ep_dir = usb.util.endpoint_direction(ep.bEndpointAddress)
            ep_type = usb.util.endpoint_type(ep.bmAttributes)

            if ep_type == usb.util.ENDPOINT_TYPE_BULK:
                if ep_dir == usb.util.ENDPOINT_IN:
                    in_endpoint = ep.bEndpointAddress
                else:
                    out_endpoint = ep.bEndpointAddress

        if not in_endpoint or not out_endpoint:
            logger.error("Could not find both IN and OUT bulk endpoints")
            return None

        config = {
            "vendor_id": device.idVendor,
            "product_id": device.idProduct,
            "interface": intf.bInterfaceNumber,
            "in_endpoint": in_endpoint,
            "out_endpoint": out_endpoint,
        }

        logger.info(
            f"Auto-detected printer config: VID={hex(config['vendor_id'])}, "
            f"PID={hex(config['product_id'])}, interface={config['interface']}, "
            f"in_ep={hex(config['in_endpoint'])}, out_ep={hex(config['out_endpoint'])}"
        )

        # Cache the configuration
        _PRINTER_CONFIG_CACHE = config
        return config

    except Exception as exc:
        logger.error(f"Error during printer auto-detection: {exc}")
        return None


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
    """Real printer service using python-escpos with auto-detection."""

    def __init__(
        self,
        encoding: str = "utf-8",
        max_width: int = 384,
        bottom_margin_mm: float = 15.0,
        thermal_dpi: int = 203,
    ):
        # Auto-detect printer configuration at initialization
        config = auto_detect_printer()

        if not config:
            raise RuntimeError("No thermal printer found during auto-detection")

        self.vendor_id = config["vendor_id"]
        self.product_id = config["product_id"]
        self.interface = config["interface"]
        self.in_endpoint = config["in_endpoint"]
        self.out_endpoint = config["out_endpoint"]
        self.encoding = encoding
        self.max_width = max_width
        self.bottom_margin_mm = bottom_margin_mm
        self.thermal_dpi = thermal_dpi

        logger.info(
            f"Printer service initialized: VID={hex(self.vendor_id)}, "
            f"PID={hex(self.product_id)}"
        )

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
        """Check if printer USB device is present (does not attempt to open)."""
        return self._device_present()


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
    encoding: str = "utf-8",
    max_width: int = 384,
    bottom_margin_mm: float = 15.0,
    thermal_dpi: int = 203,
) -> BasePrinterService:
    """Factory function to get appropriate printer service with auto-detection."""
    if not enabled:
        logger.info("Printer disabled, using mock service")
        return MockPrinterService()

    # Try to create printer service with auto-detection
    try:
        logger.info("Auto-detecting thermal printer...")
        return PrinterService(
            encoding=encoding,
            max_width=max_width,
            bottom_margin_mm=bottom_margin_mm,
            thermal_dpi=thermal_dpi,
        )
    except RuntimeError as exc:
        logger.error(f"Printer auto-detection failed: {exc}. Using mock service.")
        return MockPrinterService()
