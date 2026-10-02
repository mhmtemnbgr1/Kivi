# -*- coding: utf-8 -*-
"""İstatistik, yanlış kelime havuzu, ders ilerlemesi ve ayarların kalıcı (JSON) yönetimi.

Veri, `data/typing_data.json` dosyasında tutulur ve oturumlar arasında birikir.
Türkçe ('tr') ve İngilizce ('en') ayrı tutulur; ayarlar ortaktır.
"""

import json
import os

import layouts

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "typing_data.json")


def _empty_lang():
    return {
        "mistyped": {},       # yanlış yazılan kelime -> kaç kez
        "letter_errors": {},  # harf -> yanlış sayısı
        "letter_total": {},   # harf -> toplam yazma denemesi
        "history": [],        # geçmiş test sonuçları
        "bigrams": {},        # harf çifti -> {"n": adet, "ms": toplam süre, "err": hata}
        "lessons": {},        # ders no (str) -> en iyi WPM (geçilen dersler)
    }


def load():
    if not os.path.exists(DATA_FILE):
        data = {}
    else:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
    for lang in ("tr", "en"):
        data.setdefault(lang, _empty_lang())
        for key, default in _empty_lang().items():
            data[lang].setdefault(key, default)
    data.setdefault("settings", {})
    return data


def save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)           # yarım yazılmış dosya riskini önler


# --- Ayarlar ---------------------------------------------------------------
def get_settings():
    return dict(load()["settings"])


def save_settings(settings):
    data = load()
    data["settings"] = dict(settings)
    save(data)


# --- Test sonucu -----------------------------------------------------------
def record_session(lang, summary, letter_total, letter_errors, bigrams=None):
    """Biten testi kalıcı veriye işler (kelimeler, harfler, harf çiftleri, geçmiş)."""
    data = load()
    d = data[lang]
    for w in summary["mistyped_now"]:
        d["mistyped"][w] = d["mistyped"].get(w, 0) + 1
    for ch, n in letter_total.items():
        d["letter_total"][ch] = d["letter_total"].get(ch, 0) + n
    for ch, n in letter_errors.items():
        d["letter_errors"][ch] = d["letter_errors"].get(ch, 0) + n
    for pair, (n, ms, err) in (bigrams or {}).items():
        b = d["bigrams"].setdefault(pair, {"n": 0, "ms": 0.0, "err": 0})
        b["n"] += n
        b["ms"] = round(b["ms"] + ms, 1)
        b["err"] += err
    entry = {k: summary[k] for k in
             ("date", "duration", "wpm", "correct_words", "accuracy")}
    entry["mode"] = summary.get("mode", "normal")
    if summary.get("failed"):
        entry["failed"] = summary["failed"]
    d["history"].append(entry)
    d["history"] = d["history"][-100:]  # son 100 kayıt
    save(data)


def lesson_done(lang, level, wpm):
    data = load()
    key = str(level)
    best = data[lang]["lessons"].get(key, 0)
    data[lang]["lessons"][key] = max(best, wpm)
    save(data)


def lessons_done(lang):
    """Geçilen derslerin {ders_no: en_iyi_wpm} sözlüğü."""
    return {int(k): v for k, v in load()[lang]["lessons"].items()}


def unlocked_lesson(lang):
    """Oynanabilecek en yüksek ders numarası (geçilen + 1, en fazla ders sayısı)."""
    done = lessons_done(lang)
    top = max(done) if done else 0
    return min(top + 1, len(layouts.LESSONS[lang]))


# --- Analizler -------------------------------------------------------------
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
    rows.sort(key=lambda r: (r[3], r[1]), reverse=True)
    return rows[:top]


def weak_bigrams(lang, top=12, min_n=3):
    """Yavaş ve/veya hatalı harf çiftleri.

    Dönen liste: (çift, deneme, ortalama_ms, hata_yüzde); yavaş+hatalı olanlar üstte.
    """
    rows = []
    for pair, b in load()[lang]["bigrams"].items():
        if b["n"] < min_n:
            continue
        avg = b["ms"] / b["n"]
        rate = 100.0 * b["err"] / b["n"]
        rows.append((pair, b["n"], round(avg), round(rate, 1)))
    rows.sort(key=lambda r: r[2] * (1 + r[3] / 25.0), reverse=True)
    return rows[:top]


def mistyped_pool(lang):
    """Yanlış yazılan kelime havuzunu (kelime, sayı) listesi olarak döndürür."""
    data = load()[lang]
    return sorted(data["mistyped"].items(), key=lambda kv: kv[1], reverse=True)


def history(lang):
    return load()[lang]["history"]


def best_wpm(lang):
    """En yüksek WPM (elenerek biten testler sayılmaz)."""
    return max((h["wpm"] for h in history(lang) if not h.get("failed")), default=0)


def reset(lang):
    data = load()
    data[lang] = _empty_lang()
    save(data)
