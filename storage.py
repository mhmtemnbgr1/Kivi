# -*- coding: utf-8 -*-
"""İstatistik ve yanlış kelime havuzunun kalıcı (JSON) yönetimi + analiz.

Veri, çalıştırılan dizindeki `data/typing_data.json` dosyasında tutulur ve
oturumlar arasında birikir. Türkçe ('tr') ve İngilizce ('en') ayrı tutulur.
"""

import json
import os
from datetime import datetime

import layouts

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "typing_data.json")


def _empty_lang():
    return {
        "mistyped": {},       # yanlış yazılan kelime -> kaç kez
        "letter_errors": {},  # harf -> yanlış sayısı
        "letter_total": {},   # harf -> toplam yazma denemesi
        "history": [],        # geçmiş test sonuçları
    }


def load():
    if not os.path.exists(DATA_FILE):
        return {"tr": _empty_lang(), "en": _empty_lang()}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"tr": _empty_lang(), "en": _empty_lang()}
    for lang in ("tr", "en"):
        data.setdefault(lang, _empty_lang())
        for key in _empty_lang():
            data[lang].setdefault(key, _empty_lang()[key])
    return data


def save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_result(lang, target_words, typed_words, duration):
    """Tamamlanan bir testi işler: istatistikleri günceller ve özet döndürür.

    `typed_words` boşlukla onaylanmış (commit edilmiş) kelimelerdir.
    """
    data = load()
    d = data[lang]

    correct_chars = 0        # doğru yazılan karakter sayısı
    typed_chars = 0          # kullanıcının bastığı toplam karakter
    correct_words = 0        # tamamen doğru yazılan kelime
    mistyped_now = []        # bu testte yanlış yazılan kelimeler

    for i, typed in enumerate(typed_words):
        if i >= len(target_words):
            break
        target = target_words[i]
        typed_chars += len(typed)

        # Karakter bazında karşılaştırma
        for j, tch in enumerate(target):
            if tch.isspace():
                continue
            d["letter_total"][tch] = d["letter_total"].get(tch, 0) + 1
            if j < len(typed) and typed[j] == tch:
                correct_chars += 1
            else:
                d["letter_errors"][tch] = d["letter_errors"].get(tch, 0) + 1

        if typed == target:
            correct_words += 1
        else:
            d["mistyped"][target] = d["mistyped"].get(target, 0) + 1
            mistyped_now.append(target)

    minutes = duration / 60.0 if duration > 0 else 1 / 60.0
    wpm = round((correct_chars / 5.0) / minutes)
    raw_wpm = round((typed_chars / 5.0) / minutes)
    accuracy = round(100.0 * correct_chars / typed_chars, 1) if typed_chars else 0.0

    summary = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "lang": lang,
        "duration": duration,
        "wpm": wpm,
        "raw_wpm": raw_wpm,
        "correct_words": correct_words,
        "total_words": len(typed_words),
        "accuracy": accuracy,
        "mistyped_now": mistyped_now,
    }

    d["history"].append({k: summary[k] for k in
                         ("date", "duration", "wpm", "correct_words", "accuracy")})
    d["history"] = d["history"][-100:]  # son 100 kayıt

    save(data)
    return summary


def weak_letters(lang, top=10, min_total=3):
    """En çok hata yapılan harfleri hata oranıyla birlikte döndürür.

    Dönen liste: (harf, hata_sayısı, toplam, oran_yüzde, konum_metni)
    """
    data = load()[lang]
    errors = data["letter_errors"]
    totals = data["letter_total"]
    rows = []
    for ch, err in errors.items():
        total = totals.get(ch, 0)
        if total < min_total:
            continue
        rate = 100.0 * err / total if total else 0.0
        rows.append((ch, err, total, round(rate, 1), layouts.key_info(lang, ch)))
    # Önce hata oranı, sonra hata sayısı
    rows.sort(key=lambda r: (r[3], r[1]), reverse=True)
    return rows[:top]


def mistyped_pool(lang):
    """Yanlış yazılan kelime havuzunu (kelime, sayı) listesi olarak döndürür."""
    data = load()[lang]
    pool = sorted(data["mistyped"].items(), key=lambda kv: kv[1], reverse=True)
    return pool


def history(lang):
    return load()[lang]["history"]


def reset(lang):
    data = load()
    data[lang] = _empty_lang()
    save(data)
