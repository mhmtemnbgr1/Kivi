# -*- coding: utf-8 -*-
"""Klavye düzenleri: Türkçe Q klavye ve İngilizce QWERTY.

Her harfin hangi sırada (üst / orta / alt) ve hangi elle yazıldığını tutar.
Zayıf harf raporunda kullanıcıya "bu tuş nerede" bilgisini vermek için kullanılır.
"""

# --- Türkçe Q Klavye düzeni ---
#   üst:  q w e r t | y u ı o p ğ ü
#   orta: a s d f g | h j k l ş i
#   alt:  z x c v b | n m ö ç
TR_Q_LAYOUT = {
    # (satır, el)
    **{c: ("üst", "sol") for c in "qwert"},
    **{c: ("üst", "sağ") for c in "yuıopğü"},
    **{c: ("orta", "sol") for c in "asdfg"},
    **{c: ("orta", "sağ") for c in "hjklşi"},
    **{c: ("alt", "sol") for c in "zxcvb"},
    **{c: ("alt", "sağ") for c in "nmöç"},
}

# --- İngilizce QWERTY düzeni ---
QWERTY_LAYOUT = {
    **{c: ("üst", "sol") for c in "qwert"},
    **{c: ("üst", "sağ") for c in "yuiop"},
    **{c: ("orta", "sol") for c in "asdfg"},
    **{c: ("orta", "sağ") for c in "hjkl"},
    **{c: ("alt", "sol") for c in "zxcvb"},
    **{c: ("alt", "sağ") for c in "nm"},
}


def get_layout(lang):
    return TR_Q_LAYOUT if lang == "tr" else QWERTY_LAYOUT


def key_info(lang, ch):
    """Bir harfin klavye konumunu okunabilir metin olarak döndürür."""
    layout = get_layout(lang)
    info = layout.get(ch.lower())
    if not info:
        return "konum bilinmiyor"
    row, hand = info
    return f"{row} sıra, {hand} el"


# Ekrandaki klavye çizimi için fiziksel satırlar (soldan sağa).
KEY_ROWS = {
    "tr": ["qwertyuıopğü", "asdfghjklşi", "zxcvbnmöç.,"],
    "en": ["qwertyuiop", "asdfghjkl", "zxcvbnm,."],
}
ROW_OFFSET = [0, 1, 2]  # satırların yarım tuş kayması (gerçek klavye gibi)


# --- Parmak eşlemesi (standart on parmak yazım) ---------------------------
FINGER_NAMES = ["sol serçe", "sol yüzük", "sol orta", "sol işaret",
                "sağ işaret", "sağ orta", "sağ yüzük", "sağ serçe"]
_COL_FINGER = [0, 1, 2, 3, 3, 4, 4, 5, 6, 7, 7, 7]   # satırdaki sütuna göre parmak


def finger_of(lang, ch):
    """Harfin hangi parmakla basılacağı (0-7); bilinmiyorsa None."""
    for row in KEY_ROWS[lang]:
        if ch in row:
            return _COL_FINGER[row.index(ch)]
    return None


# --- Dersler: (başlık, bu derste öğrenilen yeni harfler) ------------------
# Her ders öncekileri kapsar (harfler birikir).
LESSONS = {
    "tr": [
        ("Ana sıra · sol el", "asdfg"),
        ("Ana sıra · sağ el", "hjkli"),
        ("Üst sıra · sol el", "qwert"),
        ("Üst sıra · sağ el", "yuıop"),
        ("Alt sıra", "zxcvbnm"),
        ("Türkçe harfler", "ğüşöç"),
    ],
    "en": [
        ("Home row · left hand", "asdfg"),
        ("Home row · right hand", "hjkl"),
        ("Top row · left hand", "qwert"),
        ("Top row · right hand", "yuiop"),
        ("Bottom row", "zxcvbnm"),
    ],
}


def lesson_letters(lang, level):
    """(izinli harfler, bu dersin odak harfleri)"""
    lessons = LESSONS[lang]
    level = max(1, min(level, len(lessons)))
    allowed = "".join(l[1] for l in lessons[:level])
    return set(allowed), lessons[level - 1][1]
