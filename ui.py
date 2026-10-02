# -*- coding: utf-8 -*-
"""Kivi — Textual tabanlı canlı terminal arayüzü.

Ekranlar: Ana menü -> Test (canlı WPM grafiği + ekran klavyesi) -> Sonuç,
İstatistikler (zayıf harf ısı haritası, kelime havuzu, geçmiş) ve sıfırlama onayı.
"""

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Sparkline, Static, TabbedContent, TabPane

import time

import engine
import layouts
import sound
import storage

DURATIONS = [15, 30, 60, 120]
LANGS = {"tr": "Türkçe · F klavye", "en": "English · QWERTY"}
MODES = {"normal": "Normal", "practice": "Alıştırma (zayıf noktalar)"}

# Renkler
OK, BAD, PENDING, ACCENT = "#7ee787", "#ff7b72", "#6e7681", "#58a6ff"
KEY_BG, KEY_FG = "#21262d", "#c9d1d9"


# ---------------------------------------------------------------------------
# Çizim yardımcıları
# ---------------------------------------------------------------------------
PLATE = "#161b22"   # klavye gövdesi (tuşların altındaki plaka)

# (yüz rengi, kenar/gölge rengi, yazı rengi)
CAP = ("#2d333b", "#1b1f24", "#adbac7")
CAP_NEXT = ("#1f6feb", "#0b3d91", "#ffffff")
CAP_WRONG = ("#da3633", "#7d1a18", "#ffffff")
CAP_DOWN_OK = ("#3fb950", "#3fb950", "#04260f")
CAP_DOWN_BAD = ("#f85149", "#f85149", "#ffffff")
HEAT_HI = ("#da3633", "#7d1a18", "#ffffff")
HEAT_MID = ("#f0883e", "#8a4a14", "#1b1f24")
HEAT_LO = ("#d29922", "#7a5710", "#1b1f24")


def render_keyboard(lang, nxt=None, wrong=None, heat=None, down=None, down_ok=True,
                    tall=True):
    """Mekanik klavye çizimi.

    nxt: sıradaki tuş (mavi)   wrong: yanlış basılan tuş (kırmızı)
    down: şu an basılı tuş (tuş aşağı iner)   heat: {harf: hata %} -> ısı haritası
    tall: 3 satırlık yüksek tuşlar (küçük terminalde 2 satırlık).
    """
    def colors_for(ch):
        if heat is not None:
            rate = heat.get(ch)
            if rate is None:
                return CAP
            return HEAT_HI if rate >= 25 else HEAT_MID if rate >= 12 else HEAT_LO
        if ch == down:
            return CAP_DOWN_OK if down_ok else CAP_DOWN_BAD
        if ch == wrong:
            return CAP_WRONG
        if ch == nxt:
            return CAP_NEXT
        return CAP

    rows = []   # her satır: [(etiket, genişlik, ch), ...]
    for r, row in enumerate(layouts.KEY_ROWS[lang]):
        keys = []
        for ch in row:
            label = "İ" if (ch == "i" and lang == "tr") else ch.upper()
            keys.append((label, 5, ch))
        rows.append((layouts.ROW_OFFSET[r] * 2, keys))
    space_label = "BOŞLUK" if lang == "tr" else "SPACE"
    rows.append((8, [(space_label.center(25), 25, " ")]))

    out = Text()
    for indent, keys in rows:
        lines = [Text(), Text(), Text()] if tall else [Text(), Text()]
        for line in lines:
            line.append(" " * indent, style=f"on {PLATE}")
        for label, w, ch in keys:
            face, edge, fg = colors_for(ch)
            pressed = ch == down and heat is None
            if tall:
                top, mid, bot = lines
                if pressed:   # tuş aşağıda: üst kenar kaybolur, yüz bir satır iner
                    top.append(" " * w, style=f"on {PLATE}")
                    mid.append("▄" * w, style=f"{face} on {PLATE}")
                    bot.append(label.center(w), style=f"bold {fg} on {face}")
                else:
                    top.append("▄" * w, style=f"{face} on {PLATE}")
                    mid.append(label.center(w), style=f"bold {fg} on {face}")
                    bot.append("▀" * w, style=f"{edge} on {PLATE}")
            else:
                mid, bot = lines
                if pressed:
                    mid.append(" " * w, style=f"on {PLATE}")
                    bot.append(label.center(w), style=f"bold {fg} on {face}")
                else:
                    mid.append(label.center(w), style=f"bold {fg} on {face}")
                    bot.append("▀" * w, style=f"{edge} on {PLATE}")
            for line in lines:
                line.append(" ", style=f"on {PLATE}")
        for line in lines:
            out.append_text(line)
            out.append("\n")
    out.rstrip()
    return out


def bar(frac, width=40):
    full = int(max(0.0, min(1.0, frac)) * width)
    t = Text()
    t.append("━" * full, style=ACCENT)
    t.append("━" * (width - full), style="#30363d")
    return t


def wrap_indices(words, width):
    lines, cur, cur_len = [], [], 0
    for i, w in enumerate(words):
        add = len(w) + (1 if cur else 0)
        if cur and cur_len + add > width:
            lines.append(cur)
            cur, cur_len, add = [], 0, len(w)
        cur.append(i)
        cur_len += add
    if cur:
        lines.append(cur)
    return lines


def render_word(target, typed, current):
    t = Text()
    for j in range(max(len(target), len(typed))):
        tch = target[j] if j < len(target) else ""
        uch = typed[j] if j < len(typed) else None
        if current and uch is None and j == len(typed):
            t.append(tch or " ", style="reverse")
        elif uch is None:
            t.append(tch, style=PENDING)
        elif j >= len(target):
            t.append(uch, style=f"{BAD} underline")
        elif uch == tch:
            t.append(tch, style=OK)
        else:
            t.append(tch, style=f"bold {BAD}")
    if current and len(typed) >= len(target):
        t.append(" ", style="reverse")
    return t


# ---------------------------------------------------------------------------
# Ana menü
# ---------------------------------------------------------------------------
class HomeScreen(Screen):
    BINDINGS = [
        ("enter", "start", "Başla"),
        ("l", "lang", "Dil"),
        ("d", "duration", "Süre"),
        ("m", "mode", "Mod"),
        ("s", "switch", "Switch"),
        ("w", "stats", "İstatistik"),
        ("x", "reset", "Sıfırla"),
        ("q", "app.quit", "Çık"),
    ]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="home"):
                yield Static(id="logo")
                yield Static(id="settings")
                yield Static(id="best")
                yield Static(id="help")

    def on_mount(self):
        self.refresh_view()

    def on_screen_resume(self):
        self.refresh_view()

    def refresh_view(self):
        app = self.app
        logo = Text(justify="center")
        logo.append("K I V I\n", style=f"bold {ACCENT}")
        logo.append("terminalde hızlı yazma antrenmanı", style=PENDING)
        self.query_one("#logo", Static).update(logo)

        s = Text()
        s.append("  Dil    ", style=PENDING)
        s.append(f"{LANGS[app.lang]}\n", style="bold")
        s.append("  Süre   ", style=PENDING)
        s.append(f"{app.duration} sn\n", style="bold")
        s.append("  Mod    ", style=PENDING)
        s.append(f"{MODES[app.mode]}\n", style="bold")
        s.append("  Switch ", style=PENDING)
        s.append(app.sound.label() if app.sound.available else "ses çalınamıyor", style="bold")
        self.query_one("#settings", Static).update(s)

        hist = storage.history(app.lang)
        best = Text(justify="center")
        if hist:
            top = max(h["wpm"] for h in hist)
            best.append(f"En yüksek: {top} WPM   ·   {len(hist)} test", style=OK)
        else:
            best.append("Henüz test yok — ilk testini başlat!", style=PENDING)
        self.query_one("#best", Static).update(best)

        h = Text(justify="center")
        h.append("Enter", style=f"bold {ACCENT}"); h.append(" başla   ")
        h.append("L", style=f"bold {ACCENT}"); h.append(" dil   ")
        h.append("D", style=f"bold {ACCENT}"); h.append(" süre   ")
        h.append("M", style=f"bold {ACCENT}"); h.append(" mod   ")
        h.append("S", style=f"bold {ACCENT}"); h.append(" switch sesi\n")
        h.append("W", style=f"bold {ACCENT}"); h.append(" istatistik   ")
        h.append("X", style=f"bold {ACCENT}"); h.append(" sıfırla   ")
        h.append("Q", style=f"bold {ACCENT}"); h.append(" çıkış")
        self.query_one("#help", Static).update(h)

    def action_start(self):
        self.app.push_screen(TestScreen())

    def action_lang(self):
        self.app.lang = "en" if self.app.lang == "tr" else "tr"
        self.refresh_view()

    def action_duration(self):
        i = DURATIONS.index(self.app.duration) if self.app.duration in DURATIONS else 0
        self.app.duration = DURATIONS[(i + 1) % len(DURATIONS)]
        self.refresh_view()

    def action_mode(self):
        self.app.mode = "practice" if self.app.mode == "normal" else "normal"
        self.refresh_view()

    def action_switch(self):
        self.app.sound.cycle()
        self.app.sound.play("key")
        self.refresh_view()

    def action_stats(self):
        self.app.push_screen(StatsScreen())

    def action_reset(self):
        def done(ok):
            if ok:
                storage.reset(self.app.lang)
                self.refresh_view()
        self.app.push_screen(ConfirmScreen(
            f"{LANGS[self.app.lang]} verileri silinsin mi?"), done)


class ConfirmScreen(ModalScreen):
    BINDINGS = [("e", "yes", "Evet"), ("y", "yes", "Evet"),
                ("h", "no", "Hayır"), ("n", "no", "Hayır"), ("escape", "no", "Vazgeç")]

    def __init__(self, question):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        t = Text(justify="center")
        t.append(self.question + "\n\n", style="bold")
        t.append("E", style=f"bold {BAD}"); t.append(" evet, sil     ")
        t.append("H", style=f"bold {OK}"); t.append(" hayır")
        yield Static(t, id="confirm")

    def action_yes(self):
        self.dismiss(True)

    def action_no(self):
        self.dismiss(False)


# ---------------------------------------------------------------------------
# Test ekranı
# ---------------------------------------------------------------------------
class TestScreen(Screen):
    """Canlı test: kelimeler, WPM grafiği ve sıradaki tuşu gösteren klavye."""

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="test"):
                yield Static(id="info")
                yield Static(id="timebar")
                yield Static(id="words")
                yield Sparkline([0], id="spark")
                yield Static(id="keyboard")
                yield Static(id="hint")

    def on_mount(self):
        self.new_session()
        self.set_interval(0.1, self.tick)

    def new_session(self):
        a = self.app
        self.session = engine.Session(a.lang, a.duration, a.mode)
        self._wrap_key = None
        self.down, self.down_ok, self.down_until = None, True, 0.0
        self.flash = ""
        self.query_one("#spark", Sparkline).data = [0]
        hint = Text(justify="center")
        hint.append("Esc", style=f"bold {ACCENT}"); hint.append(" bitir   ")
        hint.append("Tab", style=f"bold {ACCENT}"); hint.append(" yeniden başla   ")
        hint.append("Boşluk", style=f"bold {ACCENT}"); hint.append(" onayla   ")
        hint.append("F2", style=f"bold {ACCENT}"); hint.append(" switch sesi")
        self.query_one("#hint", Static).update(hint)
        self.redraw()

    def on_resize(self, event):
        self._wrap_key = None
        self.redraw()

    def tick(self):
        s = self.session
        if self.down and time.time() > self.down_until:
            self.down = None
        if s.started:
            s.sample()
            spark = self.query_one("#spark", Sparkline)
            if s.samples:
                spark.data = list(s.samples)
            if s.is_over():
                self.end()
                return
        self.redraw()

    def on_key(self, event):
        s = self.session
        key = event.key
        event.stop()
        event.prevent_default()
        snd = self.app.sound
        if key == "escape":
            self.end()
            return
        elif key == "tab":
            self.new_session()
        elif key == "f2":
            snd.cycle()
            snd.play("key")
            self.flash = f"Switch: {snd.label()}"
        elif key in ("space", "enter"):
            if s.commit():
                snd.play("space")
            self.press(" ", True)
        elif key == "backspace":
            s.backspace()
            snd.play("back")
        elif event.is_printable and event.character:
            ch = event.character
            expected = s.next_char()
            s.type_char(ch)
            snd.play("key")
            self.press(ch, ch == expected)
        else:
            return
        self.redraw()

    def press(self, ch, ok):
        """Basılan tuşu kısa süre 'aşağıda' göster."""
        self.down = {"İ": "i", "I": "ı"}.get(ch, ch.lower())
        self.down_ok = ok
        self.down_until = time.time() + 0.14

    def end(self):
        s = self.session
        before = storage.history(s.lang)
        prev_best = max((h["wpm"] for h in before), default=0)
        summary = s.finish()
        if summary is None:
            self.app.pop_screen()
            return
        summary["prev_best"] = prev_best
        self.app.switch_screen(ResultScreen(summary))

    def redraw(self):
        s = self.session
        left = int(s.remaining()) if s.started else s.duration
        info = Text(justify="center")
        info.append(f"{LANGS[s.lang]} · {MODES[s.mode]}\n", style=PENDING)
        info.append(f"{left}", style=f"bold {ACCENT}")
        info.append(" sn    ")
        info.append(f"{s.wpm()}", style=f"bold {OK}")
        info.append(" WPM    ")
        acc_style = OK if s.accuracy() >= 95 else ("#d29922" if s.accuracy() >= 85 else BAD)
        info.append(f"%{s.accuracy():g}", style=f"bold {acc_style}")
        info.append(" doğruluk    ")
        info.append(f"{s.correct_words()}", style="bold")
        info.append(" kelime")
        if self.flash:
            info.append(f"\n{self.flash}", style=ACCENT)
        self.query_one("#info", Static).update(info)

        frac = s.remaining() / s.duration if s.started else 1.0
        self.query_one("#timebar", Static).update(bar(frac, 60))
        if not s.started:
            self.query_one("#timebar", Static).update(
                Text("İlk tuşa bastığında süre başlar", style=PENDING, justify="center"))

        width = max(30, min(self.query_one("#words", Static).size.width or 80, 90) - 2)
        key = (len(s.words), width)
        if key != self._wrap_key:
            self._lines = wrap_indices(s.words, width)
            self._wrap_key = key
        cur_line = next((i for i, ln in enumerate(self._lines) if s.index in ln), 0)
        body = Text()
        for ln in self._lines[cur_line:cur_line + 3]:
            for n, wi in enumerate(ln):
                if n:
                    body.append(" ")
                if wi < s.index:
                    body.append_text(render_word(s.words[wi], s.typed[wi], False))
                elif wi == s.index:
                    body.append_text(render_word(s.words[wi], s.current, True))
                else:
                    body.append(s.words[wi], style=PENDING)
            body.append("\n")
        self.query_one("#words", Static).update(body)

        self.query_one("#keyboard", Static).update(
            render_keyboard(s.lang, nxt=s.next_char(), wrong=s.last_wrong,
                            down=self.down, down_ok=self.down_ok,
                            tall=self.size.height >= 40))


# ---------------------------------------------------------------------------
# Sonuç ekranı
# ---------------------------------------------------------------------------
class ResultScreen(Screen):
    BINDINGS = [("enter", "again", "Tekrar"), ("r", "again", "Tekrar"),
                ("w", "stats", "İstatistik"), ("escape", "menu", "Menü"),
                ("m", "menu", "Menü")]

    def __init__(self, summary):
        super().__init__()
        self.summary = summary

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="result"):
                yield Static(id="big")
                yield Sparkline(self.summary["samples"] or [0], id="rspark")
                yield Static(id="details")
                yield Static(id="rhelp")

    def on_mount(self):
        m = self.summary
        big = Text(justify="center")
        big.append(f"{m['wpm']}", style=f"bold {OK}")
        big.append(" WPM\n", style=PENDING)
        if m["wpm"] > m["prev_best"] and m["prev_best"]:
            big.append("🏆 Yeni rekor!", style="bold #d29922")
        elif not m["prev_best"]:
            big.append("İlk kaydın!", style="bold #d29922")
        else:
            big.append(f"En yüksek: {m['prev_best']} WPM", style=PENDING)
        self.query_one("#big", Static).update(big)

        d = Text(justify="center")
        d.append(f"Ham {m['raw_wpm']} WPM   ·   Doğruluk %{m['accuracy']:g}   ·   "
                 f"{m['correct_words']}/{m['total_words']} doğru kelime   ·   {m['duration']} sn\n\n")
        if m["mistyped_now"]:
            d.append("Yanlış kelimeler: ", style=BAD)
            d.append(", ".join(dict.fromkeys(m["mistyped_now"]))[:300])
        else:
            d.append("Hiç yanlış yok! 🎉", style=OK)
        self.query_one("#details", Static).update(d)

        h = Text(justify="center")
        h.append("Enter", style=f"bold {ACCENT}"); h.append(" tekrar   ")
        h.append("W", style=f"bold {ACCENT}"); h.append(" istatistik   ")
        h.append("Esc", style=f"bold {ACCENT}"); h.append(" menü")
        self.query_one("#rhelp", Static).update(h)

    def action_again(self):
        self.app.switch_screen(TestScreen())

    def action_stats(self):
        self.app.push_screen(StatsScreen())

    def action_menu(self):
        self.app.switch_screen(HomeScreen())


# ---------------------------------------------------------------------------
# İstatistik ekranı
# ---------------------------------------------------------------------------
class StatsScreen(Screen):
    BINDINGS = [("escape", "back", "Geri"), ("q", "back", "Geri"),
                ("l", "lang", "Dil"),
                ("1", "tab('weak')", "Zayıf harfler"),
                ("2", "tab('pool')", "Kelime havuzu"),
                ("3", "tab('hist')", "Geçmiş")]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="stats"):
                yield Static(id="stitle")
                with TabbedContent(id="tabs"):
                    with TabPane("1 · Zayıf harfler", id="weak"):
                        yield Static(id="heat")
                        yield DataTable(id="weak_t")
                    with TabPane("2 · Kelime havuzu", id="pool"):
                        yield DataTable(id="pool_t")
                    with TabPane("3 · Geçmiş", id="hist"):
                        yield Sparkline([0], id="hspark")
                        yield DataTable(id="hist_t")
                yield Static(id="shelp")

    def on_mount(self):
        for t, cols in (("weak_t", ("Harf", "Hata", "Deneme", "Oran", "Konum")),
                        ("pool_t", ("#", "Kelime", "Kaç kez")),
                        ("hist_t", ("Tarih", "Süre", "WPM", "Doğru kel.", "Doğruluk"))):
            tbl = self.query_one(f"#{t}", DataTable)
            tbl.add_columns(*cols)
            tbl.zebra_stripes = True
        self.load()

    def load(self):
        lang = self.app.lang
        self.query_one("#stitle", Static).update(
            Text(f"İstatistikler — {LANGS[lang]}", style=f"bold {ACCENT}", justify="center"))

        rows = storage.weak_letters(lang, top=12)
        t = self.query_one("#weak_t", DataTable)
        t.clear()
        for ch, err, total, rate, pos in rows:
            t.add_row(Text(ch, style=f"bold {BAD}"), str(err), str(total), f"%{rate:g}", pos)
        heat = {ch: rate for ch, _, _, rate, _ in storage.weak_letters(lang, top=99)}
        kb = render_keyboard(lang, heat=heat, tall=False)
        if not rows:
            kb = Text("Henüz yeterli veri yok. Birkaç test yap!", style=PENDING, justify="center")
        self.query_one("#heat", Static).update(kb)

        t = self.query_one("#pool_t", DataTable)
        t.clear()
        for i, (w, c) in enumerate(storage.mistyped_pool(lang), 1):
            t.add_row(str(i), w, f"{c}x")

        hist = storage.history(lang)
        t = self.query_one("#hist_t", DataTable)
        t.clear()
        for h in reversed(hist[-30:]):
            t.add_row(h["date"], f"{h['duration']} sn", str(h["wpm"]),
                      str(h["correct_words"]), f"%{h['accuracy']:g}")
        self.query_one("#hspark", Sparkline).data = [h["wpm"] for h in hist[-40:]] or [0]

        h = Text(justify="center")
        h.append("1/2/3", style=f"bold {ACCENT}"); h.append(" sekme   ")
        h.append("L", style=f"bold {ACCENT}"); h.append(" dil   ")
        h.append("Esc", style=f"bold {ACCENT}"); h.append(" geri")
        self.query_one("#shelp", Static).update(h)

    def action_tab(self, name):
        self.query_one("#tabs", TabbedContent).active = name

    def action_lang(self):
        self.app.lang = "en" if self.app.lang == "tr" else "tr"
        self.load()

    def action_back(self):
        self.app.pop_screen()


# ---------------------------------------------------------------------------
class KiviApp(App):
    TITLE = "Kivi"
    CSS = """
    Screen { background: #0d1117; align: center middle; }
    #home, #test, #result, #stats { width: 92%; max-width: 92; height: auto; }
    #logo { content-align: center middle; margin-bottom: 1; }
    #settings { width: auto; margin: 0 0 1 0; padding: 1 4; border: round #30363d; }
    #home Static, #test Static, #result Static { width: 100%; }
    #settings { width: auto; }
    #home { align-horizontal: center; }
    #best { margin: 1 0; text-align: center; }
    #help, #hint, #rhelp, #shelp { text-align: center; margin-top: 1; color: #8b949e; }
    #info { text-align: center; margin-bottom: 1; }
    #timebar { text-align: center; margin-bottom: 1; }
    #words { height: 5; padding: 1 2; border: round #30363d; }
    #spark { height: 3; margin: 1 0; }
    Sparkline > .sparkline--max-color { color: #7ee787; }
    Sparkline > .sparkline--min-color { color: #58a6ff; }
    #keyboard { height: auto; text-align: center; }
    #big { text-align: center; margin: 1 0; }
    #rspark { height: 4; margin: 1 0; }
    #details { text-align: center; }
    #heat { height: auto; margin: 1 0; text-align: center; }
    #weak_t, #pool_t, #hist_t { height: 14; }
    #hspark { height: 3; margin-bottom: 1; }
    ConfirmScreen { align: center middle; }
    #confirm { width: 50; height: auto; padding: 1 2; border: round #da3633;
               background: #161b22; }
    """

    def __init__(self):
        super().__init__()
        self.lang = "tr"
        self.duration = 30
        self.mode = "normal"
        self.sound = sound.KeySound("brown")

    def on_mount(self):
        self.push_screen(HomeScreen())


def run():
    KiviApp().run()
