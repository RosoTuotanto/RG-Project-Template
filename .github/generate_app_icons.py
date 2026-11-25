"""
Generate the three core Solar2D app icon files from one source image.

Usage:
    python3 generate_app_icons.py <sourceImage> <outputDir>

Outputs (written to outputDir):
    Icon.png        57x57 Solar2D simulator icon
    Icon-win32.ico  Windows icon, sizes 16 through 256
    Icon-osx.icns   macOS icon, sizes 32 through 1024

The source may be any image Pillow can decode (PNG, JPEG, WebP, BMP, ...). EXIF
orientation is normalized, then the largest centered square is cropped out. That
square must be at least 1024x1024; the tool never upscales, because enlarging
would make the icon blurry.
"""

import os
import sys
from PIL import Image, ImageOps, UnidentifiedImageError


SIMULATOR_SIZE = 57
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
ICNS_SIZES = [32, 64, 128, 256, 512, 1024]

MIN_SOURCE_SIZE = 1024

# Pillow clips these to white on a naive RGBA convert, so rescale to 8-bit first.
INTEGER_MODES = ("I", "I;16", "I;16B", "I;16L", "I;16N")


def to_rgba(image: Image.Image) -> Image.Image:
    # Integer modes carry values far above 255; rescale before the RGBA convert clips them to white.
    if image.mode in INTEGER_MODES:
        rescaled = image.convert("I").point(lambda level: level * (255.0 / 65535.0)).convert("L")
        return rescaled.convert("RGBA")
    return image.convert("RGBA")


def resize_rgba(image: Image.Image, size: int, cache: dict[int, Image.Image]) -> Image.Image:
    if size not in cache:
        if size == image.width:
            cache[size] = image
        else:
            # Premultiplied LANCZOS avoids dark halos bleeding from transparent edges.
            premultiplied = image.convert("RGBa").resize((size, size), Image.LANCZOS)
            cache[size] = premultiplied.convert("RGBA")
    return cache[size]


def center_crop_square(image: Image.Image) -> Image.Image:
    width, height = image.size
    if width == height:
        return image

    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def load_source(path: str) -> tuple[Image.Image, tuple[int, int]]:
    if not os.path.isfile(path):
        raise ValueError(f"no image file was found at: {path}")

    try:
        image = Image.open(path)
        image.load()
    except (UnidentifiedImageError, OSError):
        raise ValueError(f"the file at {path} is not an image the tool can read; use a PNG, JPEG, WebP, or BMP image")

    # Pillow re-embeds icc_profile from .info on save and copies .info into every
    # resized frame; drop it once here so no output carries a stale ICC profile.
    image.info.pop("icc_profile", None)

    # Phone photos are stored sideways with an EXIF orientation tag; apply it before
    # the crop and size checks, because 90/270 degree tags swap width and height.
    image = ImageOps.exif_transpose(image)

    image = to_rgba(image)

    original_size = image.size
    square = center_crop_square(image)

    side = square.width
    if side < MIN_SOURCE_SIZE:
        width, height = original_size
        if width == height:
            raise ValueError(f"the image is {width}x{height}, but it must be at least {MIN_SOURCE_SIZE}x{MIN_SOURCE_SIZE}; the tool never enlarges an image because that would make the icon blurry")
        raise ValueError(f"after cropping to a centered square the image is only {side}x{side} (original {width}x{height}); use a larger or more square image, at least {MIN_SOURCE_SIZE}x{MIN_SOURCE_SIZE} after cropping; the tool never enlarges an image because that would make the icon blurry")

    return square, original_size


def write_simulator_icon(out_dir: str, source: Image.Image, cache: dict[int, Image.Image]) -> str:
    frame = resize_rgba(source, SIMULATOR_SIZE, cache)
    path = os.path.join(out_dir, "Icon.png")
    frame.save(path, format="PNG")
    return path


def write_windows_icon(out_dir: str, source: Image.Image, cache: dict[int, Image.Image]) -> str:
    frames = [resize_rgba(source, size, cache) for size in ICO_SIZES]
    path = os.path.join(out_dir, "Icon-win32.ico")

    # The base frame must be the 256px one or Pillow silently drops the 256 entry;
    # the smaller frames ride along in append_images.
    frames[-1].save(path, format="ICO", sizes=[(size, size) for size in ICO_SIZES], append_images=frames[:-1])
    return path


def write_macos_icon(out_dir: str, source: Image.Image, cache: dict[int, Image.Image]) -> str:
    frames = [resize_rgba(source, size, cache) for size in ICNS_SIZES]
    path = os.path.join(out_dir, "Icon-osx.icns")

    # Pillow matches append frames by width and bicubic-resizes any missing width,
    # so pass every frame to keep all six at their native resolution.
    frames[-1].save(path, format="ICNS", append_images=frames)
    return path


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python3 generate_app_icons.py <sourceImage> <outputDir>")
        sys.exit(1)

    source_path = sys.argv[1]
    out_dir = sys.argv[2]

    try:
        source, original_size = load_source(source_path)
    except ValueError as error:
        print(f"Error: {error}")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    print(f"Source image: {source_path}")

    if source.size != original_size:
        width, height = original_size
        side = source.width
        print(f"Note: source image was {width}x{height}, cropped to a centered {side}x{side} square before resizing.")

    cache: dict[int, Image.Image] = {}

    for writer in (write_simulator_icon, write_windows_icon, write_macos_icon):
        path = writer(out_dir, source, cache)
        print(f"Wrote {os.path.basename(path)}")

    print("Done. 3 files written.")


if __name__ == "__main__":
    main()
