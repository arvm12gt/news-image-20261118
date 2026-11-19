#!/usr/bin/env python3
"""Render entry.png (1024x1024): an editorial front-page poster that sums up
18 November 2026 world news in one image.

Everything is drawn in code with Pillow -- crisp vector-style shapes and real
rendered text, so every headline stays legible (unlike AI-generated images).
Run:  python3 build_image.py   ->  writes entry.png next to this file.
"""

import glob
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

W = H = 1024
PAPER = (247, 242, 231)   # #f7f2e7
INK = (25, 25, 34)        # #191922
RED = (179, 49, 42)       # #b3312a
NAVY = (20, 64, 107)      # #14406b
GOLD = (201, 162, 39)     # #c9a227
SMOKE = (150, 144, 128)
WHITE = (255, 255, 255)

MARGIN = 44
CONTENT_W = W - 2 * MARGIN  # 936


# ---------------------------------------------------------------- fonts ----
def find_font(*patterns):
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    raise FileNotFoundError(patterns)


BOLD_PATH = find_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/**/NotoSans-Bold.ttf",
    "/usr/share/fonts/**/LiberationSans-Bold.ttf",
)
REG_PATH = find_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/**/NotoSans-Regular.ttf",
    "/usr/share/fonts/**/LiberationSans-Regular.ttf",
)

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def bold(size):
    return font(BOLD_PATH, size)


def regular(size):
    return font(REG_PATH, size)


# ------------------------------------------------------------ text utils ----
_probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def text_w(text, fnt):
    return _probe.textlength(text, font=fnt)


def wrap(text, fnt, max_w):
    """Greedy word wrap measured with the real font metrics."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if text_w(trial, fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_block(text, path, start, minimum, max_w, max_h, lh_factor=1.18,
              max_lines=None):
    """Shrink the font until the wrapped block fits the box.

    Returns (font, lines, line_height, total_height)."""
    size = start
    while size >= minimum:
        fnt = font(path, size)
        lines = wrap(text, fnt, max_w)
        lh = int(size * lh_factor)
        total = lh * len(lines)
        if total <= max_h and (max_lines is None or len(lines) <= max_lines):
            return fnt, lines, lh, total
        size -= 1
    fnt = font(path, minimum)
    lines = wrap(text, fnt, max_w)
    lh = int(minimum * lh_factor)
    return fnt, lines, lh, lh * len(lines)


def draw_lines(d, x, y, lines, fnt, lh, fill, align="left", box_w=None):
    for line in lines:
        if align == "center":
            lx = x + (box_w - text_w(line, fnt)) / 2
        else:
            lx = x
        d.text((lx, y), line, font=fnt, fill=fill)
        y += lh
    return y


def draw_tracked(d, x, y, text, fnt, fill, tracking=3):
    """Draw letterspaced caps (for kickers); returns the end x."""
    cx = x
    for ch in text:
        d.text((cx, y), ch, font=fnt, fill=fill)
        cx += text_w(ch, fnt) + tracking
    return cx - tracking


def tracked_w(text, fnt, tracking=3):
    return sum(text_w(ch, fnt) for ch in text) + tracking * (len(text) - 1)


REPORT = []


def note(name, box, used_h, lines=None):
    REPORT.append((name, box, used_h, lines))


# ------------------------------------------------------------- pictograms ----
def pic_lead(d, x, y, w, h):
    """Summit skyline with a row of national flags."""
    base = y + h
    # gold sun disc behind the centre flag
    d.ellipse([x + w / 2 - 34, y + 2, x + w / 2 + 34, y + 70], fill=GOLD)
    # skyline silhouette (navy), varied heights
    rng = [0.42, 0.62, 0.34, 0.55, 0.72, 0.4, 0.6, 0.36, 0.5, 0.66, 0.44, 0.58]
    bw = w / len(rng)
    for i, f in enumerate(rng):
        bh = (h - 34) * f
        d.rectangle([x + i * bw + 2, base - 34 - bh, x + (i + 1) * bw - 2, base - 34],
                    fill=NAVY)
    # ground / summit table band
    d.rectangle([x, base - 34, x + w, base - 22], fill=INK)
    d.rectangle([x, base - 12, x + w, base], fill=INK)
    # flag poles with flags
    colors = [RED, NAVY, GOLD, RED, NAVY]
    for i, col in enumerate(colors):
        px = x + w * (0.12 + 0.19 * i)
        top = y + 6 + (14 if i % 2 else 0)
        d.line([px, top, px, base - 34], fill=INK, width=5)
        fw, fh = 66, 40
        d.polygon([(px, top), (px + fw, top + 5), (px + fw - 10, top + fh / 2),
                   (px + fw, top + fh - 5), (px, top + fh)], fill=col,
                  outline=INK)
        d.ellipse([px - 4, top - 6, px + 4, top + 2], fill=INK)


def pic_chip(d, x, y, s):
    """Computer chip: body, inner die, pins, circuit traces."""
    inset = int(s * 0.22)
    body = [x + inset, y + inset, x + s - inset, y + s - inset]
    # circuit traces first (under the body edge)
    for fx, fy, ex, ey, col in [
        (0.30, 0.22, 0.30, 0.04, NAVY), (0.70, 0.22, 0.70, 0.04, RED),
        (0.30, 0.78, 0.30, 0.97, RED), (0.70, 0.78, 0.70, 0.97, NAVY),
        (0.22, 0.50, 0.03, 0.50, NAVY), (0.78, 0.50, 0.97, 0.50, RED),
    ]:
        d.line([x + s * fx, y + s * fy, x + s * ex, y + s * ey], fill=col, width=4)
        r = 5
        d.ellipse([x + s * ex - r, y + s * ey - r, x + s * ex + r, y + s * ey + r],
                  fill=col)
    d.rounded_rectangle(body, radius=10, fill=INK)
    die = [x + s * 0.36, y + s * 0.36, x + s * 0.64, y + s * 0.64]
    d.rounded_rectangle(die, radius=6, outline=GOLD, width=5)
    # pins on all four sides
    for f in (0.34, 0.5, 0.66):
        p = int(s * f)
        d.line([x + p, y + inset - 12, x + p, y + inset], fill=INK, width=5)
        d.line([x + p, y + s - inset, x + p, y + s - inset + 12], fill=INK, width=5)
        d.line([x + inset - 12, y + p, x + inset, y + p], fill=INK, width=5)
        d.line([x + s - inset, y + p, x + s - inset + 12, y + p], fill=INK, width=5)


def pic_chart(d, x, y, s):
    """Plunging stock chart: axes, gold gridlines, jagged red fall + arrow."""
    left, top = x + 10, y + 6
    right, bot = x + s - 4, y + s - 10
    for gy in (0.32, 0.58, 0.84):
        yy = y + s * gy
        d.line([left, yy, right, yy], fill=GOLD, width=2)
    d.line([left, top, left, bot], fill=INK, width=5)
    d.line([left, bot, right, bot], fill=INK, width=5)
    pts = [(0.06, 0.18), (0.26, 0.10), (0.40, 0.34), (0.55, 0.26),
           (0.70, 0.52), (0.84, 0.62), (0.97, 0.88)]
    abs_pts = [(x + s * a, y + s * b) for a, b in pts]
    d.line(abs_pts, fill=RED, width=7, joint="curve")
    # arrowhead along the last segment direction
    (x1, y1), (x2, y2) = abs_pts[-2], abs_pts[-1]
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L, Wd = 22, 11
    tip = (x2 + 8 * math.cos(ang), y2 + 8 * math.sin(ang))
    b1 = (x2 - L * math.cos(ang) + Wd * math.sin(ang),
          y2 - L * math.sin(ang) - Wd * math.cos(ang))
    b2 = (x2 - L * math.cos(ang) - Wd * math.sin(ang),
          y2 - L * math.sin(ang) + Wd * math.cos(ang))
    d.polygon([tip, b1, b2], fill=RED)


def pic_plane(d, x, y, s):
    """Transport plane nose-down over mountains, smoke trail behind it."""
    # mountains
    d.polygon([(x, y + s), (x + s * 0.38, y + s * 0.58), (x + s * 0.62, y + s)],
              fill=NAVY)
    d.polygon([(x + s * 0.42, y + s), (x + s * 0.78, y + s * 0.66),
               (x + s * 1.0, y + s)], fill=INK)
    # smoke trail: puffs trailing up-left behind the tail, growing as they age
    for i in range(6):
        t = i / 5.0
        cx = x + s * (0.15 - 0.09 * t)
        cy = y + s * (0.22 - 0.15 * t)
        r = 3 + 5 * t
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SMOKE)
    # plane silhouette drawn on its own layer, rotated nose-down, then
    # scaled to fit inside the pictogram box
    layer = Image.new("RGBA", (220, 160), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ink = INK + (255,)
    ld.polygon([(14, 66), (66, 50), (168, 46), (204, 58), (208, 68),
                (206, 76), (164, 82), (70, 86), (26, 82)], fill=ink)  # fuselage
    ld.polygon([(20, 64), (34, 26), (56, 28), (48, 58)], fill=ink)     # tail fin
    ld.polygon([(96, 80), (132, 80), (116, 118), (88, 112)], fill=ink)  # wing
    ld.polygon([(176, 80), (196, 80), (192, 98), (178, 94)], fill=ink)  # tailplane
    layer = layer.rotate(-28, expand=True, resample=Image.BICUBIC)
    scale = (s * 1.0) / layer.width
    layer = layer.resize((int(layer.width * scale), int(layer.height * scale)),
                         resample=Image.LANCZOS)
    d._image.paste(layer, (int(x), int(y)), layer)


def pic_justice(d, x, y, s):
    """Courthouse pillars with pediment, steps, and a gavel."""
    cx = x + s / 2
    # pediment
    d.polygon([(x + 6, y + s * 0.30), (x + s - 6, y + s * 0.30),
               (cx, y + s * 0.06)], fill=NAVY)
    d.rectangle([x + 10, y + s * 0.33, x + s - 10, y + s * 0.38], fill=NAVY)
    # pillars
    pw = s * 0.11
    for f in (0.18, 0.40, 0.62, 0.84):
        px = x + s * f - pw / 2
        d.rectangle([px, y + s * 0.42, px + pw, y + s * 0.78], fill=INK)
    d.rectangle([x + 10, y + s * 0.80, x + s - 10, y + s * 0.85], fill=NAVY)
    # steps
    d.rectangle([x + 4, y + s * 0.88, x + s - 4, y + s * 0.92], fill=INK)
    d.rectangle([x, y + s * 0.95, x + s, y + s * 0.99], fill=INK)
    # gavel on its own layer, angled across the lower right
    layer = Image.new("RGBA", (150, 110), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ink = INK + (255,)
    red = RED + (255,)
    ld.rounded_rectangle([8, 8, 74, 36], radius=8, fill=red)       # head
    ld.rectangle([0, 14, 12, 30], fill=red)
    ld.rectangle([66, 14, 80, 30], fill=red)
    ld.line([44, 30, 104, 92], fill=ink, width=11)                  # handle
    layer = layer.rotate(18, expand=True, resample=Image.BICUBIC)
    scale = 80 / layer.width
    layer = layer.resize((80, int(layer.height * scale)),
                         resample=Image.LANCZOS)
    d._image.paste(layer, (int(x + s * 0.28), int(y + s * 0.58)), layer)


def pic_drone(d, x, y, s):
    """Quadcopter drone: X-frame arms, four rotor discs, camera eye."""
    cx, cy = x + s / 2, y + s / 2
    hubs = [(x + s * 0.20, y + s * 0.20), (x + s * 0.80, y + s * 0.20),
            (x + s * 0.20, y + s * 0.80), (x + s * 0.80, y + s * 0.80)]
    # arms
    for hx, hy in hubs:
        d.line([cx, cy, hx, hy], fill=INK, width=6)
    # rotor discs (blurred blades) with red hubs
    rw, rh = s * 0.20, s * 0.075
    for hx, hy in hubs:
        d.ellipse([hx - rw, hy - rh, hx + rw, hy + rh], outline=INK, width=4)
        d.ellipse([hx - 5, hy - 5, hx + 5, hy + 5], fill=RED)
    # body
    bw, bh = s * 0.34, s * 0.26
    d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2],
                        radius=10, fill=INK)
    # camera eye slung underneath
    d.ellipse([cx - 9, cy + bh / 2 - 2, cx + 9, cy + bh / 2 + 16], fill=GOLD,
              outline=INK, width=3)
    d.ellipse([cx - 3, cy + bh / 2 + 4, cx + 3, cy + bh / 2 + 10], fill=INK)


def pic_ballot(d, x, y, s):
    """Ballot paper with a bold check sliding into a ballot box."""
    import math
    box_top = y + s * 0.56
    # ballot paper first (the box overlaps its foot, so it reads as inserted)
    px0, py0 = x + s * 0.30, y + s * 0.04
    px1, py1 = x + s * 0.70, box_top + 6
    d.rectangle([px0, py0, px1, py1], fill=WHITE, outline=INK, width=4)
    # bold red check on the paper
    d.line([px0 + 9, py0 + (py1 - py0) * 0.46, px0 + (px1 - px0) * 0.40,
            py1 - 12], fill=RED, width=7)
    d.line([px0 + (px1 - px0) * 0.40, py1 - 12, px1 - 8, py0 + 12],
           fill=RED, width=7)
    # ballot box body
    d.polygon([(x + s * 0.14, box_top), (x + s * 0.86, box_top),
               (x + s * 0.79, y + s * 0.97), (x + s * 0.21, y + s * 0.97)],
              fill=NAVY)
    # slot lip across the paper's foot
    d.rectangle([x + s * 0.34, box_top - 2, x + s * 0.66, box_top + 4],
                fill=INK)
    # gold star on the box front
    scx, scy, r_out, r_in = x + s * 0.5, y + s * 0.79, s * 0.11, s * 0.045
    star = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = -math.pi / 2 + i * math.pi / 5
        star.append((scx + r * math.cos(a), scy + r * math.sin(a)))
    d.polygon(star, fill=GOLD)


# ----------------------------------------------------------------- layout ----
def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead ----
    f_title, t_lines, t_lh, t_h = fit_block(
        "THE WORLD IN ONE IMAGE", BOLD_PATH, 68, 40, CONTENT_W, 90,
        lh_factor=1.0, max_lines=1)
    draw_lines(d, MARGIN, 30, t_lines, f_title, t_lh, INK,
               align="center", box_w=CONTENT_W)
    note("masthead title", (MARGIN, 30, CONTENT_W, 90), t_h, t_lines)

    date_f = regular(24)
    date_txt = "WEDNESDAY · 18 NOVEMBER 2026"
    draw_lines(d, MARGIN, 126, [date_txt], date_f, 30, NAVY,
               align="center", box_w=CONTENT_W)
    # thin double rules
    d.rectangle([MARGIN, 164, W - MARGIN, 169], fill=INK)
    d.rectangle([MARGIN, 174, W - MARGIN, 176], fill=INK)

    # ---- lead panel (172..540) ----
    lead_top, lead_bot = 184, 540
    draw_tracked(d, MARGIN, lead_top, "DIPLOMACY", bold(16), RED, tracking=4)
    pic_lead(d, MARGIN, lead_top + 28, CONTENT_W, 148)
    hy = lead_top + 28 + 148 + 12
    f_h, h_lines, h_lh, h_h = fit_block(
        "WORLD LEADERS CONVERGE ON MANILA", BOLD_PATH, 46, 34, CONTENT_W,
        lead_bot - hy - 96, lh_factor=1.14, max_lines=2)
    draw_lines(d, MARGIN, hy, h_lines, f_h, h_lh, INK)
    note("lead headline", (MARGIN, hy, CONTENT_W, lead_bot - hy - 96), h_h,
         h_lines)
    cy = hy + h_h + 8
    f_c, c_lines, c_lh, c_h = fit_block(
        "Trump and Modi headline the ASEAN and Quad summits — new maritime "
        "drills and AI pacts — days before Trump's China trip and the "
        "Shenzhen summit.",
        REG_PATH, 23, 18, CONTENT_W, lead_bot - cy, lh_factor=1.3, max_lines=3)
    draw_lines(d, MARGIN, cy, c_lines, f_c, c_lh, INK)
    note("lead caption", (MARGIN, cy, CONTENT_W, lead_bot - cy), c_h, c_lines)

    # rule under lead
    d.rectangle([MARGIN, 552, W - MARGIN, 554], fill=INK)

    # ---- 2x2 grid (566..922) ----
    grid_top, grid_bot = 566, 922
    row_h = (grid_bot - grid_top - 12) // 2  # 172, gap 12 with rule
    col_w = (CONTENT_W - 28) // 2            # 454, gutter 28
    col_x = [MARGIN, MARGIN + col_w + 28]
    row_y = [grid_top, grid_top + row_h + 12]
    # vertical rule between columns
    d.line([W // 2, grid_top + 4, W // 2, grid_bot - 4], fill=INK, width=2)
    # horizontal rule between rows
    d.rectangle([MARGIN, grid_top + row_h + 5, W - MARGIN,
                 grid_top + row_h + 7], fill=INK)

    panels = [
        ("TECH", pic_chip,
         "NVIDIA BEATS EARNINGS WITHOUT HUANG",
         "The chip giant tops estimates in its first report since Jensen "
         "Huang's exit — and its board bars his return."),
        ("MARKETS", pic_chart,
         "DOW PLUNGES 1,000 POINTS",
         "A tech selloff slams Wall Street — the Dow closes down 849 — and "
         "gold sinks too, down $122 to $3,728: no safe-haven bid."),
        ("WAR", pic_drone,
         "IRAN STRIKES U.S. BASES IN THE GULF",
         "Drones hit the Ali Al Salem base in Kuwait and sites in Bahrain, "
         "answering a U.S. strike on Qeshm Island; all are intercepted."),
        ("ELECTION", pic_ballot,
         "DEMOCRATS TAKE THE SENATE, 56–44",
         "Mary Peltola beats Dan Sullivan in the last race to be called — "
         "the ninth flip, a first Alaska Native senator, and the biggest "
         "majority since 2009."),
    ]

    for idx, (kicker, pic, headline, caption) in enumerate(panels):
        px = col_x[idx % 2]
        py = row_y[idx // 2]
        draw_tracked(d, px, py, kicker, bold(14), RED, tracking=4)
        content_top = py + 24
        avail_h = (py + row_h) - content_top
        # pictogram on the left, text on the right
        pic(d, px, content_top + (avail_h - 124) // 2, 124)
        tx = px + 138
        tw = col_w - 138
        # headline gets up to ~55% of the height, caption the rest
        f_h, h_lines, h_lh, h_h = fit_block(
            headline, BOLD_PATH, 28, 20, tw, int(avail_h * 0.56),
            lh_factor=1.16, max_lines=3)
        draw_lines(d, tx, content_top, h_lines, f_h, h_lh, INK)
        note(f"panel {kicker} headline", (tx, content_top, tw,
             int(avail_h * 0.56)), h_h, h_lines)
        cap_y = content_top + h_h + 6
        f_c, c_lines, c_lh, c_h = fit_block(
            caption, REG_PATH, 19, 15, tw, (py + row_h) - cap_y,
            lh_factor=1.26, max_lines=5)
        draw_lines(d, tx, cap_y, c_lines, f_c, c_lh, INK)
        note(f"panel {kicker} caption", (tx, cap_y, tw, (py + row_h) - cap_y),
             c_h, c_lines)

    # ---- footer band (934..1024) ----
    d.rectangle([0, 934, W, H], fill=NAVY)
    footer = ("ALSO TODAY · Dhoni retires from the IPL to mentor Chennai · "
              "The U.S. loses its measles-free status · Bangladesh switches "
              "on its first nuclear power plant")
    f_f, f_lines, f_lh, f_h = fit_block(
        footer, REG_PATH, 20, 16, CONTENT_W, 62, lh_factor=1.3, max_lines=2)
    fy = 934 + (90 - f_h) // 2
    draw_lines(d, MARGIN, fy, f_lines, f_f, f_lh, WHITE)
    note("footer", (MARGIN, 934, CONTENT_W, 90), f_h, f_lines)

    img.save(OUT, format="PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"saved {OUT}: {img.size[0]}x{img.size[1]}, {size} bytes")
    print("--- layout measurements (box -> used) ---")
    for name, (bx, by, bw, bh), used, lines in REPORT:
        flag = "OK " if used <= bh else "OVERFLOW"
        print(f"{flag} {name}: box h={bh} used h={used} lines={lines}")


if __name__ == "__main__":
    main()
