#!/usr/bin/env python3
"""Generate images/og-default.png — the RenoBeam social share card (1200x630).

Text-only design on the brand charcoal: "Reno" in off-white + "Beam" in the
amber-to-orange beam gradient, a thin gradient beam rule, tagline beneath,
subtle rounded border. Rendered at 2x and downscaled for crisp edges.

Run:  python3 tools/make_og.py
Requires: Pillow
"""

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "images", "og-default.png")

W, H = 1200, 630
S = 2  # supersample factor
CW, CH = W * S, H * S

# Brand palette (css/style.css)
BG = (10, 10, 13)            # --bg-0 #0a0a0d
TEXT = (245, 243, 239)       # --text #f5f3ef
AMBER = (251, 191, 36)       # --amber #fbbf24
ORANGE = (249, 115, 22)      # --orange #f97316
EMBER = (234, 88, 12)        # --ember #ea580c
PALE = (253, 230, 138)       # #fde68a (beam-grad start)

# Beam gradient stops: (position 0..1, rgb) — mirrors --beam-grad
GRAD = [(0.0, PALE), (0.30, AMBER), (0.75, ORANGE), (1.0, EMBER)]


def find_font(candidates, size):
    """Return the first loadable font from (path, index) candidates."""
    for path, index in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=index)
            except OSError:
                continue
    return ImageFont.load_default()


def bold_font(size):
    return find_font([
        ("/System/Library/Fonts/HelveticaNeue.ttc", 1),   # Bold face
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 1),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),
    ], size)


def medium_font(size):
    return find_font([
        ("/System/Library/Fonts/HelveticaNeue.ttc", 10),  # Medium face
        ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0),
    ], size)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def grad_color(t):
    """Color at position t (0..1) along the beam gradient."""
    t = max(0.0, min(1.0, t))
    for (p0, c0), (p1, c1) in zip(GRAD, GRAD[1:]):
        if t <= p1:
            span = (p1 - p0) or 1.0
            return lerp(c0, c1, (t - p0) / span)
    return GRAD[-1][1]


def gradient_strip(width, height):
    """Horizontal beam-gradient image of the given size."""
    strip = Image.new("RGB", (width, 1))
    px = strip.load()
    for x in range(width):
        px[x, 0] = grad_color(x / max(width - 1, 1))
    return strip.resize((width, height))


def soft_glow(img, center, radius, color, alpha):
    """Paint a blurred radial glow onto img."""
    glow = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(glow)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=alpha)
    glow = glow.filter(ImageFilter.GaussianBlur(radius * 0.55))
    overlay = Image.new("RGB", img.size, color)
    img.paste(overlay, (0, 0), glow)


def main():
    img = Image.new("RGB", (CW, CH), BG)

    # Very subtle brand glows — amber upper-left, orange lower-right.
    soft_glow(img, (int(CW * 0.18), int(CH * 0.06)), int(CW * 0.30), AMBER, 26)
    soft_glow(img, (int(CW * 0.85), int(CH * 0.98)), int(CW * 0.32), EMBER, 30)

    # Subtle rounded border (low-alpha off-white).
    inset = 26 * S
    border_layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border_layer)
    bd.rounded_rectangle(
        [inset, inset, CW - inset, CH - inset],
        radius=22 * S, outline=(245, 243, 239, 46), width=2 * S)
    img.paste(border_layer, (0, 0), border_layer)
    draw = ImageDraw.Draw(img)

    # ---- Wordmark: "Reno" off-white + "Beam" beam-gradient ----------------
    wm_font = bold_font(148 * S)
    reno, beam = "Reno", "Beam"
    reno_w = draw.textlength(reno, font=wm_font)
    beam_w = draw.textlength(beam, font=wm_font)
    total_w = reno_w + beam_w
    wm_x = (CW - total_w) / 2
    wm_y = 178 * S  # top of wordmark text box

    draw.text((wm_x, wm_y), reno, font=wm_font, fill=TEXT)

    # "Beam" — render as a mask, fill with the gradient.
    mask = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(mask).text((wm_x + reno_w, wm_y), beam, font=wm_font, fill=255)
    bbox = mask.getbbox()
    if bbox:
        grad = gradient_strip(bbox[2] - bbox[0], bbox[3] - bbox[1])
        grad_full = Image.new("RGB", (CW, CH), BG)
        grad_full.paste(grad, (bbox[0], bbox[1]))
        img.paste(grad_full, (0, 0), mask)

    # ---- Thin beam rule under the wordmark --------------------------------
    ascent, descent = wm_font.getmetrics()
    rule_w, rule_h = 380 * S, 5 * S
    rule_x = (CW - rule_w) // 2
    rule_y = int(wm_y + ascent + descent + 34 * S)
    rule = gradient_strip(rule_w, rule_h)
    # Slight glow behind the rule.
    glow_mask = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(glow_mask).rectangle(
        [rule_x, rule_y, rule_x + rule_w, rule_y + rule_h], fill=120)
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(10 * S))
    img.paste(Image.new("RGB", (CW, CH), ORANGE), (0, 0), glow_mask)
    img.paste(rule, (rule_x, rule_y))
    draw = ImageDraw.Draw(img)

    # ---- Tagline + sub-line ----------------------------------------------
    tag_font = bold_font(46 * S)
    tag = "Photos in. Quote out."
    tag_w = draw.textlength(tag, font=tag_font)
    tag_y = rule_y + rule_h + 38 * S
    draw.text(((CW - tag_w) / 2, tag_y), tag, font=tag_font, fill=TEXT)

    sub_font = medium_font(27 * S)
    sub = "AI renovation estimates in minutes  •  built by a working contractor"
    sub_w = draw.textlength(sub, font=sub_font)
    sub_y = tag_y + 74 * S
    # Muted sub-line: draw on an RGBA layer at partial alpha.
    sub_layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sub_layer)
    sd.text(((CW - sub_w) / 2, sub_y), sub, font=sub_font, fill=(245, 243, 239, 150))
    img.paste(sub_layer, (0, 0), sub_layer)

    # ---- Downscale + save -------------------------------------------------
    final = img.resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    final.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({W}x{H}, {os.path.getsize(OUT)//1024} KB)")


if __name__ == "__main__":
    main()
