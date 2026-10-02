# -*- coding: utf-8 -*-
"""Kivi — terminal tabanlı hızlı yazma testi.

Çalıştırmak için:  python typing_test.py

Gereksinim:  pip install -r requirements.txt   (textual)

Renk seçenekleri:
  --color auto|truecolor|256|16   terminal renk modunu zorla (varsayılan: auto)
  --no-color                      tek renkli görünüm (NO_COLOR ortam değişkeni de bunu açar)
"""

import argparse
import os


def main():
    p = argparse.ArgumentParser(description="Kivi — terminalde hızlı yazma testi")
    p.add_argument("--color", choices=["auto", "truecolor", "256", "16"], default="auto",
                   help="renk modu (varsayılan: auto)")
    p.add_argument("--no-color", action="store_true", help="renkleri kapat")
    args = p.parse_args()

    # Ortamda NO_COLOR kalmış olabilir (bazı IDE/araçlar ayarlar); Kivi renkli bir
    # oyun olduğu için yalnızca --no-color verilirse tek renkli çalışır.
    if args.no_color:
        os.environ["NO_COLOR"] = "1"
    else:
        os.environ.pop("NO_COLOR", None)
        if args.color != "auto":
            os.environ["TEXTUAL_COLOR_SYSTEM"] = {"16": "standard"}.get(args.color, args.color)

    import ui
    ui.run()


if __name__ == "__main__":
    main()
