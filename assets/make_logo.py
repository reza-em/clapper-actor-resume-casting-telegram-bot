"""Generates assets/logo.jpg (640x640) and logo.png: clapperboard + spotlight, neon/elegant. Original artwork drawn in code."""
import os, math, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); S = 1280; OUT = 640
FONT = os.path.join(HERE, "..", "..", "sticker-bot", "fonts", "Vazirmatn-Bold.ttf")
if not os.path.exists(FONT): FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GOLD = (255, 200, 87); PINK = (255, 61, 154); CYAN = (64, 224, 255); BG1 = (10, 8, 28); BG2 = (38, 10, 58)

FA_WORD = "\u06a9\u0644\u0627\u06a9\u062a"  # کلاکت (ک ل ا ک ت)


def glow(layer, radius, strength=1.0):
    b = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0: b = Image.eval(b, lambda v: min(255, int(v * strength)))
    return b

def main():
    img = Image.new("RGB", (S, S), BG1); px = img.load()
    for y in range(S):                                   # vertical gradient
        t = y / S
        c = tuple(int(BG1[i] * (1 - t) + BG2[i] * t) for i in range(3))
        for x in range(S): px[x, y] = c
    img = img.convert("RGBA")
    # spotlight cone from top-left + soft pool on the floor
    cone = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(cone)
    d.polygon([(150, -20), (330, -20), (1010, 1150), (420, 1150)], fill=(255, 235, 190, 70))
    cone = cone.filter(ImageFilter.GaussianBlur(28)); img = Image.alpha_composite(img, cone)
    pool = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ImageDraw.Draw(pool).ellipse([330, 1040, 1100, 1190], fill=(255, 210, 120, 90))
    img = Image.alpha_composite(img, pool.filter(ImageFilter.GaussianBlur(30)))
    # lamp (top-left)
    lamp = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(lamp)
    d.polygon([(120, 40), (360, 40), (330, 150), (150, 150)], fill=(30, 28, 50, 255), outline=GOLD + (255,), width=6)
    d.ellipse([170, 130, 310, 175], fill=(255, 240, 200, 255)); d.rectangle([225, 10, 255, 42], fill=GOLD + (255,))
    img = Image.alpha_composite(img, glow(lamp, 14)); img = Image.alpha_composite(img, lamp)

    # clapperboard, slightly rotated
    board = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(board)
    bx0, by0, bx1, by1 = 290, 560, 1000, 1010
    d.rounded_rectangle([bx0, by0, bx1, by1], 28, fill=(18, 16, 34, 255), outline=GOLD + (255,), width=10)
    for i in range(3):                                    # table lines
        y = by0 + 130 + i * 95
        d.line([bx0 + 40, y, bx1 - 40, y], fill=CYAN + (200,), width=5)
    d.line([bx0 + 330, by0 + 60, bx0 + 330, by1 - 40], fill=CYAN + (160,), width=4)
    f = ImageFont.truetype(FONT, 58)
    d.text((bx0 + 50, by0 + 38), "SCENE  TAKE", font=f, fill=GOLD + (255,))
    # clapper stick (top bar) drawn open at an angle
    bar = Image.new("RGBA", (S, S), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
    x0, y0, w, h = bx0 - 5, 440, bx1 - bx0 + 10, 100
    bd.rounded_rectangle([x0, y0, x0 + w, y0 + h], 18, fill=(18, 16, 34, 255), outline=PINK + (255,), width=10)
    sw = 110
    for i, sx in enumerate(range(x0 + 20, x0 + w - sw, sw * 2)):   # diagonal stripes
        bd.polygon([(sx, y0 + h - 8), (sx + sw - 30, y0 + h - 8), (sx + sw + 25, y0 + 8), (sx + 55, y0 + 8)], fill=(255, 61, 154, 255) if i % 2 == 0 else (255, 200, 87, 255))
    bd.rounded_rectangle([x0, y0, x0 + w, y0 + h], 18, outline=PINK + (255,), width=10)
    bar = bar.rotate(14, resample=Image.BICUBIC, center=(x0 + 30, y0 + h))
    # hinge
    d.ellipse([bx0 - 2, by0 - 34, bx0 + 60, by0 + 28], fill=GOLD + (255,))
    board_glow = glow(board, 16, 1.4); bar_glow = glow(bar, 16, 1.4)
    for layer in (board_glow, bar_glow, board, bar): img = Image.alpha_composite(img, layer)

    # title
    tl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
    # Persian «کلاکت»: never shape twice. With libraqm (HarfBuzz) Pillow joins + orders RTL itself from the RAW
    # logical string; otherwise fall back to arabic_reshaper (joins) + python-bidi (RTL order) on the BASIC engine.
    from PIL import features
    if features.check("raqm"):
        tf = ImageFont.truetype(FONT, 118, layout_engine=ImageFont.Layout.RAQM)
        fa_txt, kw = FA_WORD, dict(direction="rtl", language="fa")
    else:
        import arabic_reshaper
        from bidi.algorithm import get_display
        tf = ImageFont.truetype(FONT, 118, layout_engine=ImageFont.Layout.BASIC)
        fa_txt, kw = get_display(arabic_reshaper.reshape(FA_WORD)), {}
    w = td.textlength(fa_txt, font=tf, **kw)
    td.text(((S - w) / 2 + 250, 1070), fa_txt, font=tf, fill=(255, 255, 255, 255), **kw)
    en = ImageFont.truetype(FONT, 64); td.text((70, 1130), "CLAPPER", font=en, fill=CYAN + (255,))
    img = Image.alpha_composite(img, glow(tl, 10, 1.2)); img = Image.alpha_composite(img, tl)
    # sparkles
    sp = Image.new("RGBA", (S, S), (0, 0, 0, 0)); sd = ImageDraw.Draw(sp)
    for (x, y, r) in [(1100, 260, 26), (960, 380, 16), (1180, 520, 12), (760, 210, 14), (1040, 140, 10)]:
        sd.polygon([(x, y - r * 2), (x + r * .5, y - r * .5), (x + r * 2, y), (x + r * .5, y + r * .5), (x, y + r * 2), (x - r * .5, y + r * .5), (x - r * 2, y), (x - r * .5, y - r * .5)], fill=(255, 240, 200, 255))
    img = Image.alpha_composite(img, glow(sp, 8, 1.5)); img = Image.alpha_composite(img, sp)
    out = img.convert("RGB").resize((OUT, OUT), Image.LANCZOS)
    out.save(os.path.join(HERE, "logo.jpg"), quality=92, optimize=True); out.save(os.path.join(HERE, "logo.png"), optimize=True)
    print("saved", os.path.join(HERE, "logo.jpg"))
if __name__ == "__main__": main()
