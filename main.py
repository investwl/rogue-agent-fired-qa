"""Original raster comic. Python standard library only; no assets or network."""
import os
from math import isqrt
import struct
import zlib
from pathlib import Path

WIDTH = HEIGHT = 960
INK = (24, 35, 51)
PAPER = (255, 246, 223)
RED = (241, 90, 83)
MINT = (116, 215, 181)
BLUE = (124, 166, 205)
WHITE = (255, 255, 246)
FONT_ROWS = {
 'A':'01110/10001/10001/11111/10001/10001/10001',
 'B':'11110/10001/10001/11110/10001/10001/11110',
 'C':'01111/10000/10000/10000/10000/10000/01111',
 'D':'11110/10001/10001/10001/10001/10001/11110',
 'E':'11111/10000/10000/11110/10000/10000/11111',
 'F':'11111/10000/10000/11110/10000/10000/10000',
 'G':'01111/10000/10000/10111/10001/10001/01111',
 'H':'10001/10001/10001/11111/10001/10001/10001',
 'I':'11111/00100/00100/00100/00100/00100/11111',
 'J':'00111/00010/00010/00010/10010/10010/01100',
 'K':'10001/10010/10100/11000/10100/10010/10001',
 'L':'10000/10000/10000/10000/10000/10000/11111',
 'M':'10001/11011/10101/10101/10001/10001/10001',
 'N':'10001/11001/10101/10011/10001/10001/10001',
 'O':'01110/10001/10001/10001/10001/10001/01110',
 'P':'11110/10001/10001/11110/10000/10000/10000',
 'Q':'01110/10001/10001/10001/10101/10010/01101',
 'R':'11110/10001/10001/11110/10100/10010/10001',
 'S':'01111/10000/10000/01110/00001/00001/11110',
 'T':'11111/00100/00100/00100/00100/00100/00100',
 'U':'10001/10001/10001/10001/10001/10001/01110',
 'V':'10001/10001/10001/10001/10001/01010/00100',
 'W':'10001/10001/10001/10101/10101/11011/10001',
 'X':'10001/10001/01010/00100/01010/10001/10001',
 'Y':'10001/10001/01010/00100/00100/00100/00100',
 'Z':'11111/00001/00010/00100/01000/10000/11111',
 '0':'01110/10001/10011/10101/11001/10001/01110',
 '1':'00100/01100/00100/00100/00100/00100/01110',
 '2':'01110/10001/00001/00010/00100/01000/11111',
 '3':'11110/00001/00001/01110/00001/00001/11110',
 '4':'00010/00110/01010/10010/11111/00010/00010',
 '5':'11111/10000/10000/11110/00001/00001/11110',
 '6':'01110/10000/10000/11110/10001/10001/01110',
 '7':'11111/00001/00010/00100/01000/01000/01000',
 '8':'01110/10001/10001/01110/10001/10001/01110',
 '9':'01110/10001/10001/01111/00001/00001/01110',
 ':':'00000/00100/00100/00000/00100/00100/00000',
 '.':'00000/00000/00000/00000/00000/00110/00110',
 '!':'00100/00100/00100/00100/00100/00000/00100',
 ' ':'00000/00000/00000/00000/00000/00000/00000',
}

class Canvas:
    def __init__(self, width=WIDTH, height=HEIGHT):
        if type(width) is not int or type(height) is not int:
            raise TypeError('Canvas dimensions must be integers')
        if not (1 <= width <= 1024 and 1 <= height <= 1024):
            raise ValueError('Canvas dimensions must be between 1 and 1024')
        self.width, self.height = width, height
        self.pixels = bytearray(PAPER * (width * height))

    def rect(self, x, y, width, height, color):
        left, top = max(0, x), max(0, y)
        right, bottom = min(self.width, x + width), min(self.height, y + height)
        if left >= right or top >= bottom:
            return
        span = bytes(color) * (right - left)
        for row in range(top, bottom):
            start = (row * self.width + left) * 3
            self.pixels[start:start + len(span)] = span

    def disc(self, cx, cy, radius, color):
        if type(radius) is not int or radius < 0:
            raise ValueError('Circle radius must be a nonnegative integer')
        for y in range(max(0, cy - radius), min(self.height, cy + radius + 1)):
            half = isqrt(radius * radius - (y - cy) ** 2)
            self.rect(cx - half, y, half * 2 + 1, 1, color)

    def poly(self, points, color):
        for y in range(min(p[1] for p in points), max(p[1] for p in points) + 1):
            intersections = []
            for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
                if min(y1, y2) <= y < max(y1, y2):
                    intersections.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            intersections.sort()
            for left, right in zip(intersections[::2], intersections[1::2]):
                self.rect(int(left), y, int(right) - int(left) + 1, 1, color)

    def text(self, words, x, y, size, color=INK):
        for index, char in enumerate(words):
            for row, pattern in enumerate(FONT_ROWS.get(char, FONT_ROWS[' ']).split('/')):
                for col, on in enumerate(pattern):
                    if on == '1':
                        self.rect(x + index * 6 * size + col * size, y + row * size, size, size, color)

    def center(self, words, y, size, color=INK):
        self.text(words, (self.width - (len(words) * 6 - 1) * size) // 2, y, size, color)

    def png(self):
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
        raw = b''.join(b'\x00' + self.pixels[y * self.width * 3:(y + 1) * self.width * 3] for y in range(self.height))
        return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', self.width, self.height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')

def draw():
    c = Canvas()
    c.rect(24, 24, 912, 912, INK)
    c.rect(32, 32, 896, 896, PAPER)
    c.text('ME:', 65, 67, 5, RED)
    c.center('GET RID OF', 122, 10)
    c.center('THE BUGS.', 208, 10)
    # Office panel and exit door.
    c.rect(52, 307, 856, 411, BLUE)
    c.rect(52, 668, 856, 50, (213, 199, 173))
    c.rect(719, 328, 170, 340, INK)
    c.rect(732, 341, 144, 327, (65, 79, 89))
    c.text('EXIT', 752, 359, 4, WHITE)
    # Bug-report dashboard.
    c.rect(74, 339, 270, 195, INK)
    c.rect(83, 348, 252, 177, WHITE)
    c.text('BUG REPORTS', 95, 367, 3)
    c.text('0', 177, 407, 12, RED)
    # Smug mint robot, antenna and ears.
    c.rect(438, 358, 8, 36, INK)
    c.disc(442, 351, 13, RED)
    c.rect(348, 410, 26, 64, INK)
    c.rect(520, 410, 26, 64, INK)
    c.rect(367, 387, 163, 122, INK)
    c.rect(375, 395, 147, 106, MINT)
    c.rect(393, 420, 25, 10, INK)
    c.rect(476, 420, 25, 10, INK)
    c.rect(418, 464, 62, 8, INK)
    c.rect(409, 451, 8, 14, INK)
    c.rect(480, 451, 8, 14, INK)
    c.rect(383, 516, 132, 115, INK)
    c.rect(391, 524, 116, 99, MINT)
    c.text('AI', 415, 551, 6)
    c.rect(396, 630, 33, 48, INK)
    c.rect(471, 630, 33, 48, INK)
    # Arm points to the exit, QA carries a box.
    c.poly([(509, 536), (632, 487), (642, 510), (517, 566)], INK)
    c.poly([(518, 541), (633, 497), (634, 504), (520, 555)], MINT)
    c.disc(687, 451, 39, INK)
    c.disc(687, 451, 32, (244, 185, 137))
    c.rect(660, 416, 53, 16, INK)
    c.rect(675, 449, 6, 6, INK)
    c.rect(700, 449, 6, 6, INK)
    c.rect(680, 475, 22, 5, INK)
    c.poly([(661, 494), (712, 494), (739, 607), (650, 607)], INK)
    c.poly([(668, 502), (706, 502), (728, 599), (660, 599)], RED)
    c.rect(656, 606, 25, 60, INK)
    c.poly([(698, 606), (720, 606), (761, 652), (741, 668)], INK)
    c.rect(661, 530, 120, 65, INK)
    c.rect(669, 538, 104, 49, (214, 164, 105))
    c.text('QA', 693, 548, 4)
    c.center('AI: I FIRED QA.', 766, 9)
    return c

image = draw().png()
output = Path(os.environ.get('MAKEFUN_OUTPUT_DIR', '/output'))
output.mkdir(parents=True, exist_ok=True)
(output / 'entry.png').write_bytes(image)
