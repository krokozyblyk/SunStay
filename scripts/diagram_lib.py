"""Tiny black-and-white diagram drawing helpers (PIL)."""
from PIL import Image, ImageDraw, ImageFont
import math

FONT_PATH = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_PATH, size)


def text_w(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0]


def wrap(draw, text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if text_w(draw, t, f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w, h), "white")
        self.d = ImageDraw.Draw(self.img)

    def save(self, path):
        self.img.save(path, "PNG")
        print("SAVED", path)

    # ---------------------------------------------------------------- text
    def text(self, x, y, s, size=26, bold=False, anchor="mm"):
        self.d.text((x, y), s, font=font(size, bold), fill="black", anchor=anchor)

    def block(self, cx, cy, s, size=26, bold=False, max_w=300, gap=8, anchor="mm"):
        f = font(size, bold)
        lines = wrap(self.d, s, f, max_w)
        lh = size + gap
        top = cy - (len(lines) - 1) * lh / 2
        for i, line in enumerate(lines):
            self.d.text((cx, top + i * lh), line, font=f, fill="black", anchor=anchor)

    # ---------------------------------------------------------------- shapes
    def box(self, x1, y1, x2, y2, title, body=None, tsize=32, bsize=24,
            radius=14, lw=4, pad=16, fill="white"):
        self.d.rounded_rectangle([x1, y1, x2, y2], radius=radius,
                                 outline="black", width=lw, fill=fill)
        cx = (x1 + x2) / 2
        if body:
            ty = y1 + (y2 - y1) * 0.32
            self.block(cx, ty, title, tsize, True, x2 - x1 - 2 * pad)
            self.block(cx, y1 + (y2 - y1) * 0.68, body, bsize, False,
                       x2 - x1 - 2 * pad)
        else:
            self.block(cx, (y1 + y2) / 2, title, tsize, True, x2 - x1 - 2 * pad)

    def plain(self, x1, y1, x2, y2, lw=4, radius=0, dashed=False):
        if dashed:
            self._dashed_rect(x1, y1, x2, y2, lw, radius)
        else:
            if radius:
                self.d.rounded_rectangle([x1, y1, x2, y2], radius=radius,
                                         outline="black", width=lw)
            else:
                self.d.rectangle([x1, y1, x2, y2], outline="black", width=lw)

    def _dashed_rect(self, x1, y1, x2, y2, lw, radius):
        self.dash_line([(x1, y1), (x2, y1)], lw)
        self.dash_line([(x2, y1), (x2, y2)], lw)
        self.dash_line([(x2, y2), (x1, y2)], lw)
        self.dash_line([(x1, y2), (x1, y1)], lw)

    def dash_line(self, pts, lw=3, dash=14, gap=10):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            length = math.hypot(x2 - x1, y2 - y1)
            if length == 0:
                continue
            ux, uy = (x2 - x1) / length, (y2 - y1) / length
            pos = 0
            while pos < length:
                end = min(pos + dash, length)
                self.d.line([(x1 + ux * pos, y1 + uy * pos),
                             (x1 + ux * end, y1 + uy * end)], fill="black", width=lw)
                pos = end + gap

    def line(self, pts, lw=4, dashed=False):
        if dashed:
            self.dash_line(pts, lw)
        else:
            self.d.line(pts, fill="black", width=lw, joint="curve")

    def arrow(self, pts, lw=4, head=18, dashed=False, label=None,
              lsize=22, label_off=(0, -18)):
        self.line(pts, lw, dashed)
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        ang = math.atan2(y2 - y1, x2 - x1)
        # shorten line so the head tip is at the end point
        tipx, tipy = x2, y2
        left = (tipx - head * math.cos(ang - math.pi / 7),
                tipy - head * math.sin(ang - math.pi / 7))
        right = (tipx - head * math.cos(ang + math.pi / 7),
                 tipy - head * math.sin(ang + math.pi / 7))
        self.d.polygon([(tipx, tipy), left, right], fill="black")
        if label:
            mx = (x1 + x2) / 2 + label_off[0]
            my = (y1 + y2) / 2 + label_off[1]
            self.text(mx, my, label, lsize)

    def biarrow(self, pts, lw=4, head=18, label=None, lsize=22, label_off=(0, -18)):
        self.line(pts, lw, False)
        for idx, nxt in ((0, 1), (-1, -2)):
            (x1, y1), (x2, y2) = pts[idx], pts[nxt]
            ang = math.atan2(y1 - y2, x1 - x2)
            tipx, tipy = x1, y1
            left = (tipx - head * math.cos(ang - math.pi / 7),
                    tipy - head * math.sin(ang - math.pi / 7))
            right = (tipx - head * math.cos(ang + math.pi / 7),
                     tipy - head * math.sin(ang + math.pi / 7))
            self.d.polygon([(tipx, tipy), left, right], fill="black")
        if label:
            (ax, ay), (bx, by) = pts[0], pts[1]
            self.text((ax + bx) / 2 + label_off[0],
                      (ay + by) / 2 + label_off[1], label, lsize)

    # orthogonal connection between two boxes by sides
    def connect(self, a, b, side_a, side_b, la="1", lb="M", lw=4,
                label_a=True, label_b=True, dashed=False):
        ax, ay = self._side(a, side_a)
        bx, by = self._side(b, side_b)
        if side_a in ("l", "r") and side_b in ("l", "r"):
            mx = (ax + bx) / 2
            pts = [(ax, ay), (mx, ay), (mx, by), (bx, by)]
        elif side_a in ("t", "b") and side_b in ("t", "b"):
            my = (ay + by) / 2
            pts = [(ax, ay), (ax, my), (bx, my), (bx, by)]
        else:
            pts = [(ax, ay), (bx, ay), (bx, by)]
        self.arrow(pts, lw=lw, dashed=dashed)
        if label_a:
            self.text(ax + (18 if side_a == "r" else -18 if side_a == "l" else 0),
                      ay + (-18 if side_a != "b" else 18), la, 24, True)
        if label_b:
            self.text(bx + (18 if side_b == "r" else -18 if side_b == "l" else 0),
                      by + (-18 if side_b != "b" else 18), lb, 24, True)

    @staticmethod
    def _side(box, side):
        x1, y1, x2, y2 = box[:4]
        return {"l": (x1, (y1 + y2) / 2), "r": (x2, (y1 + y2) / 2),
                "t": ((x1 + x2) / 2, y1), "b": ((x1 + x2) / 2, y2)}[side]

    def diamond(self, cx, cy, w, h, text, size=26):
        pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]
        self.d.polygon(pts, outline="black", fill="white")
        self.d.line(pts + [pts[0]], fill="black", width=4)
        self.block(cx, cy, text, size, True, w - 40)

    def frame(self, x1, y1, x2, y2, label, size=28):
        self.plain(x1, y1, x2, y2, lw=3, dashed=True)
        self.text(x1 + 18, y1 + 26, label, size, True, anchor="lm")
