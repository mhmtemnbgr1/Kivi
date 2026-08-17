# -*- coding: utf-8 -*-
"""Yazma testi motoru: gerçek zamanlı tuş okuma, zamanlayıcı ve canlı ekran.

Windows'ta `msvcrt`, diğer sistemlerde `termios`/`select` kullanır.
"""

import os
import random
import shutil
import sys
import time

import storage

# ANSI renk kodları
RESET = "\033[0m"
GREEN = "\033[32m"
RED = "\033[31m"
GREY = "\033[90m"
CYAN = "\033[36m"
BOLD = "\033[1m"
CURSOR = "\033[7m"       # ters video (imleç bloğu)
HIDE_CUR = "\033[?25l"
SHOW_CUR = "\033[?25h"

IS_WIN = os.name == "nt"


def enable_ansi():
    """ANSI renklerini ve UTF-8 (Türkçe karakter) desteğini etkinleştirir."""
    # Çıktı/giriş akışlarını UTF-8'e sabitle (Türkçe harfler için)
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if IS_WIN:
        try:
            import ctypes
            k = ctypes.windll.kernel32
            # ANSI kaçış dizilerini aç
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
            # Konsol kod sayfasını UTF-8 (65001) yap
            k.SetConsoleOutputCP(65001)
            k.SetConsoleCP(65001)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Tuş okuma
# ---------------------------------------------------------------------------
class KeyReader:
    """Bloklamayan, zaman aşımlı tek tuş okuyucu (Windows + POSIX)."""

    def __enter__(self):
        if not IS_WIN:
            import termios
            import tty
            self._fd = sys.stdin.fileno()
            self._old = termios.tcgetattr(self._fd)
            tty.setraw(self._fd)
        return self

    def __exit__(self, *exc):
        if not IS_WIN:
            import termios
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old)

    def get_key(self, timeout=0.05):
        """timeout saniye içinde bir tuş dönerse onu, yoksa None döndürür."""
        if IS_WIN:
            import msvcrt
            end = time.time() + timeout
            while time.time() < end:
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch in ("\x00", "\xe0"):   # ok/fonksiyon tuşu -> yut
                        msvcrt.getwch()
                        return None
                    return ch
                time.sleep(0.004)
            return None
        else:
            import select
            r, _, _ = select.select([sys.stdin], [], [], timeout)
            if r:
                ch = sys.stdin.read(1)
                if ch == "\x1b":  # ESC dizisi olabilir; kalanını yut
                    r2, _, _ = select.select([sys.stdin], [], [], 0.001)
                    if r2:
                        sys.stdin.read(2)
                        return None
                return ch
            return None


# ---------------------------------------------------------------------------
# Kelime üretimi
# ---------------------------------------------------------------------------
def generate_words(lang, mode, count):
    """Teste uygun kelime akışı üretir.

    mode='normal'  -> temel havuzdan rastgele
    mode='practice'-> yanlış yazılan kelimeler ağırlıklı (bilinmeyenler sık çıkar)
    """
    from words import get_wordlist
    base = get_wordlist(lang)

    if mode != "practice":
        return [random.choice(base) for _ in range(count)]

    pool = storage.mistyped_pool(lang)
    weak = [w for w, _ in weak_letter_set(lang)]
    if not pool and not weak:
        # Henüz veri yok; normal moda düş
        return [random.choice(base) for _ in range(count)]

    words, weights = [], []
    # Yanlış yazılan kelimeler: sayısı kadar ağırlık (çok yanlış = çok sık)
    for w, c in pool:
        words.append(w)
        weights.append(c * 5)
    # Zayıf harf içeren temel kelimeler orta ağırlıkla
    weakset = set(weak)
    for w in base:
        if weakset and any(ch in weakset for ch in w):
            words.append(w)
            weights.append(2)
    # Biraz da genel kelime (çeşitlilik için)
    for w in base:
        words.append(w)
        weights.append(1)

    return random.choices(words, weights=weights, k=count)


def weak_letter_set(lang, top=8):
    return [(r[0], r[1]) for r in storage.weak_letters(lang, top=top, min_total=1)]


# ---------------------------------------------------------------------------
# Ekran çizimi
# ---------------------------------------------------------------------------
def _wrap_indices(words, width):
    """Kelimeleri (indeksleriyle) genişliğe göre satırlara böler."""
    lines, cur, cur_len = [], [], 0
    for i, w in enumerate(words):
        add = len(w) + (1 if cur else 0)
        if cur and cur_len + add > width:
            lines.append(cur)
            cur, cur_len = [], 0
            add = len(w)
        cur.append(i)
        cur_len += add
    if cur:
        lines.append(cur)
    return lines


def _render_word(target, typed, is_current):
    """Bir kelimeyi renkli karakter dizisi olarak üretir."""
    out = []
    n = max(len(target), len(typed))
    for j in range(n):
        tch = target[j] if j < len(target) else ""
        uch = typed[j] if j < len(typed) else None

        if is_current and uch is None and j == len(typed):
            # imlecin bulunduğu (henüz yazılmamış) karakter
            out.append(CURSOR + (tch if tch else " ") + RESET)
        elif uch is None:
            out.append(GREY + tch + RESET)                       # yazılmadı
        elif j >= len(target):
            out.append(RED + uch + RESET)                        # fazladan
        elif uch == tch:
            out.append(GREEN + tch + RESET)                      # doğru
        else:
            out.append(RED + tch + RESET)                        # yanlış
    return "".join(out)


def _draw(frame_lines):
    sys.stdout.write("\033[H" + "\n".join(frame_lines) + "\033[0J")
    sys.stdout.flush()


def _live_stats(target_words, typed_words, elapsed):
    correct_chars = 0
    for i, typed in enumerate(typed_words):
        if i >= len(target_words):
            break
        target = target_words[i]
        for j, tch in enumerate(target):
            if j < len(typed) and typed[j] == tch:
                correct_chars += 1
    minutes = elapsed / 60.0 if elapsed > 0 else 1 / 60.0
    wpm = round((correct_chars / 5.0) / minutes)
    correct_words = sum(1 for i, t in enumerate(typed_words)
                        if i < len(target_words) and t == target_words[i])
    return wpm, correct_words


# ---------------------------------------------------------------------------
# Test döngüsü
# ---------------------------------------------------------------------------
def run_test(lang, duration, mode="normal"):
    """Testi çalıştırır; sonuç özetini döndürür (veya iptal edilirse None)."""
    lang_name = "Türkçe" if lang == "tr" else "İngilizce"
    mode_name = "Alıştırma" if mode == "practice" else "Normal"

    # Süreye göre bolca kelime üret
    count = max(150, int(duration / 60.0 * 220) + 80)
    target_words = generate_words(lang, mode, count)

    width = max(30, min(shutil.get_terminal_size((80, 24)).columns, 100) - 2)
    lines = _wrap_indices(target_words, width)

    # Kelime -> satır eşlemesi (kaydırma için)
    word_line = {}
    for li, idxs in enumerate(lines):
        for wi in idxs:
            word_line[wi] = li

    typed_words = []      # onaylanmış kelimeler
    current = ""          # yazılmakta olan kelime
    word_index = 0
    started = False       # ilk tuşta zamanlayıcı başlar
    start_time = None
    last_render = -1

    sys.stdout.write("\033[2J" + HIDE_CUR)
    try:
        with KeyReader() as reader:
            while True:
                now = time.time()
                if started:
                    elapsed = now - start_time
                    remaining = duration - elapsed
                    if remaining <= 0:
                        break
                else:
                    elapsed = 0.0
                    remaining = duration

                key = reader.get_key(timeout=0.03)
                dirty = False

                if key is not None:
                    if key in ("\x1b",):            # ESC -> iptal
                        sys.stdout.write(SHOW_CUR)
                        return None
                    if key == "\x03":               # Ctrl+C
                        raise KeyboardInterrupt
                    if not started:
                        started = True
                        start_time = time.time()

                    if key in ("\r", "\n", " "):    # kelimeyi onayla
                        if current or word_index < len(target_words):
                            typed_words.append(current)
                            current = ""
                            word_index += 1
                            if word_index >= len(target_words):
                                break
                        dirty = True
                    elif key in ("\x08", "\x7f"):   # backspace
                        current = current[:-1]
                        dirty = True
                    elif key.isprintable():
                        current += key
                        dirty = True

                # Zamanlayıcı saniyesi değiştiyse veya tuş geldiyse yeniden çiz
                sec = int(remaining)
                if dirty or sec != last_render:
                    last_render = sec
                    wpm, cwords = _live_stats(
                        target_words, typed_words + [current], elapsed)

                    header = (f"{BOLD}Hızlı Yazma Testi{RESET}  "
                              f"{CYAN}{lang_name} · {mode_name}{RESET}")
                    stat = (f"Süre: {BOLD}{max(0, int(remaining))}sn{RESET}   "
                            f"Kelime: {BOLD}{cwords}{RESET}   "
                            f"WPM: {BOLD}{wpm}{RESET}")

                    # Görünür pencere: bulunduğumuz satır + sonraki 2 satır
                    cur_line = word_line.get(word_index, len(lines) - 1)
                    win = lines[cur_line:cur_line + 3]
                    body = []
                    for idxs in win:
                        parts = []
                        for wi in idxs:
                            if wi < word_index:
                                parts.append(_render_word(
                                    target_words[wi], typed_words[wi], False))
                            elif wi == word_index:
                                parts.append(_render_word(
                                    target_words[wi], current, True))
                            else:
                                parts.append(GREY + target_words[wi] + RESET)
                        body.append(" ".join(parts))
                    while len(body) < 3:
                        body.append("")

                    frame = [header, stat, ""] + body + [
                        "", GREY + "ESC: bitir/iptal   Boşluk: kelimeyi onayla" + RESET]
                    _draw(frame)
    finally:
        sys.stdout.write(SHOW_CUR + "\n")
        sys.stdout.flush()

    actual_duration = duration if started else 0
    if not typed_words:
        return None
    return storage.record_result(lang, target_words, typed_words, actual_duration)
