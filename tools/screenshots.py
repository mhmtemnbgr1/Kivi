# -*- coding: utf-8 -*-
"""README görsellerini üretir (docs/*.svg).

Görseller SENTETİK demo verisiyle üretilir; gerçek `data/typing_data.json`
dosyasına dokunulmaz ve kişisel veri içermez. Üretim sırasında ses kapalıdır.

Çalıştırma:  python tools/screenshots.py
"""

import asyncio
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.pop("NO_COLOR", None)

import storage  # noqa: E402

OUT = os.path.join(ROOT, "docs")
SIZE = (100, 50)
SAMPLES = [22, 31, 38, 41, 44, 43, 48, 52, 50, 55, 54, 58]


def seed_demo():
    """Geçici dizinde sahte istatistik oluşturur ve storage'ı oraya yönlendirir."""
    tmp = tempfile.mkdtemp(prefix="kivi_demo_")
    storage.DATA_DIR = tmp
    storage.DATA_FILE = os.path.join(tmp, "typing_data.json")
    data = {"tr": storage._empty_lang(), "en": storage._empty_lang(), "settings": {}}
    d = data["tr"]
    d["letter_total"] = {c: 40 for c in "ağıöşçüeklmnrtdyuoibzsvhfjp"}
    d["letter_errors"] = {"ğ": 14, "ö": 11, "ç": 9, "ş": 7, "j": 6, "v": 5, "ü": 4, "ı": 3}
    d["mistyped"] = {"öğretmen": 4, "çığlık": 3, "gökyüzü": 3, "şoför": 2, "fırtına": 2}
    d["bigrams"] = {"ğı": {"n": 24, "ms": 7900, "err": 6}, "şı": {"n": 18, "ms": 5600, "err": 3},
                    "öğ": {"n": 30, "ms": 8800, "err": 5}, "çı": {"n": 22, "ms": 5900, "err": 2},
                    "ıl": {"n": 40, "ms": 9200, "err": 2}, "üş": {"n": 15, "ms": 4300, "err": 2},
                    "ve": {"n": 60, "ms": 9000, "err": 1}, "ir": {"n": 55, "ms": 8000, "err": 0}}
    d["lessons"] = {"1": 28, "2": 34}                 # 3. ders açık
    wpms = [38, 41, 40, 45, 47, 46, 52, 50, 55, 58, 57, 61]
    modes = ["normal", "normal", "lesson", "practice", "normal", "strict",
             "normal", "drill", "normal", "normal", "speed", "normal"]
    d["history"] = [{"date": f"2026-09-{i + 10:02d} 20:{i:02d}", "duration": 30, "wpm": w,
                     "correct_words": w // 2, "accuracy": 90 + (i % 8), "mode": modes[i]}
                    for i, w in enumerate(wpms)]
    d["history"].insert(5, {"date": "2026-09-14 21:05", "duration": 9, "wpm": 33,
                            "correct_words": 4, "accuracy": 96.0, "mode": "sudden",
                            "failed": "error"})
    storage.save(data)


def type_words(s, n):
    """Oturumdaki ilk n kelimeyi doğru yazılmış gibi işler."""
    for _ in range(n):
        for ch in s.target:
            s.type_char(ch)
        s.commit()


async def main():
    seed_demo()
    import ui
    os.makedirs(OUT, exist_ok=True)

    def shot(app, name):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(app.export_screenshot(title="Kivi"))
        print("yazıldı:", name)

    app = ui.KiviApp()
    app.sound.switch = "off"                            # üretim sırasında ses çalma
    app.mode, app.lesson, app.fingers = "lesson", 3, True
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        shot(app, "menu.svg")

        # Ders modu: parmak renkleri + kilitli tuşlar
        await pilot.press("enter")
        await pilot.pause()
        s = app.screen.session
        type_words(s, 2)
        s.start = time.time() - 14
        await pilot.press(*s.target[:2])
        await pilot.pause()
        shot(app, "lesson.svg")
        await pilot.press("escape")                     # ders sonucu
        await pilot.pause()
        await pilot.press("m")

        # Normal test
        app.mode, app.fingers = "normal", False
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        s = app.screen.session
        s.words[:12] = ["merhaba", "dünya", "klavye", "hızlı", "yazmak", "güzel",
                        "öğrenci", "çiçek", "şehir", "bilgi", "ekran", "zaman"]
        for ch in "merhaba dünya klavye hız":
            await pilot.press("space" if ch == " " else ch)
        app.screen.press("ı", True)
        s.start = time.time() - 18                      # ~18 sn geçmiş gibi
        await pilot.pause()
        shot(app, "test.svg")
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("m")

        # Ölüm modu: ilk hatada elenir
        app.mode = "sudden"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        s = app.screen.session
        type_words(s, 6)
        s.start = time.time() - 11
        wrong = "x" if s.next_char() != "x" else "q"
        await pilot.press(wrong)
        await pilot.pause()
        app.screen.query_one("Sparkline").data = SAMPLES
        shot(app, "result.svg")

        await pilot.press("w")                          # istatistik
        await pilot.pause()
        shot(app, "stats.svg")
        await pilot.press("4")
        await pilot.pause()
        shot(app, "pairs.svg")


if __name__ == "__main__":
    asyncio.run(main())
