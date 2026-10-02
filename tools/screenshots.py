# -*- coding: utf-8 -*-
"""README görsellerini üretir (docs/*.svg).

Görseller SENTETİK demo verisiyle üretilir; gerçek `data/typing_data.json`
dosyasına dokunulmaz ve kişisel veri içermez.

Çalıştırma:  python tools/screenshots.py
"""

import asyncio
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import storage  # noqa: E402

OUT = os.path.join(ROOT, "docs")
SIZE = (100, 46)


def seed_demo():
    """Geçici dizinde sahte istatistik oluşturur ve storage'ı oraya yönlendirir."""
    tmp = tempfile.mkdtemp(prefix="kivi_demo_")
    storage.DATA_DIR = tmp
    storage.DATA_FILE = os.path.join(tmp, "typing_data.json")
    data = {"tr": storage._empty_lang(), "en": storage._empty_lang()}
    d = data["tr"]
    d["letter_total"] = {c: 40 for c in "ağıöşçüeklmnrtdyuoibzsvhfjp"}
    d["letter_errors"] = {"ğ": 14, "ö": 11, "ç": 9, "ş": 7, "j": 6, "v": 5, "ü": 4, "ı": 3}
    d["mistyped"] = {"öğretmen": 4, "çığlık": 3, "gökyüzü": 3, "şoför": 2, "fırtına": 2}
    wpms = [38, 41, 40, 45, 47, 46, 52, 50, 55, 58, 57, 61]
    d["history"] = [{"date": f"2026-09-{i + 10:02d} 20:{i:02d}", "duration": 30, "wpm": w,
                     "correct_words": w // 2, "accuracy": 90 + (i % 8)}
                    for i, w in enumerate(wpms)]
    storage.save(data)


async def main():
    seed_demo()
    import ui
    os.makedirs(OUT, exist_ok=True)

    def shot(app, name):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(app.export_screenshot(title="Kivi"))
        print("yazıldı:", name)

    app = ui.KiviApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        shot(app, "menu.svg")

        await pilot.press("enter")                      # test ekranı
        await pilot.pause()
        s = app.screen.session
        s.words[:12] = ["merhaba", "dünya", "klavye", "hızlı", "yazmak", "güzel",
                        "öğrenci", "çiçek", "şehir", "bilgi", "ekran", "zaman"]
        for ch in "merhaba dünya klavye hız":
            await pilot.press("space" if ch == " " else ch)
        s.start = time.time() - 18                      # ~18 sn geçmiş gibi
        # canlı grafik için örnek WPM verisi
        app.screen.query_one("Sparkline").data = [22, 31, 38, 41, 44, 43, 48, 52, 50, 55, 54, 58]
        await pilot.pause()
        shot(app, "test.svg")

        await pilot.press("escape")                     # sonuç ekranı
        await pilot.pause()
        app.screen.query_one("Sparkline").data = [22, 31, 38, 41, 44, 43, 48, 52, 50, 55, 54, 58]
        shot(app, "result.svg")

        await pilot.press("w")                          # istatistik
        await pilot.pause()
        shot(app, "stats.svg")


if __name__ == "__main__":
    asyncio.run(main())
