# ⌨️ Kivi — Terminalde Hızlı Yazma Testi

Gerçek zamanlı, renkli ve canlı bir terminal arayüzüne sahip yazma hızı testi.
Yazdıkça **canlı WPM grafiği** çizilir, **ekran klavyesi** sıradaki tuşu gösterir,
yanlışlarını ve zayıf harflerini hatırlayıp sana özel alıştırma yaptırır.

<p align="center">
  <img src="docs/menu.svg" alt="Ana menü" width="48%">
  <img src="docs/test.svg" alt="Canlı test ekranı" width="48%">
</p>
<p align="center">
  <img src="docs/result.svg" alt="Sonuç ekranı" width="48%">
  <img src="docs/stats.svg" alt="Zayıf harf ısı haritası" width="48%">
</p>

> Görseller sentetik demo verisiyle üretilmiştir; kişisel veri içermez
> (`python tools/screenshots.py`).

## Kurulum ve çalıştırma

```bash
pip install -r requirements.txt
python typing_test.py
```

Python 3.9+ ve renk destekleyen bir terminal (Windows Terminal, PowerShell, iTerm2, …)
yeterlidir. IDE çıktı panelinde değil, gerçek bir terminalde çalıştır.

## Özellikler

- ⏱️ **Süre ayarlı test** — 15 / 30 / 60 / 120 sn. Süre ilk tuşa basınca başlar.
- 📈 **Canlı WPM grafiği** ve doğruluk göstergesi, ilerleme çubuğu.
- 🎹 **Ekran klavyesi** — F klavye (Türkçe) ve QWERTY; sıradaki tuş mavi, yanlış basılan tuş kırmızı yanar.
- 🇹🇷 / 🇬🇧 **İki dil** — Türkçe (F klavye) ve İngilizce (QWERTY).
- 🔥 **Zayıf harf ısı haritası** — hata oranına göre klavye üzerinde boyanır; tablo tuşun
  konumunu (sıra / el) da söyler.
- 🎯 **Alıştırma modu** — yanlış yazdığın kelimeler ve zayıf harf içerenler daha sık çıkar.
- 🗂️ **Kelime havuzu ve geçmiş** — yanlış kelimeler, son testler ve rekor takibi (🏆).

## Kısayollar

| Ekran | Tuş | İşlev |
|-------|-----|-------|
| Menü | `Enter` / `L` / `D` / `M` | Başla / dil / süre / mod değiştir |
| Menü | `W` / `X` / `Q` | İstatistik / verileri sıfırla / çıkış |
| Test | `Boşluk` | Kelimeyi onayla (boşken yok sayılır) |
| Test | `Backspace` / `Tab` / `Esc` | Sil / yeniden başla / bitir ve sonucu gör |
| İstatistik | `1` `2` `3` / `L` / `Esc` | Sekme / dil / geri |

## Puanlama

- **WPM** = doğru karakter / 5 / geçen dakika. Süre dolmadan `Esc` ile bitirirsen gerçek geçen süre kullanılır.
- **Doğruluk** = doğru basılan tuş / toplam basılan tuş (düzeltilen hatalar da sayılır).
- Atlanan harfler, fazladan basılan karakterler ve yarım kalan son kelime hesaba katılır.

## Dosyalar

| Dosya | Görevi |
|-------|--------|
| `typing_test.py` | Giriş noktası |
| `ui.py` | Textual arayüzü: menü, test, sonuç, istatistik |
| `engine.py` | Terminalden bağımsız test mantığı (`Session`) |
| `storage.py` | İstatistik/havuz kaydı ve analiz (JSON) |
| `words.py` | Türkçe ve İngilizce kelime havuzları |
| `layouts.py` | F klavye / QWERTY konumları ve ekran klavyesi satırları |
| `tools/screenshots.py` | README görsellerini üretir |
| `tests/` | Birim testleri (`python -m unittest discover tests`) |
| `data/` | Kayıtlı istatistikler (otomatik oluşur, git'e eklenmez) |
