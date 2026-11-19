"""Square 1024 px icon for the plugin listing."""
import pathlib
from PIL import Image, ImageDraw, ImageFont

out = pathlib.Path(__file__).resolve().parents[1] / "tools" / "icon.png"
S = 1024
im = Image.new("RGB", (S, S), "#0f172a")
d = ImageDraw.Draw(im)
d.rounded_rectangle((96, 96, S - 96, S - 96), radius=150, outline="#38bdf8", width=28)
font = None
for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"):
    try:
        font = ImageFont.truetype(name, 520)
        break
    except OSError:
        pass
font = font or ImageFont.load_default()
d.text((S // 2, S // 2 - 90), "[1]", font=font, fill="#f8fafc", anchor="mm")
small = ImageFont.truetype(font.path, 96) if hasattr(font, "path") else font
d.text((S // 2, S - 215), "cited by AI", font=small, fill="#38bdf8", anchor="mm")
out.parent.mkdir(parents=True, exist_ok=True)
im.save(out, optimize=True)
print(out, out.stat().st_size)
