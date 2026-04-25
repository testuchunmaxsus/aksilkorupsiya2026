"""Remove near-white background from logo.png and save with transparency."""
from PIL import Image
from pathlib import Path

SRC = Path("D:/hackaton/logo.png")
DST = Path("D:/hackaton/auksionwatch/frontend/public/logo.png")

# Tolerance for "near white" pixels (0-255 scale)
TOL = 18


def main():
    img = Image.open(SRC).convert("RGBA")
    w, h = img.size
    px = img.load()

    # Flood-fill style: any pixel close to white becomes fully transparent.
    # Edge softening: pixels in the threshold band become semi-transparent.
    edges_band = TOL + 22

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            mn = min(r, g, b)
            mx = max(r, g, b)
            # white-ish: all channels high and roughly equal
            if r >= 255 - TOL and g >= 255 - TOL and b >= 255 - TOL:
                px[x, y] = (255, 255, 255, 0)
            elif r >= 255 - edges_band and g >= 255 - edges_band and b >= 255 - edges_band and (mx - mn) < 14:
                # gradient between full opacity and transparent
                # how much "white" — closer to white -> more transparent
                avg = (r + g + b) / 3
                fade = (avg - (255 - edges_band)) / edges_band  # 0..1
                new_a = max(0, int(a * (1 - fade)))
                px[x, y] = (r, g, b, new_a)

    DST.parent.mkdir(parents=True, exist_ok=True)
    img.save(DST, "PNG", optimize=True)

    # Also save a square icon version (cropped to logo mark only — left ~28%)
    icon_w = int(w * 0.32)
    icon = img.crop((0, 0, icon_w, h))
    # tighten bbox
    bbox = icon.getbbox()
    if bbox:
        icon = icon.crop(bbox)
    icon_path = DST.parent / "logo-icon.png"
    icon.save(icon_path, "PNG", optimize=True)

    print(f"saved {DST} ({DST.stat().st_size} bytes)")
    print(f"saved {icon_path} ({icon_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
