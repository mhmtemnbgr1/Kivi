# -*- coding: utf-8 -*-
"""Çekirdek mantık testleri.  Çalıştırma:  python -m unittest discover tests"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine  # noqa: E402
import storage  # noqa: E402


def make(words=("elma", "armut", "kitap"), duration=30):
    return engine.Session("tr", duration, words=list(words) * 40)


class SessionTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        storage.DATA_DIR, storage.DATA_FILE = d, os.path.join(d, "t.json")

    def test_empty_space_is_ignored(self):
        s = make()
        self.assertFalse(s.commit(now=100))
        self.assertEqual(s.index, 0)
        self.assertFalse(s.started)

    def test_perfect_word(self):
        s = make()
        for ch in "elma":
            s.type_char(ch, now=100)
        s.commit(now=100)
        self.assertEqual((s.correct_words(), s.wrong, s.accuracy()), (1, 0, 100.0))

    def test_wrong_and_skipped_letters_counted(self):
        s = make()
        s.type_char("x", now=100)       # e yerine x
        s.commit(now=100)               # l, m, a atlandı
        self.assertEqual(s.wrong, 4)
        self.assertEqual(s.letter_errors, {"e": 1, "l": 1, "m": 1, "a": 1})

    def test_extra_chars_hurt_accuracy(self):
        s = make()
        for ch in "elmaaa":
            s.type_char(ch, now=100)
        self.assertEqual(s.wrong, 2)

    def test_partial_last_word_is_scored(self):
        s = make()
        for ch in "el":
            s.type_char(ch, now=100)
        out = s.finish(now=130)
        self.assertEqual(out["total_words"], 1)
        self.assertEqual(out["mistyped_now"], ["elma"])

    def test_early_finish_uses_real_elapsed(self):
        s = make(duration=60)
        for ch in "elma":
            s.type_char(ch, now=100)
        s.commit(now=100)
        out = s.finish(now=106)          # 6 sn sonra ESC
        self.assertEqual(out["duration"], 6)
        self.assertEqual(out["wpm"], 8)  # 4 harf / 5 / (6/60)

    def test_nothing_typed_returns_none(self):
        self.assertIsNone(make().finish())

    def test_words_never_run_out(self):
        s = engine.Session("en", 30)
        for _ in range(500):
            for ch in s.target:
                s.type_char(ch, now=100)
            s.commit(now=100)
        self.assertGreater(len(s.words), s.index)

    def test_session_is_saved(self):
        s = make()
        for ch in "elma":
            s.type_char(ch, now=100)
        s.commit(now=100)
        s.finish(now=110)
        self.assertEqual(len(storage.history("tr")), 1)
        self.assertEqual(storage.load()["tr"]["letter_total"]["e"], 1)


class ModeTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        storage.DATA_DIR, storage.DATA_FILE = d, os.path.join(d, "t.json")

    @staticmethod
    def mk(mode, **kw):
        return engine.Session("tr", 30, mode, words=["elma", "armut", "kitap"] * 60, **kw)

    def test_sudden_death_ends_on_first_error(self):
        s = self.mk("sudden")
        s.type_char("e", now=100)
        self.assertIsNone(s.failed)
        s.type_char("x", now=100)
        self.assertEqual(s.failed, "error")
        self.assertTrue(s.is_over(now=100))
        self.assertEqual(s.finish(now=101)["failed"], "error")

    def test_sudden_death_skipped_letters_fail(self):
        s = self.mk("sudden")
        s.type_char("e", now=100)
        s.commit(now=100)
        self.assertEqual(s.failed, "error")

    def test_strict_blocks_wrong_word(self):
        s = self.mk("strict")
        for ch in "elmx":
            s.type_char(ch, now=100)
        self.assertFalse(s.commit(now=100))
        self.assertTrue(s.rejected)
        s.backspace()
        s.type_char("a", now=100)
        self.assertTrue(s.commit(now=100))
        self.assertEqual(s.index, 1)

    def test_speed_limit_fails_when_too_slow(self):
        s = self.mk("speed", limit=40)
        s.type_char("e", now=100)                 # çok yavaş: 12 sn'de tek harf
        for sec in range(1, 13):
            s.sample(now=100 + sec)
        self.assertEqual(s.failed, "speed")

    def test_speed_limit_survives_when_fast(self):
        s = self.mk("speed", limit=30)
        t = 100.0
        for i in range(60):                       # ~12 harf/sn  -> ~140 WPM
            for ch in s.target[len(s.current):len(s.current) + 1]:
                s.type_char(ch, now=t)
            if len(s.current) == len(s.target):
                s.commit(now=t)
            t += 0.2
            s.sample(now=t)
        self.assertIsNone(s.failed)

    def test_lesson_words_use_only_allowed_letters(self):
        import layouts
        for level in range(1, len(layouts.LESSONS["tr"]) + 1):
            allowed, focus = layouts.lesson_letters("tr", level)
            for w in engine.lesson_words("tr", level, 200):
                self.assertTrue(set(w) <= allowed, (level, w))
                self.assertTrue(any(c in focus for c in w), (level, w))

    def test_lesson_pass_unlocks_next(self):
        s = engine.Session("tr", 30, "lesson", lesson=1)
        for _ in range(10):
            for ch in s.target:
                s.type_char(ch, now=100)
            s.commit(now=100)
        out = s.finish(now=110)
        self.assertTrue(out["lesson_passed"])
        self.assertEqual(storage.unlocked_lesson("tr"), 2)

    def test_drill_is_30_seconds_and_falls_back(self):
        s = engine.Session("tr", 120, "drill")
        self.assertEqual(s.duration, 30)
        self.assertTrue(s.words)

    def test_bigrams_recorded(self):
        s = self.mk("normal")
        s.type_char("e", now=100.0)
        s.type_char("l", now=100.2)
        s.type_char("x", now=100.5)
        self.assertEqual(s.bigrams["el"][0], 1)
        self.assertAlmostEqual(s.bigrams["el"][1], 200, delta=1)
        self.assertEqual(s.bigrams["lm"][2], 1)    # x yanlış -> hata sayıldı

    def test_failed_runs_excluded_from_best(self):
        s = self.mk("sudden")
        s.type_char("x", now=100)
        s.finish(now=102)
        self.assertEqual(storage.best_wpm("tr"), 0)


class SoundTests(unittest.TestCase):
    def test_every_switch_generates_wavs(self):
        import sound
        k = sound.KeySound("blue")
        for sw in sound.ORDER[1:]:
            for kind in ("key", "space", "back"):
                for path in k._files(sw, kind):
                    self.assertTrue(os.path.getsize(path) > 1000)

    def test_cycle_wraps(self):
        import sound
        k = sound.KeySound("black")
        self.assertEqual(k.cycle(), "off")


if __name__ == "__main__":
    unittest.main()
