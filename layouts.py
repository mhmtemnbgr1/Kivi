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
