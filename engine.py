# -*- coding: utf-8 -*-
"""Yazma testi çekirdeği: kelime üretimi, tuş işleme, WPM/doğruluk hesabı.

Bu modül terminalden bağımsızdır (arayüz `ui.py` içindedir); bu sayede
mantık tek başına test edilebilir.
"""

import random
import time
from datetime import datetime

import storage
from words import get_wordlist

REFILL = 40      # önümüzde bu kadar kelime kalırsa yenisini ekle
CHUNK = 80       # her eklemede kaç kelime


def weak_letter_set(lang, top=8):
    return [(r[0], r[1]) for r in storage.weak_letters(lang, top=top, min_total=3)]


def generate_words(lang, mode, count):
    """Kelime akışı üretir.

    mode='normal'   -> temel havuzdan rastgele
    mode='practice' -> yanlış yazılan kelimeler ve zayıf harf içerenler ağırlıklı
    """
    base = get_wordlist(lang)
    if mode != "practice":
        out = random.choices(base, k=count)
    else:
        pool = storage.mistyped_pool(lang)
        weakset = {w for w, _ in weak_letter_set(lang)}
        if not pool and not weakset:
            out = random.choices(base, k=count)
        else:
            words, weights = [], []
            for w, c in pool:
                words.append(w)
                weights.append(min(c, 6) * 5)   # çok yanlış = sık, ama tek kelime ekranı kaplamasın
            for w in base:
                words.append(w)
                weights.append(2 if any(ch in weakset for ch in w) else 1)
            out = random.choices(words, weights=weights, k=count)
    for i in range(1, len(out)):                # art arda aynı kelime gelmesin
        if out[i] == out[i - 1]:
            out[i] = random.choice(base)
    return out


class Session:
    """Tek bir test oturumu. Zaman dışarıdan (`now`) verilebilir -> test edilebilir."""

    def __init__(self, lang, duration, mode="normal", words=None):
        self.lang = lang
        self.duration = duration
        self.mode = mode
        self.words = words or generate_words(lang, mode, CHUNK * 2)
        self.typed = []            # onaylanmış kelimeler
        self.current = ""
        self.start = None
        self.last_sample = 0
        self.samples = []          # saniye saniye WPM
        self.keys = 0              # basılan karakter tuşu sayısı
        self.wrong = 0             # yanlış basılan tuş sayısı
        self.letter_total = {}
        self.letter_errors = {}
        self.last_wrong = None     # son yanlış basılan tuş (ekran klavyesi için)

    # -- durum -------------------------------------------------------------
    @property
    def started(self):
        return self.start is not None

    @property
    def index(self):
        return len(self.typed)

    @property
    def target(self):
        return self.words[self.index]

    def next_char(self):
        """Sıradaki basılması gereken tuş (kelime bitmişse boşluk)."""
        t = self.target
        return t[len(self.current)] if len(self.current) < len(t) else " "

    def elapsed(self, now=None):
        if not self.started:
            return 0.0
        return min(self.duration, (now or time.time()) - self.start)

    def remaining(self, now=None):
        return max(0.0, self.duration - self.elapsed(now))

    def is_over(self, now=None):
        return self.started and self.remaining(now) <= 0

    # -- girdi -------------------------------------------------------------
    def _begin(self, now):
        if not self.started:
            self.start = now or time.time()

    def _extend(self):
        if len(self.words) - self.index < REFILL:
            self.words += generate_words(self.lang, self.mode, CHUNK)

    def type_char(self, ch, now=None):
        self._begin(now)
        t = self.target
        pos = len(self.current)
        self.keys += 1
        if pos < len(t):
            exp = t[pos]
            self.letter_total[exp] = self.letter_total.get(exp, 0) + 1
            if ch != exp:
                self.letter_errors[exp] = self.letter_errors.get(exp, 0) + 1
                self.wrong += 1
                self.last_wrong = ch
            else:
                self.last_wrong = None
        else:                       # kelimeden fazla karakter
            self.wrong += 1
            self.last_wrong = ch
        self.current += ch

    def backspace(self):
        self.current = self.current[:-1]
        self.last_wrong = None

    def commit(self, now=None):
        """Boşluk/Enter: kelimeyi onayla. Boş kelimede hiçbir şey yapmaz."""
        if not self.current:
            return False
        self._begin(now)
        t = self.target
        for ch in t[len(self.current):]:        # atlanan harfler hata sayılır
            self.letter_total[ch] = self.letter_total.get(ch, 0) + 1
            self.letter_errors[ch] = self.letter_errors.get(ch, 0) + 1
            self.wrong += 1
        self.typed.append(self.current)
        self.current = ""
        self.last_wrong = None
        self._extend()
        return True

    # -- ölçüm -------------------------------------------------------------
    def correct_chars(self):
        n = 0
        for typed, target in zip(self.typed + [self.current], self.words):
            n += sum(1 for a, b in zip(typed, target) if a == b)
        return n

    def wpm(self, now=None):
        el = self.elapsed(now)
        if el <= 0:
            return 0
        return round(self.correct_chars() / 5.0 / (el / 60.0))

    def accuracy(self):
        return round(100.0 * (self.keys - self.wrong) / self.keys, 1) if self.keys else 100.0

    def correct_words(self):
        return sum(1 for t, w in zip(self.typed, self.words) if t == w)

    def sample(self, now=None):
        """Her tam saniyede bir WPM örneği ekler (canlı grafik için)."""
        sec = int(self.elapsed(now))
        while self.started and self.last_sample < sec:
            self.last_sample += 1
            self.samples.append(self.wpm(self.start + self.last_sample))

    # -- bitiş -------------------------------------------------------------
    def finish(self, now=None):
        """Süre bitince ya da ESC ile: sonucu kaydeder; kelime yazılmadıysa None."""
        if self.current:                      # yarım kalan son kelime de sayılsın
            self.typed.append(self.current)
            self.current = ""
        if not self.typed:
            return None
        el = max(self.elapsed(now), 1.0)
        minutes = el / 60.0
        mistyped = [w for t, w in zip(self.typed, self.words) if t != w]
        typed_chars = sum(len(t) for t in self.typed)
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "lang": self.lang,
            "mode": self.mode,
            "duration": round(el),
            "wpm": round(self.correct_chars() / 5.0 / minutes),
            "raw_wpm": round(typed_chars / 5.0 / minutes),
            "correct_words": self.correct_words(),
            "total_words": len(self.typed),
            "accuracy": self.accuracy(),
            "mistyped_now": mistyped,
            "samples": list(self.samples),
        }
        storage.record_session(self.lang, summary, self.letter_total, self.letter_errors)
        return summary
