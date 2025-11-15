#!/usr/bin/env python3
"""
Minimal helper to send text or bitmaps to a single, known ESC/POS USB printer.

Dependencies (install once):
    pip install python-escpos pyusb pillow
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Optional

try:
    from escpos.printer import Usb
except ImportError as exc:  # pragma: no cover - env specific
    raise SystemExit(
        "python-escpos is required. Install with `pip install python-escpos pyusb`."
    ) from exc

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dep
    Image = None


# --- Printer-specific constants (edit these once for your hardware) -----------------
VENDOR_ID = 0x6868
PRODUCT_ID = 0x0200
INTERFACE = 0
ENCODING = "utf-8"
DEFAULT_MESSAGE = "Hello from the thermal printer!"
IN_ENDPOINT = 0x81
OUT_ENDPOINT = 0x03
MAX_THERMAL_WIDTH_PX = 384  # typical printable width for 58 mm paper
THERMAL_DPI = 203  # ≈8 dots/mm for most 58 mm heads
BOTTOM_MARGIN_MM = 15  # purge ~1.5 cm before tearing
# -----------------------------------------------------------------------------------


def open_printer(
    *,
    vendor: int = VENDOR_ID,
    product: int = PRODUCT_ID,
    interface: int = INTERFACE,
) -> Usb:
    if IN_ENDPOINT is None or OUT_ENDPOINT is None:
        raise RuntimeError(
            "Set IN_ENDPOINT and OUT_ENDPOINT to your printer's endpoint addresses."
        )
    return Usb(
        idVendor=vendor,
        idProduct=product,
        interface=interface,
        in_ep=IN_ENDPOINT,
        out_ep=OUT_ENDPOINT,
    )


def advance_paper_mm(printer: Usb, margin_mm: float = BOTTOM_MARGIN_MM) -> None:
    """Feed raw dots to get a consistent physical margin (ESC J n)."""
    if margin_mm <= 0:
        return
    dots_remaining = int(round((margin_mm * THERMAL_DPI) / 25.4))
    while dots_remaining > 0:
        chunk = min(255, dots_remaining)
        printer._raw(bytes((0x1B, 0x4A, chunk)))
        dots_remaining -= chunk


def print_message(
    message: str,
    *,
    vendor: int = VENDOR_ID,
    product: int = PRODUCT_ID,
    interface: int = INTERFACE,
    encoding: str = ENCODING,
) -> None:
    printer: Optional[Usb] = None
    try:
        printer = open_printer(vendor=vendor, product=product, interface=interface)
        if not message.endswith("\n"):
            message += "\n"
        printer._raw(message.encode(encoding, errors="replace"))
        advance_paper_mm(printer, BOTTOM_MARGIN_MM)
    finally:
        if printer is not None:
            try:
                printer.close()
            except Exception:
                pass


def prepare_image(image_path: str, *, max_width: int = MAX_THERMAL_WIDTH_PX):
    if Image is None:
        raise RuntimeError(
            "Pillow is required for image printing. Install with `pip install pillow`."
        )
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    image = Image.open(path)
    image = image.convert("L")  # grayscale

    if image.width > max_width:
        ratio = max_width / image.width
        new_height = max(1, int(image.height * ratio))
        resample = getattr(Image, "LANCZOS", Image.BICUBIC)
        image = image.resize((max_width, new_height), resample=resample)

    padded_width = ((image.width + 7) // 8) * 8
    if padded_width != image.width:
        padded = Image.new("L", (padded_width, image.height), color=255)
        padded.paste(image, (0, 0))
        image = padded

    return image.convert("1")  # 1-bit monochrome optimised for ESC/POS


def print_image(
    image_path: str,
    *,
    max_width: int = MAX_THERMAL_WIDTH_PX,
    vendor: int = VENDOR_ID,
    product: int = PRODUCT_ID,
    interface: int = INTERFACE,
) -> None:
    printer: Optional[Usb] = None
    try:
        printer = open_printer(vendor=vendor, product=product, interface=interface)
        image = prepare_image(image_path, max_width=max_width)
        printer.image(image, impl="bitImageRaster")
        printer.ln()
        advance_paper_mm(printer, BOTTOM_MARGIN_MM)
    finally:
        if printer is not None:
            try:
                printer.close()
            except Exception:
                pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print text or bitmap assets on a USB thermal printer."
    )
    parser.add_argument(
        "--image",
        "-i",
        metavar="PATH",
        help="Path to a PNG/JPG to print. Falls back to text mode if omitted.",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=MAX_THERMAL_WIDTH_PX,
        help=f"Maximum image width in pixels (default {MAX_THERMAL_WIDTH_PX}).",
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to print when --image is not supplied.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.image:
            print_image(
                args.image,
                max_width=args.max_width,
            )
        else:
            message = " ".join(args.text).strip() or DEFAULT_MESSAGE
            print_message(message=message)
    except Exception as exc:
        raise SystemExit(f"Failed to print: {exc}") from exc
    return 0


if __name__ == "__main__":
    sys.exit(main())
