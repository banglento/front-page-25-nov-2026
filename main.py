#!/usr/bin/env python3
"""Front page of one day's world news: Wednesday 25 November 2026.

Draws a 1024x1024 newspaper front page with a self-written 5x7 bitmap
font, procedural illustrations, and a hand-rolled PNG encoder.
Standard library only, no network, fully deterministic.
"""
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 242, 231)
INK = (17, 17, 17)
RED = (176, 32, 32)
BLUE = (31, 78, 121)
DARKBLUE = (24, 52, 86)
ORANGE = (214, 105, 30)
YELLOW = (232, 178, 44)
GREY = (120, 120, 116)
LIGHTGREY = (200, 196, 186)
PURPLE = (106, 63, 160)
BROWN = (122, 74, 30)
GREEN = (46, 110, 60)
SKY = (178, 208, 228)
SEA = (46, 110, 158)

# ---------------------------------------------------------------- PNG encoder
def png_bytes(w, h, rgb):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.hline(cx - dx, yy, 2 * dx + 1, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            t = 1.0 - ((yy - cy) / ry) ** 2
            dx = int(rx * (t ** 0.5)) if t > 0 else 0
            self.hline(cx - dx, yy, 2 * dx + 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - t <= d <= r:
                    self.set(xx, yy, c)

    def polygon(self, pts, c):
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), yy, max(1, int(xs[i + 1]) - int(xs[i])), c)

    def star(self, cx, cy, r_out, r_in, points, c):
        import math
        pts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.pi * i / points - math.pi / 2
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        self.polygon(pts, c)


# --------------------------------------------------------------------- font
# 5x7 bitmap font, uppercase + digits + punctuation.
FONT = {
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    ",": ("     ", "     ", "     ", "     ", "     ", " ##  ", " #   "),
    ".": ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    "'": (" #   ", " #   ", "  #  ", "     ", "     ", "     ", "     "),
    "-": ("     ", "     ", "     ", " ####", "     ", "     ", "     "),
    ":": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    "!": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    "&": (" ##  ", "#  # ", "# #  ", " #   ", "# # #", "#  # ", " ## #"),
    "/": ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    "(": ("   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "),
    ")": (" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "),
    "%": ("#   #", "#  # ", "   # ", "  #  ", " #   ", "#  # ", "#   #"),
    "+": ("     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "),
    "=": ("     ", "     ", "#####", "     ", "#####", "     ", "     "),
    "~": ("     ", "     ", " ## #", "# ## ", "     ", "     ", "     "),
    "*": ("     ", " # # ", "  #  ", "#####", "  #  ", " # # ", "     "),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    for ch in s:
        glyph = FONT.get(ch.upper(), FONT[" "])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "#":
                    cv.fill_rect(x + col * scale, y + row * scale,
                                 scale, scale, color)
        x += 6 * scale
    return x


def draw_text_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_width(s, scale) // 2, y, s, scale, color)


def draw_wrapped(cv, x, y, max_w, text, scale, color, gap=4):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for ln in lines:
        draw_text(cv, x, y, ln, scale, color)
        y += 7 * scale + gap
    return y


def panel(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, PAPER)
    cv.fill_rect(x, y, w, 2, INK)
    cv.fill_rect(x, y + h - 2, w, 2, INK)
    cv.fill_rect(x, y, 2, h, INK)
    cv.fill_rect(x + w - 2, y, 2, h, INK)


def kicker(cv, x, y, s, color=RED):
    draw_text(cv, x, y, s, 2, color)


# ------------------------------------------------------------- illustrations
def draw_ship_scene(cv, x, y, w, h):
    """Cargo ship at sea, drone above, explosion burst."""
    cv.fill_rect(x, y, w, h, SKY)
    sea_y = y + h - 46
    cv.fill_rect(x, sea_y, w, h - (sea_y - y), SEA)
    # waves
    for i in range(0, w, 26):
        cv.hline(x + i, sea_y + 10, 16, (255, 255, 255))
        cv.hline(x + i + 8, sea_y + 26, 14, (200, 220, 240))
    # ship hull
    hx, hy = x + 30, sea_y - 26
    cv.polygon([(hx, hy), (hx + 220, hy), (hx + 196, hy + 26),
                (hx + 14, hy + 26)], (60, 60, 66))
    cv.fill_rect(hx + 8, hy - 22, 150, 22, (96, 96, 100))  # deck cargo
    cv.fill_rect(hx + 26, hy - 16, 34, 12, RED)
    cv.fill_rect(hx + 76, hy - 16, 34, 12, YELLOW)
    cv.fill_rect(hx + 126, hy - 16, 34, 12, BLUE)
    cv.fill_rect(hx + 168, hy - 34, 14, 34, INK)  # funnel
    cv.fill_rect(hx + 164, hy - 40, 22, 6, RED)
    cv.vline(hx + 200, hy - 46, 46, INK, 3)  # mast
    # drone
    dx, dy = x + w - 96, y + 34
    cv.fill_rect(dx - 10, dy - 4, 20, 8, INK)
    cv.hline(dx - 18, dy - 8, 36, INK, 2)
    cv.hline(dx - 18, dy + 6, 36, INK, 2)
    cv.circle(dx - 16, dy - 8, 3, GREY)
    cv.circle(dx + 16, dy - 8, 3, GREY)
    cv.circle(dx - 16, dy + 6, 3, GREY)
    cv.circle(dx + 16, dy + 6, 3, GREY)
    # explosion burst over the ship
    ex, ey = hx + 120, hy - 44
    cv.star(ex, ey, 34, 14, 8, ORANGE)
    cv.star(ex, ey, 20, 9, 8, YELLOW)
    cv.circle(ex, ey, 7, RED)


def draw_cop_scene(cv, x, y, w, h):
    """Summit hall under a hot sun, flags, no deal. Fits a short box."""
    import math
    cv.fill_rect(x, y, w, h, SKY)
    # sun
    sx, sy = x + w - 44, y + 18
    cv.circle(sx, sy, 11, YELLOW)
    for i in range(6):
        a = math.pi * i / 3
        cv.line(int(sx + 14 * math.cos(a)), int(sy + 14 * math.sin(a)),
                int(sx + 20 * math.cos(a)), int(sy + 20 * math.sin(a)),
                ORANGE, 2)
    # hall
    bx, by = x + 20, y + h - 30
    cv.fill_rect(bx, by, 170, 30, (240, 234, 220))
    cv.polygon([(bx - 8, by), (bx + 85, by - 20), (bx + 178, by)],
               (180, 60, 50))
    for i in range(4):
        cv.fill_rect(bx + 14 + i * 40, by + 6, 8, 22, INK)
    # small flags on the roof line
    for i, fc in enumerate((RED, GREEN, BLUE)):
        fx = bx + 24 + i * 52
        cv.vline(fx, by - 28, 12, INK, 2)
        cv.fill_rect(fx + 2, by - 28, 14, 9, fc)
    # big red X over the hall's right end
    cv.line(x + 236, y + 6, x + 276, y + 46, RED, 5)
    cv.line(x + 276, y + 6, x + 236, y + 46, RED, 5)


def draw_tower_scene(cv, x, y, w, h):
    """Kingdom Centre tower, smoke plume above. Fits a short box."""
    cv.fill_rect(x, y, w, h, SKY)
    tx = x + w // 2 - 28
    top = y + 14
    # tower body with pointed arch opening near the top
    cv.polygon([(tx, y + h - 2), (tx, top + 8), (tx + 56, top + 8),
                (tx + 56, y + h - 2)], (70, 80, 96))
    cv.polygon([(tx + 19, top + 8), (tx + 28, top - 2), (tx + 37, top + 8)],
               SKY)
    for row in range(3):
        for col in range(3):
            cv.fill_rect(tx + 8 + col * 16, top + 16 + row * 10, 9, 6,
                         (220, 220, 200))
    # smoke plume
    cx = x + w // 2
    for (sx, sy, r) in ((cx - 18, y + 9, 7), (cx, y + 4, 8),
                        (cx + 18, y + 9, 7)):
        cv.circle(sx, sy, r, GREY)
    cv.circle(cx, y + 1, 4, (150, 150, 146))
    # ground
    cv.fill_rect(x, y + h - 2, w, 2, INK)


def draw_candles_scene(cv, x, y, w, h):
    """Three candles with flames. Fits a short box."""
    cv.fill_rect(x, y, w, h, (232, 222, 240))
    for i, (cx, cw) in enumerate(((x + 60, 16), (x + w // 2, 20),
                                  (x + w - 60, 16))):
        base = y + h - 6
        cv.fill_rect(cx - cw // 2, base - 34, cw, 34, (250, 248, 244))
        cv.fill_rect(cx - cw // 2, base - 34, cw, 4, PURPLE)
        cv.vline(cx, base - 40, 6, INK, 2)
        cv.ellipse(cx, base - 46, 5, 8, ORANGE)
        cv.ellipse(cx, base - 44, 2, 4, YELLOW)
    cv.fill_rect(x, y + h - 6, w, 3, PURPLE)


def draw_turkey_scene(cv, x, y, w, h):
    """White House columns behind, a turkey in front. Fits a short box."""
    import math
    cv.fill_rect(x, y, w, h, SKY)
    # white house
    hx, hy = x + 16, y + 16
    cv.polygon([(hx, hy + 12), (hx + 70, hy), (hx + 140, hy + 12)], INK)
    cv.fill_rect(hx, hy + 12, 140, 34, (250, 248, 244))
    for i in range(4):
        cv.fill_rect(hx + 10 + i * 34, hy + 18, 8, 26, INK)
    cv.fill_rect(hx, hy + 44, 140, 3, INK)
    # turkey: feather fan + body + head
    tx, ty = x + w - 64, y + h - 4
    for i in range(5):
        a = math.radians(-60 + 30 * i)
        fx = int(tx + 30 * math.sin(a))
        fy = int(ty - 30 * math.cos(a))
        cv.ellipse(fx, fy, 7, 15, (150, 90, 40) if i % 2 else (122, 74, 30))
    cv.ellipse(tx, ty - 10, 20, 14, BROWN)
    cv.circle(tx + 16, ty - 28, 8, BROWN)
    cv.polygon([(tx + 23, ty - 30), (tx + 32, ty - 27), (tx + 23, ty - 24)],
               ORANGE)
    cv.circle(tx + 19, ty - 31, 1, INK)
    # ground
    cv.fill_rect(x, y + h - 2, w, 2, INK)


def draw_plane(cv, x, y, s, color):
    """Simple early-warning jet silhouette, facing right."""
    cv.polygon([(x, y), (x + 46 * s, y), (x + 58 * s, y + 4 * s),
                (x + 46 * s, y + 8 * s), (x, y + 8 * s)], color)
    cv.polygon([(x + 14 * s, y), (x + 26 * s, y - 10 * s),
                (x + 32 * s, y - 10 * s), (x + 26 * s, y)], color)
    cv.polygon([(x + 34 * s, y + 8 * s), (x + 40 * s, y + 16 * s),
                (x + 46 * s, y + 16 * s), (x + 42 * s, y + 8 * s)], color)
    cv.fill_rect(x + 48 * s, y + 1 * s, 8 * s, 6 * s, color)


# ---------------------------------------------------------------------- page
def build():
    cv = Canvas(W, H, PAPER)

    # ---- masthead
    draw_text_centered(cv, W // 2, 30, "THE WORLD TODAY", 9, INK)
    cv.hline(28, 104, W - 56, INK, 4)
    cv.hline(28, 112, W - 56, INK, 1)
    draw_text(cv, 28, 126, "NO. 329", 2, INK)
    draw_text_centered(cv, W // 2, 122, "WEDNESDAY 25 NOVEMBER 2026", 4, RED)
    draw_text(cv, W - 28 - text_width("PRICE: FREE", 2), 126, "PRICE: FREE",
              2, INK)
    cv.hline(28, 164, W - 56, INK, 2)

    # ---- lead story: Ukraine hits Russian ships
    lx, ly, lw, lh = 28, 178, W - 56, 288
    panel(cv, lx, ly, lw, lh)
    kicker(cv, lx + 20, ly + 16, "WAR AT SEA - UKRAINE")
    draw_text(cv, lx + 20, ly + 44, "UKRAINE HITS TWO", 3, INK)
    draw_text(cv, lx + 20, ly + 72, "RUSSIAN SHIPS", 3, INK)
    draw_wrapped(cv, lx + 20, ly + 112, 480,
                 "Kyiv confirms a drone strike on a Russian cargo ship in "
                 "the Gulf of Finland - and the sinking of a Russian warship "
                 "in Benghazi, Libya. Moscow calls it terrorism and vows "
                 "revenge.", 2, INK)
    draw_ship_scene(cv, lx + 530, ly + 16, lw - 550, lh - 32)

    # ---- row 2: COP31 / Riyadh
    ry, rh = 482, 224
    pw = (W - 56 - 16) // 2
    # COP31
    panel(cv, 28, ry, pw, rh)
    kicker(cv, 48, ry + 14, "CLIMATE - ANTALYA")
    draw_text(cv, 48, ry + 40, "COP31 COLLAPSES", 3, INK)
    draw_text(cv, 48, ry + 68, "NO CLIMATE DEAL", 3, INK)
    draw_wrapped(cv, 48, ry + 100, pw - 40,
                 "Summit ends with no final deal as oil and gas producers "
                 "block fossil-fuel phaseout language.", 2, INK)
    draw_cop_scene(cv, 48, ry + 152, pw - 40, 62)
    # Riyadh
    rx = 28 + pw + 16
    panel(cv, rx, ry, pw, rh)
    kicker(cv, rx + 20, ry + 14, "MIDDLE EAST - RIYADH")
    draw_text(cv, rx + 20, ry + 40, "HOUTHIS HIT", 3, INK)
    draw_text(cv, rx + 20, ry + 68, "RIYADH TOWER", 3, INK)
    draw_wrapped(cv, rx + 20, ry + 100, pw - 40,
                 "Kingdom Centre, the capital's tallest tower, is struck; "
                 "11 hurt in the second attack in days.", 2, INK)
    draw_tower_scene(cv, rx + 20, ry + 152, pw - 40, 62)

    # ---- row 3: UN femicide / Trump turkey
    ry3, rh3 = 722, 224
    panel(cv, 28, ry3, pw, rh3)
    kicker(cv, 48, ry3 + 14, "UNITED NATIONS - 25 NOV")
    draw_text(cv, 48, ry3 + 40, "47,000 WOMEN", 3, RED)
    draw_text(cv, 48, ry3 + 68, "KILLED IN A YEAR", 3, INK)
    draw_wrapped(cv, 48, ry3 + 100, pw - 40,
                 "Killed by partners or family - about 5 every hour, the UN "
                 "says, on the day against violence against women.", 2, INK)
    draw_candles_scene(cv, 48, ry3 + 152, pw - 40, 62)
    # Trump
    panel(cv, rx, ry3, pw, rh3)
    kicker(cv, rx + 20, ry3 + 14, "WASHINGTON - THANKSGIVING")
    draw_text(cv, rx + 20, ry3 + 40, "TRUMP PARDONS", 3, INK)
    draw_text(cv, rx + 20, ry3 + 68, "THE TURKEYS", 3, INK)
    draw_wrapped(cv, rx + 20, ry3 + 100, pw - 40,
                 "Freedom and Feathers are spared at the White House; Rudy "
                 "Giuliani gets the Medal of Freedom.", 2, INK)
    draw_turkey_scene(cv, rx + 20, ry3 + 152, pw - 40, 62)

    # ---- bottom strip: NATO / Sigonella
    by = 962
    panel(cv, 28, by, W - 56, 34)
    draw_plane(cv, 44, by + 12, 1, BLUE)
    draw_text(cv, 116, by + 10,
              "ALSO: NATO JETS TO POLAND; US BASE SIGONELLA SHUT AFTER "
              "DRONE SIGHTINGS", 2, INK)

    return png_bytes(W, H, cv.px)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
