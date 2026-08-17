# ⌨️ Hızlı Yazma Testi (Terminal)

Terminal tabanlı, gerçek zamanlı bir yazma hızı testi. Süre boyunca yazdığın
kelimeleri ölçer, yanlışlarını hatırlar ve zayıf harflerini raporlar.

## Çalıştırma

```bash
python typing_test.py
```

> Not: Gerçek zamanlı tuş okuma için gerçek bir terminalde çalıştır
> (Windows Terminal / PowerShell / CMD). IDE'nin çıktı panelinde çalışmayabilir.

## Özellikler

- ⏱️ **Süre ayarlı test** — 15 / 30 / 60 sn veya özel süre. Süre içinde kaç
  kelime yazdığını ve WPM'ini gösterir. Süre ilk tuşa bastığında başlar.
- 🇹🇷 / 🇬🇧 **İki dil** — Türkçe (F klavye) ve İngilizce (QWERTY).
- 🧠 **Hafıza** — Yanlış yazılan kelimeler ve harfler oturumlar arası
  kaydedilir (`data/typing_data.json`).
- 📉 **Zayıf harflerin** — En sık hata yaptığın harfleri, hata oranını ve
  o tuşun **klavyedeki konumunu** (üst/orta/alt sıra, sol/sağ el) gösterir.
- 🗂️ **Yanlış kelime havuzu** — Doğru yazamadığın tüm kelimeleri listeler.
- 🎯 **Alıştırma modu** — Yanlış yazdığın kelimeler ve zayıf harf içeren
  kelimeler **daha sık** karşına çıkar; böylece zayıf noktalarını çalışırsın.
- 📊 **Geçmiş** — Son testlerin ve en yüksek WPM'in.

## Test sırasında

- Yaz: harfler doğruysa **yeşil**, yanlışsa **kırmızı** renklenir.
- **Boşluk / Enter**: kelimeyi onaylar (bir sonrakine geçer).
- **Backspace**: son harfi siler.
- **ESC**: testi bitirir / iptal eder.

## Dosyalar

| Dosya | Görevi |
|-------|--------|
| `typing_test.py` | Ana menü ve giriş noktası |
| `engine.py` | Gerçek zamanlı tuş okuma, zamanlayıcı, canlı ekran |
| `storage.py` | İstatistik/havuz kaydı ve analiz (JSON) |
| `words.py` | Türkçe ve İngilizce kelime havuzları |
| `layouts.py` | F klavye ve QWERTY harf konumları |
| `data/` | Kayıtlı istatistikler (otomatik oluşur) |
