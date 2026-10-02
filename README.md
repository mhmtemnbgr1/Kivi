# ⌨️ Kivi — Terminalde Hızlı Yazma Testi

Retro/synthwave temalı, canlı WPM grafikli ve mekanik klavye sesli bir terminal yazma testi.

<p align="center">
  <img src="docs/menu.svg" width="48%"> <img src="docs/test.svg" width="48%">
</p>
<p align="center">
  <img src="docs/lesson.svg" width="48%"> <img src="docs/stats.svg" width="48%">
</p>

## Çalıştırma

```bash
pip install -r requirements.txt
python typing_test.py
```

Renkler siyah-beyazsa `--color 256` (veya `truecolor`, `16`) dene.

## Özellikler

- 🎹 Neon mekanik klavye (Türkçe Q / QWERTY): sıradaki tuş parlar, basılan tuş iner
- 🔊 Switch sesleri: mavi, kırmızı, kahverengi, siyah
- 📈 Canlı WPM, doğruluk ve süre çubuğu
- 🎯 7 mod: normal, alıştırma, zayıf harf drili, hata düzeltmeli, ölüm ☠, hız limiti ⚡, ders
- 🎓 Ders modu: kilitli tuşlar ve parmak renkleriyle harf harf öğrenme
- 🔥 Zayıf harf ısı haritası, harf çifti analizi, kelime havuzu, geçmiş ve rekorlar

## Kısayollar

| Ekran | Tuşlar |
|-------|--------|
| Menü | `Enter` başla · `L` dil · `D` süre · `M` mod · `T` limit · `E` ders · `F` parmak · `S` switch · `W` istatistik |
| Test | `Boşluk` onayla · `Tab` yeniden · `F2` switch · `Esc` bitir |

## Dosyalar

`typing_test.py` giriş · `ui.py` arayüz · `theme.py` tema/klavye · `engine.py` test mantığı ·
`storage.py` kayıt · `sound.py` sesler · `layouts.py` klavye/ders · `words.py` kelimeler ·
`tests/` testler · `tools/screenshots.py` görsel üretici

Testler: `python -m unittest discover tests`
