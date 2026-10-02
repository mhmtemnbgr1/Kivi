# -*- coding: utf-8 -*-
"""Türkçe ve İngilizce kelime havuzları.

Türkçe liste, F klavyede sık kullanılan Türkçe harfleri (ç, ğ, ı, ö, ş, ü)
içeren yaygın kelimelerden oluşur.
"""

TURKISH_WORDS = [
    "ve", "bir", "bu", "için", "ile", "çok", "daha", "gibi", "kadar", "ama",
    "ben", "sen", "biz", "siz", "onlar", "şey", "zaman", "gün", "yıl", "insan",
    "hayat", "dünya", "ülke", "şehir", "sokak", "yol", "araba", "kapı", "pencere", "masa",
    "sandalye", "kalem", "kitap", "kağıt", "defter", "okul", "öğrenci", "öğretmen", "ders", "sınav",
    "bilgi", "bilgisayar", "klavye", "ekran", "telefon", "internet", "yazılım", "program", "sistem", "dosya",
    "su", "ateş", "hava", "toprak", "ağaç", "çiçek", "orman", "deniz", "göl", "nehir",
    "dağ", "güneş", "ay", "yıldız", "gökyüzü", "bulut", "yağmur", "kar", "rüzgar", "fırtına",
    "anne", "baba", "kardeş", "çocuk", "aile", "arkadaş", "komşu", "sevgi", "mutluluk", "üzüntü",
    "korku", "umut", "hayal", "düşünce", "duygu", "yürek", "kalp", "beyin", "göz", "kulak",
    "burun", "ağız", "diş", "dil", "el", "kol", "bacak", "ayak", "parmak", "saç",
    "yemek", "ekmek", "çorba", "pilav", "makarna", "et", "tavuk", "balık", "sebze", "meyve",
    "elma", "armut", "üzüm", "portakal", "muz", "çilek", "karpuz", "domates", "salatalık", "patates",
    "çay", "kahve", "süt", "peynir", "yumurta", "şeker", "tuz", "yağ", "un", "bal",
    "kırmızı", "mavi", "yeşil", "sarı", "beyaz", "siyah", "mor", "pembe", "turuncu", "gri",
    "büyük", "küçük", "uzun", "kısa", "geniş", "dar", "yüksek", "alçak", "hızlı", "yavaş",
    "güzel", "çirkin", "iyi", "kötü", "doğru", "yanlış", "kolay", "zor", "yeni", "eski",
    "sıcak", "soğuk", "ılık", "temiz", "kirli", "açık", "kapalı", "dolu", "boş", "ağır",
    "hafif", "sert", "yumuşak", "tatlı", "acı", "ekşi", "taze", "olgun", "genç", "yaşlı",
    "çalışmak", "yürümek", "koşmak", "gelmek", "gitmek", "görmek", "duymak", "konuşmak", "dinlemek", "yazmak",
    "okumak", "öğrenmek", "anlamak", "bilmek", "istemek", "sevmek", "gülmek", "ağlamak", "uyumak", "yemek",
    "içmek", "almak", "vermek", "yapmak", "etmek", "olmak", "bulmak", "kaybetmek", "açmak", "kapatmak",
    "başlamak", "bitirmek", "durmak", "beklemek", "düşünmek", "hatırlamak", "unutmak", "sormak", "cevaplamak", "söylemek",
    "para", "iş", "meslek", "şirket", "müdür", "çalışan", "toplantı", "proje", "görev", "hedef",
    "sağlık", "hastane", "doktor", "hemşire", "ilaç", "hastalık", "ağrı", "tedavi", "ameliyat", "muayene",
    "spor", "futbol", "basketbol", "voleybol", "yüzme", "koşu", "antrenman", "takım", "oyuncu", "maç",
    "müzik", "şarkı", "enstrüman", "gitar", "piyano", "keman", "davul", "flüt", "melodi", "ritim",
    "sanat", "resim", "heykel", "tiyatro", "sinema", "film", "roman", "şiir", "hikaye", "yazar",
    "gökçe", "çığlık", "öğle", "üşümek", "şoför", "çöp", "üçgen", "öğüt", "çığır",
]

ENGLISH_WORDS = [
    "the", "and", "for", "you", "that", "with", "this", "have", "from", "they",
    "will", "would", "there", "their", "what", "about", "which", "when", "make", "like",
    "time", "just", "know", "take", "people", "into", "year", "your", "good", "some",
    "could", "them", "other", "than", "then", "look", "only", "come", "over", "think",
    "also", "back", "after", "work", "first", "well", "even", "want", "because", "these",
    "give", "most", "very", "through", "much", "before", "here", "should", "such", "still",
    "world", "life", "house", "water", "light", "night", "story", "point", "little", "great",
    "small", "large", "young", "early", "high", "important", "different", "possible", "public", "human",
    "hand", "part", "child", "eye", "woman", "place", "week", "case", "point", "government",
    "company", "number", "group", "problem", "fact", "money", "story", "example", "family", "student",
    "school", "state", "country", "system", "program", "question", "during", "without", "again", "under",
    "between", "another", "around", "however", "become", "become", "family", "leave", "while", "mean",
    "keep", "start", "night", "begin", "seem", "help", "talk", "turn", "hand", "problem",
    "write", "provide", "read", "play", "move", "live", "believe", "hold", "happen", "must",
    "paper", "music", "power", "history", "table", "chair", "window", "picture", "garden", "market",
    "street", "morning", "summer", "winter", "friend", "father", "mother", "sister", "brother", "teacher",
    "doctor", "office", "letter", "answer", "reason", "moment", "future", "modern", "simple", "strong",
    "quick", "clear", "green", "black", "white", "brown", "happy", "quiet", "clean", "fresh",
    "space", "field", "river", "mountain", "forest", "ocean", "island", "bridge", "castle", "village",
    "travel", "journey", "adventure", "discovery", "science", "nature", "planet", "energy", "machine", "engine",
    "create", "design", "build", "change", "improve", "develop", "support", "manage", "control", "measure",
    "beautiful", "wonderful", "dangerous", "difficult", "necessary", "available", "particular", "national", "personal", "general",
]


def get_wordlist(lang):
    """Dil koduna göre temel kelime listesini döndürür ('tr' veya 'en')."""
    words = TURKISH_WORDS if lang == "tr" else ENGLISH_WORDS
    return list(dict.fromkeys(words))  # tekrarlayan kelimeleri ele
