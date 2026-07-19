"""Prep a source photo for ASCII conversion.

Removes the background, boosts local contrast so a flatly-lit face gets
real highlights/shadows, then composites onto pure white so the empty
background maps to the blank end of the ASCII ramp.

Usage: python scripts/prep_photo.py source-photo.jpg
"""
import io
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep(
    src_path: str,
    out_path: str = "source-prepped.png",
    target_width: int = 700,
    bust_fraction: float = 0.45,
) -> None:
    with open(src_path, "rb") as f:
        cutout = remove(f.read())  # RGBA, subject isolated, transparent elsewhere

    rgba = Image.open(io.BytesIO(cutout)).convert("RGBA")

    # crop to the subject's bounding box (with a little breathing room)
    alpha = np.array(rgba.getchannel("A"))
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0:
        raise SystemExit("rembg found no subject in this photo")
    pad_x = int((xs.max() - xs.min()) * 0.08)
    pad_y = int((ys.max() - ys.min()) * 0.06)
    left = max(0, xs.min() - pad_x)
    right = min(rgba.width, xs.max() + pad_x)
    top = max(0, ys.min() - pad_y)
    bottom = min(rgba.height, ys.max() + pad_y)
    rgba = rgba.crop((left, top, right, bottom))

    # an ASCII "portrait" reads as head + shoulders, not a full-body sliver
    bust_height = max(1, int(rgba.height * bust_fraction))
    rgba = rgba.crop((0, 0, rgba.width, bust_height))

    # composite onto pure white so the removed background -> white -> space glyph
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)

    # CLAHE: pull real highlights/shadows out of a flatly-lit face
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # re-flatten anything CLAHE dragged off pure white back toward white,
    # so the background stays clean instead of turning noisy/gray
    mask = np.array(rgba.getchannel("A")) < 10
    gray[mask] = 255

    out = Image.fromarray(gray)
    scale = target_width / out.width
    out = out.resize((target_width, max(1, int(out.height * scale))), Image.LANCZOS)
    out.save(out_path)
    print(f"wrote {out_path} ({out.width}x{out.height})")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    prep(src)
