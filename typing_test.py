# -*- coding: utf-8 -*-
"""Terminal tabanlı Hızlı Yazma Testi.

Çalıştırmak için:  python typing_test.py

Özellikler:
  - Süre ayarlı test, sürede yazılan kelime/WPM ölçümü
  - Türkçe (F klavye) ve İngilizce (QWERTY) olmak üzere 2 dil
  - Yanlış yazılan kelimeler ve harfler hafızada tutulur
  - "Zayıf harflerin" raporu (en sık hata yapılan harfler + klavye konumu)
  - Yanlış kelime havuzu görüntüleme
  - Alıştırma modu: bilmediğin/yanlış yazdığın kelimeler sık sık çıkar
"""

import sys

import engine
import storage

BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
GREY = "\033[90m"
RESET = "\033[0m"


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def prompt(msg):
    try:
        return input(msg)
    except (EOFError, KeyboardInterrupt):
        return ""


def choose_duration():
    print(f"\n{BOLD}Süre seç:{RESET}")
    print("  1) 15 saniye")
    print("  2) 30 saniye")
    print("  3) 60 saniye")
    print("  4) Özel (saniye gir)")
    c = prompt("Seçim [2]: ").strip() or "2"
    if c == "1":
        return 15
    if c == "3":
        return 60
    if c == "4":
        v = prompt("Kaç saniye? ").strip()
        try:
            return max(5, min(600, int(v)))
        except ValueError:
            return 30
    return 30


def show_result(summary):
    if not summary:
        print(f"\n{GREY}Test iptal edildi veya kelime yazılmadı.{RESET}")
        prompt("\nDevam etmek için Enter...")
        return
    lang_name = "Türkçe" if summary["lang"] == "tr" else "İngilizce"
    print(f"\n{BOLD}=== Sonuç ({lang_name}) ==={RESET}")
    print(f"  Süre           : {summary['duration']} sn")
    print(f"  {BOLD}WPM (net)      : {summary['wpm']}{RESET}   "
          f"{GREY}(ham: {summary['raw_wpm']}){RESET}")
    print(f"  Doğru kelime   : {GREEN}{summary['correct_words']}{RESET} "
          f"/ {summary['total_words']}")
    print(f"  Doğruluk       : {summary['accuracy']}%")
    if summary["mistyped_now"]:
        kelimeler = ", ".join(summary["mistyped_now"][:15])
        print(f"  {RED}Yanlış kelimeler{RESET}: {kelimeler}")
    else:
        print(f"  {GREEN}Hiç yanlış yok! 🎉{RESET}")
    prompt("\nDevam etmek için Enter...")


def show_weak_letters(lang):
    clear()
    lang_name = "Türkçe (F klavye)" if lang == "tr" else "İngilizce (QWERTY)"
    print(f"{BOLD}=== Zayıf Harflerin — {lang_name} ==={RESET}\n")
    rows = storage.weak_letters(lang, top=12)
    if not rows:
        print(f"{GREY}Henüz yeterli veri yok. Birkaç test yap!{RESET}")
    else:
        print(f"  {'Harf':<6}{'Hata':<8}{'Deneme':<9}{'Oran':<9}Konum")
        print(f"  {'-'*4:<6}{'-'*4:<8}{'-'*6:<9}{'-'*4:<9}{'-'*20}")
        for ch, err, total, rate, pos in rows:
            print(f"  {RED}{ch:<6}{RESET}{err:<8}{total:<9}{rate:<8}% {pos}")
        print(f"\n{GREY}Oran = harfi yazarken yaptığın hata yüzdesi. "
              f"En üsttekilere odaklan.{RESET}")
    prompt("\nDevam etmek için Enter...")


def show_pool(lang):
    clear()
    lang_name = "Türkçe" if lang == "tr" else "İngilizce"
    print(f"{BOLD}=== Yanlış Kelime Havuzu — {lang_name} ==={RESET}\n")
    pool = storage.mistyped_pool(lang)
    if not pool:
        print(f"{GREY}Havuz boş. (Ya çok iyisin ya da henüz test yapmadın.){RESET}")
    else:
        print(f"  Toplam {len(pool)} farklı kelime. (en çok yanlış üstte)\n")
        for i, (w, c) in enumerate(pool, 1):
            print(f"  {i:>3}. {w:<22}{GREY}{c}x{RESET}")
            if i % 40 == 0:
                if prompt(f"{GREY}--- devam için Enter (q: çık) ---{RESET} ").strip().lower() == "q":
                    break
        print(f"\n{GREY}İpucu: Alıştırma modunda bu kelimeler sık sık karşına çıkar.{RESET}")
    prompt("\nDevam etmek için Enter...")


def show_history(lang):
    clear()
    lang_name = "Türkçe" if lang == "tr" else "İngilizce"
    print(f"{BOLD}=== Geçmiş — {lang_name} ==={RESET}\n")
    hist = storage.history(lang)
    if not hist:
        print(f"{GREY}Henüz test kaydı yok.{RESET}")
    else:
        print(f"  {'Tarih':<18}{'Süre':<7}{'WPM':<6}{'Doğru kel.':<12}Doğruluk")
        for h in hist[-20:]:
            print(f"  {h['date']:<18}{str(h['duration'])+'sn':<7}"
                  f"{h['wpm']:<6}{h['correct_words']:<12}{h['accuracy']}%")
        best = max(hist, key=lambda h: h["wpm"])
        print(f"\n  {GREEN}En yüksek WPM: {best['wpm']} ({best['date']}){RESET}")
    prompt("\nDevam etmek için Enter...")


def choose_language(action="test"):
    print(f"\n{BOLD}Dil seç:{RESET}")
    print("  1) Türkçe (F klavye)")
    print("  2) İngilizce (QWERTY)")
    c = prompt("Seçim [1]: ").strip() or "1"
    return "en" if c == "2" else "tr"


def reset_menu():
    clear()
    print(f"{BOLD}=== Sıfırla ==={RESET}\n")
    print("  1) Türkçe verilerini sıfırla")
    print("  2) İngilizce verilerini sıfırla")
    print("  3) Vazgeç")
    c = prompt("Seçim: ").strip()
    if c == "1":
        if prompt(f"{RED}Emin misin? (e/h): {RESET}").strip().lower() == "e":
            storage.reset("tr")
            print(f"{GREEN}Türkçe verileri sıfırlandı.{RESET}")
    elif c == "2":
        if prompt(f"{RED}Emin misin? (e/h): {RESET}").strip().lower() == "e":
            storage.reset("en")
            print(f"{GREEN}İngilizce verileri sıfırlandı.{RESET}")
    prompt("\nDevam etmek için Enter...")


def main_menu():
    engine.enable_ansi()
    while True:
        clear()
        print(f"{BOLD}{CYAN}╔══════════════════════════════════════╗{RESET}")
        print(f"{BOLD}{CYAN}║       HIZLI YAZMA TESTİ ⌨️            ║{RESET}")
        print(f"{BOLD}{CYAN}╚══════════════════════════════════════╝{RESET}\n")
        print("  1) Test başlat (normal)")
        print("  2) Alıştırma modu (zayıf kelimeler sık çıkar)")
        print("  3) Zayıf harflerim")
        print("  4) Yanlış kelime havuzu")
        print("  5) İstatistik / geçmiş")
        print("  6) Verileri sıfırla")
        print("  0) Çıkış")
        c = prompt("\nSeçim: ").strip()

        if c == "1":
            lang = choose_language()
            dur = choose_duration()
            print(f"\n{GREY}Hazır ol... ilk tuşa bastığında süre başlar.{RESET}")
            prompt("Başlamak için Enter...")
            summary = engine.run_test(lang, dur, mode="normal")
            show_result(summary)
        elif c == "2":
            lang = choose_language()
            dur = choose_duration()
            print(f"\n{GREY}Alıştırma modu: yanlış yazdığın kelimeler "
                  f"daha sık çıkar. İlk tuşta süre başlar.{RESET}")
            prompt("Başlamak için Enter...")
            summary = engine.run_test(lang, dur, mode="practice")
            show_result(summary)
        elif c == "3":
            show_weak_letters(choose_language())
        elif c == "4":
            show_pool(choose_language())
        elif c == "5":
            show_history(choose_language())
        elif c == "6":
            reset_menu()
        elif c == "0" or c == "":
            clear()
            print("Görüşürüz! 👋")
            break


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h\n")
        print("Çıkıldı.")
