#!/usr/bin/env python3
"""Render the fuel pump icon (same drawing as www/favicon.svg) to PNG, stdlib only."""
import math, os, struct, zlib

GREEN, WHITE = (11, 122, 92), (255, 255, 255)
WWW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "www")


def rrect(x, y, w, h, r):
    cx, cy, hx, hy = x + w / 2, y + h / 2, w / 2 - r, h / 2 - r
    def sdf(px, py):
        dx, dy = abs(px - cx) - hx, abs(py - cy) - hy
        return math.hypot(max(dx, 0), max(dy, 0)) + min(max(dx, dy), 0) - r
    return sdf


def polyline(points, width):
    segs = list(zip(points, points[1:]))
    def sdf(px, py):
        best = 1e9
        for (ax, ay), (bx, by) in segs:
            vx, vy = bx - ax, by - ay
            t = max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
            best = min(best, math.hypot(px - ax - t * vx, py - ay - t * vy))
        return best - width / 2
    return sdf


def arc(cx, cy, r, a0, a1, n=8):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


hose = [(38, 24), (42.5, 24)] + arc(42.5, 27, 3, -90, 0)[1:] + [(45.5, 42)] + arc(48, 42, 2.5, 180, 0)[1:] + [(50.5, 22), (44.5, 16)]
GLYPH = [
    (rrect(14, 12, 24, 40, 4), WHITE),
    (rrect(18.5, 17, 15, 11, 2), GREEN),
    (rrect(10, 49, 32, 5, 2), WHITE),
    (polyline(hose, 4), WHITE),
]


def render(size, path, rounded=True, glyph_scale=1.0):
    bg = rrect(0, 0, 64, 64, 14 if rounded else 0)
    k = 64 / size
    rows = []
    for j in range(size):
        row = bytearray([0])
        for i in range(size):
            x, y = (i + .5) * k, (j + .5) * k
            alpha = max(0.0, min(1.0, .5 - bg(x, y) / k))
            color = GREEN
            gx, gy = 32 + (x - 32) / glyph_scale, 32 + (y - 32) / glyph_scale
            for sdf, c in GLYPH:
                cov = max(0.0, min(1.0, .5 - sdf(gx, gy) * glyph_scale / k))
                if cov:
                    color = tuple(round(a + (b - a) * cov) for a, b in zip(color, c))
            row += bytes(color) + bytes([round(alpha * 255)])
        rows.append(bytes(row))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    os.chmod(path, 0o644)


render(192, os.path.join(WWW, "icon-192.png"))
render(512, os.path.join(WWW, "icon-512.png"))
render(512, os.path.join(WWW, "icon-maskable-512.png"), rounded=False, glyph_scale=.72)
render(180, os.path.join(WWW, "apple-touch-icon.png"), rounded=False, glyph_scale=.85)
