"""Gera o icone do app (icon.png) na identidade do Iris Analyzer.

    python3 packaging/make_icon.py
"""
import math
import os

from PIL import Image, ImageDraw

S = 1024
OUT = os.path.join(os.path.dirname(__file__), "icon.png")


def gerar():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 40, S - 40, S - 40], radius=200, fill=(17, 18, 20, 255))
    cx = cy = S // 2
    R = int(S * 0.34)
    rp = int(R * 0.36)
    d.ellipse([cx - R - 14, cy - R - 14, cx + R + 14, cy + R + 14],
              outline=(233, 74, 18, 255), width=18)
    for i in range(R, rp, -1):
        t = (i - rp) / (R - rp)
        col = (int(233 * t + 120 * (1 - t)), int(74 * t + 40 * (1 - t)),
               int(18 * t + 12 * (1 - t)), 255)
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col)
    for a in range(0, 360, 5):
        ang = math.radians(a)
        d.line([cx + rp * math.cos(ang), cy + rp * math.sin(ang),
                cx + R * math.cos(ang), cy + R * math.sin(ang)],
               fill=(255, 150, 90, 90), width=3)
    d.ellipse([cx - rp, cy - rp, cx + rp, cy + rp], fill=(10, 10, 11, 255))
    d.ellipse([cx - rp + 30, cy - rp + 24, cx - rp + 92, cy - rp + 86],
              fill=(255, 255, 255, 210))
    img.save(OUT)
    print("icone salvo em", OUT)


if __name__ == "__main__":
    gerar()
