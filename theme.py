# -*- coding: utf-8 -*-
"""Retro / synthwave tema: renk paleti, gradyanlar, büyük harf fontu ve neon klavye."""

import math

from rich.text import Text

import layouts

# --- Palet ------------------------------------------------------------------
BG = "#140a24"
PANEL = "#1d1033"
LINE = "#5b2a86"
PINK = "#ff2e97"
CYAN = "#00e5ff"
YELLOW = "#ffd23f"
ORANGE = "#ff8c42"
GREEN = "#39ff88"
RED = "#ff3b5c"
PURPLE = "#b14aed"
DIM = "#8a74a8"
FAINT = "#5d4a7a"
TEXT = "#f3e9ff"

RAINBOW = [PINK, PURPLE, CYAN, PURPLE, PINK]          # döngüsel -> dikişsiz akış
SUNSET = [YELLOW, ORANGE, PINK, PURPLE]


# --- Renk yardımcıları ------------------------------------------------------
def _rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    a, b = _rgb(c1), _rgb(c2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(stops, t):
    """stops listesi üzerinde 0..1 konumundaki rengi verir."""
    t = max(0.0, min(0.9999, t))
    seg = t * (len(stops) - 1)
    i = int(seg)
    return lerp(stops[i], stops[i + 1], seg - i)


def gradient_text(s, stops=RAINBOW, phase=0.0, style=""):
    out = Text()
    n = max(1, len(s) - 1)
    for i, ch in enumerate(s):
        out.append(ch, style=f"{style} {gradient(stops, (i / n + phase) % 1.0)}".strip())
    return out


def chip(key, label, color=PINK):
    """[ KEY ] etiketi: klavye tuşu görünümlü kısayol ipucu."""
    t = Text()
    t.append(f" {key} ", style=f"bold {BG} on {color}")
    t.append(f" {label}  ", style=DIM)
    return t


def hints(items, color=PINK):
    out = Text(justify="center")
    for key, label in items:
        out.append_text(chip(key, label, color))
    return out


# --- Büyük harf fontu (5 satır) --------------------------------------------
FONT = {
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": [" █ ", "██ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
    "K": ["█ █", "█ █", "██ ", "█ █", "█ █"],
    "I": ["███", " █ ", " █ ", " █ ", "███"],
    "V": ["█ █", "█ █", "█ █", "█ █", " █ "],
}


def big(text, stops=RAINBOW, phase=0.0, scale=2):
    """Büyük blok yazı; gradyan çapraz akar (phase zamanla artarsa animasyon olur)."""
    rows = ["" for _ in range(5)]
    for ch in text:
        glyph = FONT.get(ch.upper(), ["   "] * 5)
        for r in range(5):
            rows[r] += "".join(c * scale for c in glyph[r]) + " " * scale
    width = max(len(r) for r in rows)
    out = Text(justify="center")
    for r, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == " ":
                out.append(" ")
            else:
                pos = (x / max(1, width) + r * 0.05 + phase) % 1.0
                out.append(ch, style=gradient(stops, pos))
        if r < 4:
            out.append("\n")
    return out


def wave(width, t):
    """Akan equalizer dalgası (retro ses görselleştirici)."""
    bars = "▁▂▃▄▅▆▇█"
    out = Text(justify="center")
    for x in range(width):
        v = (math.sin(x * 0.28 + t * 3.0) + math.sin(x * 0.11 - t * 1.7) + 2) / 4
        out.append(bars[min(7, int(v * 8))], style=gradient(RAINBOW, (x / width + t * 0.12) % 1.0))
    return out


def smooth_bar(frac, width, t=0.0):
    """Akıcı (kesirli bloklu) gradyan ilerleme çubuğu."""
    parts = " ▏▎▍▌▋▊▉"
    total = frac * width
    full = int(total)
    rest = total - full
    out = Text(justify="center")
    for x in range(width):
        col = gradient([CYAN, PURPLE, PINK], x / max(1, width - 1))
        if x < full:
            out.append("█", style=col)
        elif x == full and full < width:
            out.append(parts[int(rest * 8)], style=f"{col} on {PANEL}")
        else:
            out.append(" ", style=f"on {PANEL}")
    return out


# --- Neon mekanik klavye ----------------------------------------------------
PLATE = "#0e0618"
CAP_FACE, CAP_EDGE, CAP_TEXT = "#2a1744", "#150a26", "#c9a8f5"


def _heat_face(rate):
    return gradient([YELLOW, ORANGE, RED], rate / 35.0)


FINGER_COLORS = [PINK, ORANGE, YELLOW, GREEN, CYAN, "#4d8dff", PURPLE, "#e056fd"]


def finger_legend():
    """Parmak renk açıklaması: ■ serçe ■ yüzük ... (sol -> sağ)"""
    out = Text(justify="center")
    short = ["serçe", "yüzük", "orta", "işaret", "işaret", "orta", "yüzük", "serçe"]
    for i, name in enumerate(short):
        if i == 4:
            out.append("│ ", style=FAINT)
        out.append("■ ", style=FINGER_COLORS[i])
        out.append(name + " ", style=DIM)
    return out


def render_keyboard(lang, t=0.0, nxt=None, wrong=None, heat=None, pressed=None, tall=True,
                    fingers=False, allowed=None):
    """Neon mekanik klavye.

    nxt: sıradaki tuş (pembe-camgöbeği arasında nabız gibi parlar)
    wrong: yanlış basılan tuş
    heat: {harf: hata %} -> ısı haritası
    pressed: {tuş: (basılma_zamanı, doğru_mu)} -> tuşlar basılınca iner ve yavaşça söner
    t: şimdiki zaman (animasyon için)
    fingers: tuşları basılacak parmağa göre renklendirir
    allowed: ders modunda henüz açılmamış (izinli olmayan) harfler soluk çizilir
    """
    pressed = pressed or {}

    def base_look(ch):
        if allowed is not None and ch.isalpha() and ch not in allowed:
            return "#1a0f2b", "#120a20", FAINT                 # kilitli tuş
        if fingers:
            f = layouts.finger_of(lang, ch)
            if f is not None:
                face = lerp(CAP_FACE, FINGER_COLORS[f], 0.42)
                return face, lerp(face, "#000000", 0.55), TEXT
        return CAP_FACE, CAP_EDGE, CAP_TEXT

    def look(ch):
        """(yüz, kenar, yazı, aşağıda_mı)"""
        bface, bedge, btext = base_look(ch)
        if heat is not None:
            rate = heat.get(ch)
            if rate is None:
                return bface, bedge, btext, False
            f = _heat_face(rate)
            return f, lerp(f, "#000000", 0.55), BG, False
        if ch in pressed:
            t0, ok = pressed[ch]
            k = 1.0 - (t - t0) / 0.45
            if k > 0:
                color = GREEN if ok else RED
                face = lerp(bface, color, k)
                return face, face, BG if k > 0.5 else TEXT, k > 0.45
        if ch == wrong:
            return RED, lerp(RED, "#000000", 0.5), TEXT, False
        if ch == nxt:
            glow = (math.sin(t * 5.0) + 1) / 2 * 0.65
            f = lerp(CYAN, PINK, glow)
            return f, lerp(f, "#000000", 0.5), BG, False
        return bface, bedge, btext, False

    rows = []
    for r, row in enumerate(layouts.KEY_ROWS[lang]):
        keys = [(("İ" if (ch == "i" and lang == "tr") else ch.upper()), 5, ch) for ch in row]
        rows.append((layouts.ROW_OFFSET[r] * 2, keys))
    label = "BOŞLUK" if lang == "tr" else "SPACE"
    rows.append((8, [(label.center(25), 25, " ")]))

    out = Text(justify="center")
    for indent, keys in rows:
        lines = [Text(), Text(), Text()] if tall else [Text(), Text()]
        for line in lines:
            line.append(" " * indent, style=f"on {PLATE}")
        for text, w, ch in keys:
            face, edge, fg, down = look(ch)
            if tall:
                top, mid, bot = lines
                if down:
                    top.append(" " * w, style=f"on {PLATE}")
                    mid.append("▄" * w, style=f"{face} on {PLATE}")
                    bot.append(text.center(w), style=f"bold {fg} on {face}")
                else:
                    top.append("▄" * w, style=f"{face} on {PLATE}")
                    mid.append(text.center(w), style=f"bold {fg} on {face}")
                    bot.append("▀" * w, style=f"{edge} on {PLATE}")
            else:
                mid, bot = lines
                if down:
                    mid.append(" " * w, style=f"on {PLATE}")
                    bot.append(text.center(w), style=f"bold {fg} on {face}")
                else:
                    mid.append(text.center(w), style=f"bold {fg} on {face}")
                    bot.append("▀" * w, style=f"{edge} on {PLATE}")
            for line in lines:
                line.append(" ", style=f"on {PLATE}")
        for line in lines:
            out.append_text(line)
            out.append("\n")
    out.rstrip()
    return out
