# -*- coding: utf-8 -*-
"""Yazma testi çekirdeği: kelime üretimi, tuş işleme, modlar, WPM/doğruluk hesabı.

Bu modül terminalden bağımsızdır (arayüz `ui.py` içindedir); bu sayede
mantık tek başına test edilebilir.

Modlar:
  normal    rastgele kelimeler
  practice  yanlış yazılan kelimeler ve zayıf harfler sık çıkar
  drill     zayıf harf + zayıf harf çifti drili (sabit 30 sn)
  strict    hata düzeltmeli: kelime doğru yazılmadan sonrakine geçilmez
  sudden    ölüm modu: ilk hatada test biter
  speed     hız limiti: son 5 sn'lik hızın limitin altına düşerse test biter
  lesson    ders: yalnızca öğrenilen harflerle alıştırma
"""

import random
import time
from datetime import datetime

import layouts
import storage
from words import get_wordlist

REFILL = 40      # önümüzde bu kadar kelime kalırsa yenisini ekle
CHUNK = 80       # her eklemede kaç kelime
GRACE = 8        # hız limiti modunda ilk saniyeler tolerans
WINDOW = 5       # hız limiti için ölçüm penceresi (sn)
DRILL_SECONDS = 30
PASS_ACCURACY = 90.0   # ders geçmek için gereken doğruluk
PASS_WORDS = 8         # ... ve doğru kelime sayısı

MODE_ORDER = ["normal", "practice", "drill", "strict", "sudden", "speed", "lesson"]


def weak_letter_set(lang, top=8):
    return [(r[0], r[1]) for r in storage.weak_letters(lang, top=top, min_total=3)]


def _no_repeats(out, base):
    for i in range(1, len(out)):                # art arda aynı kelime gelmesin
        if out[i] == out[i - 1]:
            out[i] = random.choice(base)
    return out


def lesson_words(lang, level, count):
    """Yalnızca öğrenilmiş harflerden kelime üretir; her kelimede odak harf bulunur."""
    allowed, focus = layouts.lesson_letters(lang, level)
    base = get_wordlist(lang)
    real = [w for w in base if set(w) <= allowed and any(c in focus for c in w)]
    pool = sorted(allowed)
    out = []
    for _ in range(count):
        if real and random.random() < 0.45:
            out.append(random.choice(real))
            continue
        n = random.randint(3, 5)
        chars = [random.choice(focus) if random.random() < 0.5 else random.choice(pool)
                 for _ in range(n)]
        if not any(c in focus for c in chars):
            chars[random.randrange(n)] = random.choice(focus)
        out.append("".join(chars))
    return _no_repeats(out, real or ["a" * 3])


def drill_words(lang, count):
    """Zayıf harf ve harf çiftlerini yoğun içeren kelimeler; veri yoksa None."""
    letters = {r[0] for r in storage.weak_letters(lang, top=5, min_total=3)}
    pairs = [r[0] for r in storage.weak_bigrams(lang, top=6)]
    base = get_wordlist(lang)
    words, weights = [], []
    for w in base:
        score = 3 * sum(1 for p in pairs if p in w) + sum(1 for c in w if c in letters)
        if score:
            words.append(w)
            weights.append(score)
    for w, c in storage.mistyped_pool(lang):
        words.append(w)
        weights.append(min(c, 6) * 3)
    if not words:
        return None
    return _no_repeats(random.choices(words, weights=weights, k=count), base)


def generate_words(lang, mode, count, lesson=1):
    """Moda göre kelime akışı üretir."""
    base = get_wordlist(lang)
    if mode == "lesson":
        return lesson_words(lang, lesson, count)
    if mode == "drill":
        out = drill_words(lang, count)
        if out:
            return out
    if mode == "practice":
        pool = storage.mistyped_pool(lang)
        weakset = {w for w, _ in weak_letter_set(lang)}
        if pool or weakset:
            words, weights = [], []
            for w, c in pool:
                words.append(w)
                weights.append(min(c, 6) * 5)   # çok yanlış = sık, ama tek kelime ekranı kaplamasın
            for w in base:
                words.append(w)
                weights.append(2 if any(ch in weakset for ch in w) else 1)
            return _no_repeats(random.choices(words, weights=weights, k=count), base)
    return _no_repeats(random.choices(base, k=count), base)


class Session:
    """Tek bir test oturumu. Zaman dışarıdan (`now`) verilebilir -> test edilebilir."""

    def __init__(self, lang, duration, mode="normal", words=None, limit=30, lesson=1):
        self.lang = lang
        self.mode = mode
        self.duration = DRILL_SECONDS if mode == "drill" else duration
        self.limit = limit
        self.lesson = lesson
        self.words = words or generate_words(lang, mode, CHUNK * 2, lesson)
        self.typed = []            # onaylanmış kelimeler
        self.current = ""
        self.start = None
        self.last_sample = 0
        self.samples = []          # saniye saniye WPM
        self.hist = []             # (geçen_sn, doğru_karakter) -> anlık hız ölçümü
        self.keys = 0              # basılan karakter tuşu sayısı
        self.wrong = 0             # yanlış basılan tuş sayısı
        self.letter_total = {}
        self.letter_errors = {}
        self.bigrams = {}          # harf çifti -> [adet, toplam_ms, hata]
        self.last_key_time = None
        self.last_wrong = None     # son yanlış basılan tuş (ekran klavyesi için)
        self.failed = None         # None | "error" (ölüm) | "speed" (hız limiti)
        self.rejected = False      # hata düzeltmeli modda reddedilen onay

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
        return min(self.duration, (time.time() if now is None else now) - self.start)

    def remaining(self, now=None):
        return max(0.0, self.duration - self.elapsed(now))

    def is_over(self, now=None):
        return self.started and (self.remaining(now) <= 0 or self.failed is not None)

    # -- girdi -------------------------------------------------------------
    def _begin(self, now):
        if not self.started:
            self.start = time.time() if now is None else now

    def _extend(self):
        if len(self.words) - self.index < REFILL:
            self.words += generate_words(self.lang, self.mode, CHUNK, self.lesson)

    def type_char(self, ch, now=None):
        now = time.time() if now is None else now
        self._begin(now)
        self.rejected = False
        t = self.target
        pos = len(self.current)
        self.keys += 1
        bad = False
        if pos < len(t):
            exp = t[pos]
            self.letter_total[exp] = self.letter_total.get(exp, 0) + 1
            bad = ch != exp
            if bad:
                self.letter_errors[exp] = self.letter_errors.get(exp, 0) + 1
            # Harf çifti: önceki tuş doğruysa ve duraklama yoksa geçiş süresini ölç
            if (pos >= 1 and self.current[-1] == t[pos - 1]
                    and self.last_key_time is not None and now - self.last_key_time < 2.0):
                b = self.bigrams.setdefault(t[pos - 1] + exp, [0, 0.0, 0])
                b[0] += 1
                b[1] += (now - self.last_key_time) * 1000
                b[2] += 1 if bad else 0
        else:                       # kelimeden fazla karakter
            bad = True
        if bad:
            self.wrong += 1
            self.last_wrong = ch
            if self.mode == "sudden":
                self.failed = "error"
        else:
            self.last_wrong = None
        self.last_key_time = now
        self.current += ch

    def backspace(self):
        self.rejected = False
        self.current = self.current[:-1]
        self.last_wrong = None

    def commit(self, now=None):
        """Boşluk/Enter: kelimeyi onayla. Boş kelimede hiçbir şey yapmaz.

        Hata düzeltmeli modda kelime doğru değilse onay reddedilir (False döner).
        """
        if not self.current:
            return False
        if self.mode == "strict" and self.current != self.target:
            self.rejected = True
            return False
        self._begin(now)
        self.rejected = False
        t = self.target
        skipped = t[len(self.current):]
        for ch in skipped:                      # atlanan harfler hata sayılır
            self.letter_total[ch] = self.letter_total.get(ch, 0) + 1
            self.letter_errors[ch] = self.letter_errors.get(ch, 0) + 1
            self.wrong += 1
        if skipped and self.mode == "sudden":
            self.failed = "error"
        self.typed.append(self.current)
        self.current = ""
        self.last_wrong = None
        self.last_key_time = None
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

    def speed_now(self, now=None):
        """Son WINDOW saniyedeki hız (WPM); henüz yeterli veri yoksa None."""
        el = self.elapsed(now)
        if el < WINDOW or not self.hist:
            return None
        cutoff = el - WINDOW
        then = min(self.hist, key=lambda h: abs(h[0] - cutoff))
        span = el - then[0]
        if span < WINDOW * 0.8:
            return None
        return round((self.correct_chars() - then[1]) / 5.0 / (span / 60.0))

    def accuracy(self):
        return round(100.0 * (self.keys - self.wrong) / self.keys, 1) if self.keys else 100.0

    def correct_words(self):
        return sum(1 for t, w in zip(self.typed, self.words) if t == w)

    def sample(self, now=None):
        """Saniyede bir WPM örneği ekler (canlı grafik) ve hız limitini denetler."""
        if not self.started:
            return
        el = self.elapsed(now)
        while self.last_sample < int(el):
            self.last_sample += 1
            self.samples.append(self.wpm(self.start + self.last_sample))
        self.hist.append((el, self.correct_chars()))
        self.hist = [h for h in self.hist if h[0] >= el - WINDOW - 2]
        if self.mode == "speed" and self.failed is None and el >= GRACE:
            cur = self.speed_now(now)
            if cur is not None and cur < self.limit:
                self.failed = "speed"

    # -- bitiş -------------------------------------------------------------
    def finish(self, now=None):
        """Süre bitince, elenince ya da ESC ile: sonucu kaydeder; kelime yazılmadıysa None."""
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
            "lesson": self.lesson,
            "limit": self.limit,
            "failed": self.failed,
            "duration": round(el),
            "wpm": round(self.correct_chars() / 5.0 / minutes),
            "raw_wpm": round(typed_chars / 5.0 / minutes),
            "correct_words": self.correct_words(),
            "total_words": len(self.typed),
            "accuracy": self.accuracy(),
            "mistyped_now": mistyped,
            "samples": list(self.samples),
        }
        summary["lesson_passed"] = (
            self.mode == "lesson" and self.failed is None
            and summary["accuracy"] >= PASS_ACCURACY
            and summary["correct_words"] >= PASS_WORDS)
        storage.record_session(self.lang, summary, self.letter_total, self.letter_errors,
                               {k: tuple(v) for k, v in self.bigrams.items()})
        if summary["lesson_passed"]:
            storage.lesson_done(self.lang, self.lesson, summary["wpm"])
        return summary
