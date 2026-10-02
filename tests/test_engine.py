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


if __name__ == "__main__":
    unittest.main()
