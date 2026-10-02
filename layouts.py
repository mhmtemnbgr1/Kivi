# -*- coding: utf-8 -*-
"""Klavye düzenleri: Türkçe F klavye ve İngilizce QWERTY.

Her harfin hangi sırada (üst / orta / alt) ve hangi elle yazıldığını tutar.
Zayıf harf raporunda kullanıcıya "bu tuş nerede" bilgisini vermek için kullanılır.
"""

# --- Türkçe F Klavye düzeni (harf satırları) ---
#   üst:  f g ğ ı o | d r n h p q w
#   orta: u i e a ü | t k m l y ş
#   alt:  j ö v c ç | z s b
F_LAYOUT = {
    # (satır, el)
    **{c: ("üst", "sol") for c in "fgğıo"},
    **{c: ("üst", "sağ") for c in "drnhpqw"},
    **{c: ("orta", "sol") for c in "uieaü"},
    **{c: ("orta", "sağ") for c in "tkmlyş"},
    **{c: ("alt", "sol") for c in "jövcç"},
    **{c: ("alt", "sağ") for c in "zsb"},
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
    return F_LAYOUT if lang == "tr" else QWERTY_LAYOUT


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
    "tr": ["fgğıodrnhpqw", "uieaütkmlyş", "jövcçzsb.,"],
    "en": ["qwertyuiop", "asdfghjkl", "zxcvbnm,."],
}
ROW_OFFSET = [0, 1, 2]  # satırların yarım tuş kayması (gerçek klavye gibi)
