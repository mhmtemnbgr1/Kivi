# -*- coding: utf-8 -*-
"""Kivi — retro/synthwave temalı, animasyonlu Textual arayüzü.

Ekranlar: Ana menü -> Test (canlı WPM grafiği + neon mekanik klavye) -> Sonuç,
İstatistikler (zayıf harfler, kelime havuzu, geçmiş, harf çiftleri) ve sıfırlama onayı.
"""

import time

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Sparkline, Static, TabbedContent, TabPane

import engine
import layouts
import sound
import storage
from theme import (BG, CYAN, DIM, FAINT, GREEN, ORANGE, PINK, PURPLE, RAINBOW, RED, SUNSET,
                   TEXT, YELLOW, big, chip, finger_legend, gradient_text, hints,
                   render_keyboard, smooth_bar, wave)

DURATIONS = [15, 30, 60, 120]
LIMITS = [20, 30, 40, 50, 60, 80]
LANGS = {"tr": "Türkçe · Q klavye", "en": "English · QWERTY"}
MODE_INFO = {                       # ad, kısa açıklama
    "normal": ("Normal", "rastgele kelimeler"),
    "practice": ("Alıştırma", "yanlış kelimeler ve zayıf harfler sık çıkar"),
    "drill": ("Zayıf harf drili", "30 sn · zayıf harf ve harf çiftleri"),
    "strict": ("Hata düzeltmeli", "yanlış kelimeyi düzeltmeden geçemezsin"),
    "sudden": ("Ölüm modu", "ilk hatada oyun biter"),
    "speed": ("Hız limiti", "hızın limitin altına düşerse oyun biter"),
    "lesson": ("Ders", "harf harf öğren, dersi geçince yenisi açılır"),
}
FPS = 1 / 20


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------
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


def render_word(target, typed, current, blink):
    t = Text()
    for j in range(max(len(target), len(typed))):
        tch = target[j] if j < len(target) else ""
        uch = typed[j] if j < len(typed) else None
        if current and uch is None and j == len(typed):
            t.append(tch or " ", style=f"bold {BG} on {CYAN}" if blink else f"bold {CYAN} underline")
        elif uch is None:
            t.append(tch, style=TEXT if current else FAINT)      # aktif kelime daha parlak
        elif j >= len(target):
            t.append(uch, style=f"{RED} underline")
        elif uch == tch:
            t.append(tch, style=GREEN)
        else:
            t.append(tch, style=f"bold {RED}")
    if current and len(typed) >= len(target):
        t.append(" ", style=f"on {CYAN}" if blink else "")
    return t


def label_row(name, value, color=CYAN):
    t = Text()
    t.append(f"  {name:<8}", style=DIM)
    t.append("◂ ", style=FAINT)
    t.append(value, style=f"bold {color}")
    t.append(" ▸", style=FAINT)
    return t


class Animated(Screen):
    """Her ekranın 20 FPS çalışan animasyon zamanlayıcısı."""

    def on_mount(self):
        self.t0 = time.time()
        self.set_interval(FPS, self._frame)

    @property
    def t(self):
        return time.time() - self.t0

    def _frame(self):
        self.animate(self.t)

    def animate(self, t):
        pass


# ---------------------------------------------------------------------------
# Ana menü
# ---------------------------------------------------------------------------
class HomeScreen(Animated):
    BINDINGS = [
        ("enter", "start", "Başla"),
        ("l", "lang", "Dil"),
        ("d", "duration", "Süre"),
        ("m", "mode", "Mod"),
        ("t", "limit", "Limit"),
        ("e", "lesson", "Ders"),
        ("f", "fingers", "Parmak"),
        ("s", "switch", "Switch"),
        ("w", "stats", "İstatistik"),
        ("x", "reset", "Sıfırla"),
        ("q", "app.quit", "Çık"),
    ]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="home"):
                yield Static(id="logo")
                yield Static(id="tag")
                yield Static(id="wave")
                yield Static(id="settings")
                yield Static(id="cta")
                yield Static(id="best")
                yield Static(id="help")

    def on_mount(self):
        super().on_mount()
        self.query_one("#settings").border_title = "◤ AYARLAR ◢"
        self.query_one("#tag", Static).update(
            Text("▓▒░  TERMİNALDE HIZLI YAZMA ANTRENMANI  ░▒▓", style=DIM, justify="center"))
        self.refresh_view()
        self.animate(0)

    def on_screen_resume(self):
        self.refresh_view()

    def animate(self, t):
        self.query_one("#logo", Static).update(big("KIVI", RAINBOW, phase=t * 0.18))
        self.query_one("#wave", Static).update(wave(64, t))
        blink = int(t * 1.6) % 2 == 0
        cta = Text(justify="center")
        cta.append("▶  ENTER'A BAS  ◀" if blink else "                ",
                   style=f"bold {YELLOW}")
        self.query_one("#cta", Static).update(cta)

    def refresh_view(self):
        app = self.app
        mode_name, mode_desc = MODE_INFO[app.mode]
        dur = "30 saniye (sabit)" if app.mode == "drill" else f"{app.duration} saniye"
        s = Text()
        s.append_text(label_row("DİL", LANGS[app.lang], CYAN))
        s.append("\n")
        s.append_text(label_row("SÜRE", dur, YELLOW))
        s.append("\n")
        s.append_text(label_row("MOD", mode_name, PINK))
        s.append(f"\n  {'':<8}  {mode_desc}", style=FAINT)
        if app.mode == "speed":
            s.append("\n")
            s.append_text(label_row("LİMİT", f"{app.limit} WPM", RED))
        if app.mode == "lesson":
            n = app.lesson_level()
            title, letters = layouts.LESSONS[app.lang][n - 1]
            done = n in storage.lessons_done(app.lang)
            s.append("\n")
            s.append_text(label_row(
                "DERS", f"{n}/{len(layouts.LESSONS[app.lang])} · {title}"
                        f"  [{letters}]{' ✔' if done else ''}", ORANGE))
        s.append("\n")
        s.append_text(label_row(
            "SWITCH", app.sound.label() if app.sound.available else "ses çalınamıyor", GREEN))
        s.append("\n")
        s.append_text(label_row("PARMAK", "renkli" if app.fingers else "kapalı", PURPLE))
        self.query_one("#settings", Static).update(s)

        best_wpm = storage.best_wpm(app.lang)
        hist = storage.history(app.lang)
        best = Text(justify="center")
        if hist:
            best.append("★ EN YÜKSEK ", style=DIM)
            best.append(f"{best_wpm} WPM", style=f"bold {YELLOW}")
            best.append(f"   ·   {len(hist)} test", style=DIM)
        else:
            best.append("henüz skor yok — ilk rekoru sen kır!", style=DIM)
        self.query_one("#best", Static).update(best)

        self.query_one("#help", Static).update(hints([
            ("L", "dil"), ("D", "süre"), ("M", "mod"), ("T", "limit"), ("E", "ders"),
            ("F", "parmak"), ("S", "switch"), ("W", "istatistik"), ("X", "sıfırla"),
            ("Q", "çık")], PURPLE))

    def action_start(self):
        self.app.push_screen(TestScreen())

    def action_lang(self):
        self.app.lang = "en" if self.app.lang == "tr" else "tr"
        self.app.save_settings()
        self.refresh_view()

    def action_duration(self):
        i = DURATIONS.index(self.app.duration) if self.app.duration in DURATIONS else 0
        self.app.duration = DURATIONS[(i + 1) % len(DURATIONS)]
        self.app.save_settings()
        self.refresh_view()

    def action_mode(self):
        order = engine.MODE_ORDER
        self.app.mode = order[(order.index(self.app.mode) + 1) % len(order)]
        self.app.save_settings()
        self.refresh_view()

    def action_limit(self):
        i = LIMITS.index(self.app.limit) if self.app.limit in LIMITS else 0
        self.app.limit = LIMITS[(i + 1) % len(LIMITS)]
        self.app.save_settings()
        self.refresh_view()

    def action_lesson(self):
        top = storage.unlocked_lesson(self.app.lang)
        n = self.app.lesson_level()
        self.app.lesson = n + 1 if n < top else 1       # açık dersler arasında döner
        self.app.save_settings()
        self.refresh_view()

    def action_fingers(self):
        self.app.fingers = not self.app.fingers
        self.app.save_settings()
        self.refresh_view()

    def action_switch(self):
        self.app.sound.cycle()
        self.app.sound.play("key")
        self.app.save_settings()
        self.refresh_view()

    def action_stats(self):
        self.app.push_screen(StatsScreen())

    def action_reset(self):
        def done(ok):
            if ok:
                storage.reset(self.app.lang)
                self.refresh_view()
        self.app.push_screen(ConfirmScreen(
            f"{LANGS[self.app.lang]} verileri (ders ilerlemesi dahil) silinsin mi?"), done)


class ConfirmScreen(ModalScreen):
    BINDINGS = [("e", "yes", "Evet"), ("y", "yes", "Evet"),
                ("h", "no", "Hayır"), ("n", "no", "Hayır"), ("escape", "no", "Vazgeç")]

    def __init__(self, question):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        t = Text(justify="center")
        t.append("⚠  ", style=f"bold {YELLOW}")
        t.append(self.question + "\n\n", style=f"bold {TEXT}")
        t.append_text(chip("E", "evet, sil", RED))
        t.append_text(chip("H", "hayır", GREEN))
        yield Static(t, id="confirm")

    def action_yes(self):
        self.dismiss(True)

    def action_no(self):
        self.dismiss(False)


# ---------------------------------------------------------------------------
# Test ekranı
# ---------------------------------------------------------------------------
class TestScreen(Animated):
    """Canlı test: kelimeler, WPM grafiği ve sıradaki tuşu gösteren neon klavye."""

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
        super().on_mount()
        self.query_one("#words").border_title = "◤ YAZ ◢"
        self.query_one("#spark").border_title = "canlı WPM"
        self.new_session()

    def new_session(self):
        a = self.app
        self.lesson = a.lesson_level()
        self.session = engine.Session(a.lang, a.duration, a.mode,
                                      limit=a.limit, lesson=self.lesson)
        self.show_fingers = a.fingers or a.mode == "lesson"
        self.allowed = None
        if a.mode == "lesson":
            letters, _ = layouts.lesson_letters(a.lang, self.lesson)
            self.allowed = letters
        self._wrap_key = None
        self.pressed = {}
        self.flash, self.flash_until, self.flash_color = "", 0.0, GREEN
        self.query_one("#spark", Sparkline).data = [0]
        self.query_one("#hint", Static).update(hints([
            ("ESC", "bitir"), ("TAB", "yeniden"), ("SPACE", "onayla"),
            ("F2", "switch sesi")], PURPLE))
        self.redraw()

    def on_resize(self, event):
        self._wrap_key = None

    def say(self, msg, color=GREEN, secs=2.0):
        self.flash, self.flash_color, self.flash_until = msg, color, time.time() + secs

    def animate(self, t):
        s = self.session
        now = time.time()
        self.pressed = {k: v for k, v in self.pressed.items() if now - v[0] < 0.5}
        if self.flash and now > self.flash_until:
            self.flash = ""
        if s.started:
            s.sample()
            if s.samples:
                self.query_one("#spark", Sparkline).data = list(s.samples)
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
            self.app.save_settings()
            self.say(f"♪ switch: {snd.label()}")
        elif key in ("space", "enter"):
            if s.commit():
                snd.play("space")
                self.press(" ", True)
            elif s.rejected:
                snd.play("back")
                self.say("✗ önce kelimeyi düzelt", RED, 1.2)
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
        if s.failed:
            self.end()
            return
        self.redraw()

    def press(self, ch, ok):
        """Basılan tuş aşağı iner ve yavaşça söner."""
        self.pressed[{"İ": "i", "I": "ı"}.get(ch, ch.lower())] = (time.time(), ok)

    def end(self):
        s = self.session
        prev_best = storage.best_wpm(s.lang)
        summary = s.finish()
        if summary is None:
            self.app.pop_screen()
            return
        summary["prev_best"] = prev_best
        self.app.switch_screen(ResultScreen(summary))

    def subtitle(self):
        s = self.session
        name = MODE_INFO[s.mode][0]
        if s.mode == "lesson":
            title, letters = layouts.LESSONS[s.lang][self.lesson - 1]
            return f"DERS {self.lesson} · {title} · odak: {' '.join(letters)}"
        if s.mode == "sudden":
            return f"{LANGS[s.lang]} · ☠ {name} — tek hata ve bitti"
        if s.mode == "speed":
            return f"{LANGS[s.lang]} · ⚡ {name} — en az {s.limit} WPM"
        if s.mode == "strict":
            return f"{LANGS[s.lang]} · ✎ {name}"
        return f"{LANGS[s.lang]} · {name}"

    def redraw(self):
        s = self.session
        t = time.time()
        left = int(s.remaining()) if s.started else s.duration

        acc = s.accuracy()
        acc_color = GREEN if acc >= 95 else YELLOW if acc >= 85 else RED
        info = Text(justify="center")
        info.append(f"{self.subtitle()}\n", style=FAINT)
        info.append(f"⏱ {left}s", style=f"bold {CYAN}")
        info.append("   ")
        info.append(f"⚡ {s.wpm()} WPM", style=f"bold {YELLOW}")
        info.append("   ")
        info.append(f"◎ %{acc:g}", style=f"bold {acc_color}")
        info.append("   ")
        info.append(f"✔ {s.correct_words()}", style=f"bold {PINK}")
        if s.mode == "speed" and s.started:
            cur = s.speed_now()
            if s.elapsed() < engine.GRACE:
                info.append(f"   ⏳ tolerans {int(engine.GRACE - s.elapsed()) + 1}s", style=DIM)
            elif cur is not None:
                danger = cur < s.limit + 5
                info.append(f"   son 5sn: {cur}",
                            style=f"bold {RED}" if danger and int(t * 4) % 2 == 0
                            else f"bold {RED if danger else GREEN}")
        info.append("\n")
        info.append(self.flash, style=self.flash_color)
        self.query_one("#info", Static).update(info)

        if s.started:
            self.query_one("#timebar", Static).update(smooth_bar(s.remaining() / s.duration, 64))
        else:
            blink = int(t * 2) % 2 == 0
            self.query_one("#timebar", Static).update(Text(
                "İlk tuşa bastığında süre başlar" if blink else "",
                style=DIM, justify="center"))

        width = self.query_one("#words", Static).size.width or 80
        width = max(30, min(width, 90))
        key = (len(s.words), width)
        if key != self._wrap_key:
            self._lines = wrap_indices(s.words, width)
            self._wrap_key = key
        cur_line = next((i for i, ln in enumerate(self._lines) if s.index in ln), 0)
        blink = int(t * 2.5) % 2 == 0
        body = Text()
        for ln in self._lines[cur_line:cur_line + 3]:
            for n, wi in enumerate(ln):
                if n:
                    body.append(" ")
                if wi < s.index:
                    body.append_text(render_word(s.words[wi], s.typed[wi], False, blink))
                elif wi == s.index:
                    body.append_text(render_word(s.words[wi], s.current, True, blink))
                else:
                    body.append(s.words[wi], style=FAINT)
            body.append("\n")
        self.query_one("#words", Static).update(body)

        kb = render_keyboard(
            s.lang, t=t, nxt=s.next_char(), wrong=s.last_wrong, pressed=self.pressed,
            tall=self.size.height >= 44, fingers=self.show_fingers, allowed=self.allowed)
        if self.show_fingers:
            kb.append("\n")
            kb.append_text(finger_legend())
        self.query_one("#keyboard", Static).update(kb)


# ---------------------------------------------------------------------------
# Sonuç ekranı
# ---------------------------------------------------------------------------
class ResultScreen(Animated):
    BINDINGS = [("enter", "again", "Tekrar"), ("r", "again", "Tekrar"),
                ("w", "stats", "İstatistik"), ("escape", "menu", "Menü"),
                ("m", "menu", "Menü")]

    def __init__(self, summary):
        super().__init__()
        self.summary = summary

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="result"):
                yield Static(id="banner")
                yield Static(id="big")
                yield Static(id="unit")
                yield Sparkline(self.summary["samples"] or [0], id="rspark")
                yield Static(id="details")
                yield Static(id="rhelp")

    def on_mount(self):
        super().on_mount()
        m = self.summary
        app = self.app
        self.query_one("#unit", Static).update(
            Text(f"W P M   ·   {MODE_INFO[m['mode']][0]}", style=DIM, justify="center"))

        # Ders geçildiyse bir sonraki ders açılır ve otomatik seçilir
        self.lesson_msg = None
        if m["mode"] == "lesson":
            total = len(layouts.LESSONS[m["lang"]])
            if m["lesson_passed"]:
                if m["lesson"] < total:
                    app.lesson = m["lesson"] + 1
                    app.save_settings()
                    self.lesson_msg = ("✔ DERS GEÇİLDİ — sonraki ders açıldı", GREEN)
                else:
                    self.lesson_msg = ("✔ TÜM DERSLER TAMAM — tebrikler!", GREEN)
            else:
                self.lesson_msg = (f"✗ geçmek için en az %{engine.PASS_ACCURACY:g} doğruluk ve "
                                   f"{engine.PASS_WORDS} doğru kelime gerek", ORANGE)

        d = Text(justify="center")
        for name, val, color in (("HAM", f"{m['raw_wpm']}", CYAN),
                                 ("DOĞRULUK", f"%{m['accuracy']:g}", GREEN),
                                 ("KELİME", f"{m['correct_words']}/{m['total_words']}", PINK),
                                 ("SÜRE", f"{m['duration']}s", YELLOW)):
            d.append(f" {name} ", style=f"bold {BG} on {color}")
            d.append(f" {val}    ", style=f"bold {color}")
        d.append("\n\n")
        if m["mistyped_now"]:
            d.append("yanlışlar: ", style=RED)
            d.append(", ".join(dict.fromkeys(m["mistyped_now"]))[:300], style=TEXT)
        else:
            d.append("★ hiç yanlış yok! ★", style=f"bold {GREEN}")
        self.query_one("#details", Static).update(d)
        self.query_one("#rhelp", Static).update(hints([
            ("ENTER", "tekrar"), ("W", "istatistik"), ("ESC", "menü")], PURPLE))
        self.animate(0)

    def animate(self, t):
        m = self.summary
        blink = int(t * 2.5) % 2 == 0
        self.query_one("#big", Static).update(big(str(m["wpm"]), SUNSET, phase=t * 0.15, scale=2))
        banner = Text(justify="center")
        if m["failed"] == "error":
            banner.append("☠  ELENDİN — hata yaptın  ☠" if blink else "   ELENDİN — hata yaptın   ",
                          style=f"bold {RED}")
        elif m["failed"] == "speed":
            banner.append(f"⚡ HIZ DÜŞTÜ — limit {m['limit']} WPM ⚡" if blink
                          else f"   HIZ DÜŞTÜ — limit {m['limit']} WPM   ", style=f"bold {RED}")
        elif self.lesson_msg:
            banner.append(self.lesson_msg[0], style=f"bold {self.lesson_msg[1]}")
        elif m["wpm"] > m["prev_best"] and m["prev_best"]:
            banner.append("★ ★ ★  YENİ REKOR  ★ ★ ★" if blink
                          else "☆ ☆ ☆  YENİ REKOR  ☆ ☆ ☆", style=f"bold {YELLOW}")
        elif not m["prev_best"]:
            banner.append("★  İLK SKORUN  ★", style=f"bold {YELLOW}")
        else:
            banner.append(f"en yüksek: {m['prev_best']} WPM", style=DIM)
        self.query_one("#banner", Static).update(banner)

    def action_again(self):
        self.app.switch_screen(TestScreen())

    def action_stats(self):
        self.app.push_screen(StatsScreen())

    def action_menu(self):
        self.app.switch_screen(HomeScreen())


# ---------------------------------------------------------------------------
# İstatistik ekranı
# ---------------------------------------------------------------------------
class StatsScreen(Animated):
    BINDINGS = [("escape", "back", "Geri"), ("q", "back", "Geri"),
                ("l", "lang", "Dil"),
                ("1", "tab('weak')", "Zayıf harfler"),
                ("2", "tab('pool')", "Kelime havuzu"),
                ("3", "tab('hist')", "Geçmiş"),
                ("4", "tab('pairs')", "Harf çiftleri")]

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
                    with TabPane("4 · Harf çiftleri", id="pairs"):
                        yield Static(id="pairs_info")
                        yield DataTable(id="pairs_t")
                yield Static(id="shelp")

    def on_mount(self):
        super().on_mount()
        for t, cols in (("weak_t", ("Harf", "Hata", "Deneme", "Oran", "Konum")),
                        ("pool_t", ("#", "Kelime", "Kaç kez")),
                        ("hist_t", ("Tarih", "Mod", "Süre", "WPM", "Doğru kel.", "Doğruluk")),
                        ("pairs_t", ("Çift", "Deneme", "Ort. süre", "Hata", "Konum"))):
            tbl = self.query_one(f"#{t}", DataTable)
            tbl.add_columns(*cols)
            tbl.zebra_stripes = True
        self.query_one("#hspark").border_title = "WPM gelişimi"
        self.load()

    def animate(self, t):
        self.query_one("#stitle", Static).update(gradient_text(
            f"▓▒░  İSTATİSTİKLER · {LANGS[self.app.lang]}  ░▒▓", RAINBOW, t * 0.15))

    def load(self):
        lang = self.app.lang
        rows = storage.weak_letters(lang, top=12)
        t = self.query_one("#weak_t", DataTable)
        t.clear()
        for ch, err, total, rate, pos in rows:
            color = RED if rate >= 25 else ORANGE if rate >= 12 else YELLOW
            t.add_row(Text(ch, style=f"bold {color}"), str(err), str(total),
                      Text(f"%{rate:g}", style=color), pos)
        heat = {ch: rate for ch, _, _, rate, _ in storage.weak_letters(lang, top=99)}
        if rows:
            kb = render_keyboard(lang, heat=heat, tall=False)
        else:
            kb = Text("henüz yeterli veri yok — birkaç test yap!", style=DIM, justify="center")
        self.query_one("#heat", Static).update(kb)

        t = self.query_one("#pool_t", DataTable)
        t.clear()
        for i, (w, c) in enumerate(storage.mistyped_pool(lang), 1):
            t.add_row(str(i), w, f"{c}x")

        hist = storage.history(lang)
        t = self.query_one("#hist_t", DataTable)
        t.clear()
        for h in reversed(hist[-30:]):
            mode = MODE_INFO.get(h.get("mode", "normal"), MODE_INFO["normal"])[0]
            if h.get("failed"):
                mode = Text(f"☠ {mode}", style=RED)
            t.add_row(h["date"], mode, f"{h['duration']} sn",
                      Text(str(h["wpm"]), style=f"bold {YELLOW}"),
                      str(h["correct_words"]), f"%{h['accuracy']:g}")
        ok = [h["wpm"] for h in hist if not h.get("failed")]
        self.query_one("#hspark", Sparkline).data = ok[-40:] or [0]

        pairs = storage.weak_bigrams(lang, top=14)
        t = self.query_one("#pairs_t", DataTable)
        t.clear()
        for pair, n, avg, rate in pairs:
            color = RED if rate >= 15 else ORANGE if rate >= 5 else YELLOW
            pos = " → ".join(layouts.key_info(lang, c).split(",")[0] for c in pair)
            t.add_row(Text(pair.upper(), style=f"bold {color}"), str(n), f"{avg} ms",
                      Text(f"%{rate:g}", style=color), pos)
        self.query_one("#pairs_info", Static).update(Text(
            "yavaş ve hatalı geçişler üstte — Zayıf harf drili bu çiftleri çalıştırır"
            if pairs else "henüz yeterli veri yok — birkaç test yap!",
            style=DIM, justify="center"))

        self.query_one("#shelp", Static).update(hints([
            ("1-4", "sekme"), ("L", "dil"), ("ESC", "geri")], PURPLE))

    def action_tab(self, name):
        self.query_one("#tabs", TabbedContent).active = name

    def action_lang(self):
        self.app.lang = "en" if self.app.lang == "tr" else "tr"
        self.app.save_settings()
        self.load()

    def action_back(self):
        self.app.pop_screen()


# ---------------------------------------------------------------------------
class KiviApp(App):
    TITLE = "Kivi"
    CSS = """
    Screen { background: #140a24; align: center middle; }
    #home, #test, #result, #stats { width: 94%; max-width: 96; height: auto; }
    #home Static, #test Static, #result Static { width: 100%; }

    /* Menü */
    #logo { height: 5; margin-top: 1; text-align: center; }
    #tag, #best, #cta { text-align: center; height: 1; }
    #wave { height: 1; margin: 1 0; text-align: center; }
    #settings { width: 64; height: auto; padding: 1 2; margin: 1 0;
                border: heavy #ff2e97; border-title-color: #ffd23f;
                border-title-align: center; background: #1d1033; }
    #home { align-horizontal: center; }
    #help, #hint, #rhelp, #shelp { text-align: center; margin-top: 1; }

    /* Test */
    #info { text-align: center; height: 3; }
    #timebar { height: 1; margin-bottom: 1; }
    #words { height: 9; padding: 1 3; border: double #00e5ff;
             border-title-color: #ff2e97; border-title-align: center;
             background: #1d1033; }
    #spark { height: 4; margin: 1 0 0 0; border: round #5b2a86;
             border-title-color: #8a74a8; padding: 0 1; }
    Sparkline > .sparkline--max-color { color: #ff2e97; }
    Sparkline > .sparkline--min-color { color: #00e5ff; }
    #keyboard { height: auto; text-align: center; margin-top: 1; }

    /* Sonuç */
    #banner { height: 1; text-align: center; margin: 1 0; }
    #big { height: 5; text-align: center; }
    #unit { height: 1; text-align: center; margin: 1 0 0 0; }
    #rspark { height: 5; margin: 1 0; }
    #details { text-align: center; }

    /* İstatistik */
    #stitle { height: 1; margin-bottom: 1; }
    #heat { height: auto; margin: 1 0; text-align: center; }
    #pairs_info { height: 1; margin: 1 0; }
    #weak_t, #pool_t, #hist_t, #pairs_t { height: 14; background: #1d1033; }
    #hspark { height: 5; margin-bottom: 1; border: round #5b2a86;
              border-title-color: #8a74a8; }
    TabbedContent { background: #140a24; }
    Tabs { background: #140a24; }
    Tab { color: #8a74a8; background: #140a24; }
    Tab.-active { color: #ff2e97; text-style: bold; background: #140a24; }
    Underline > .underline--bar { color: #ff2e97; background: #3a1c5c; }
    DataTable { color: #f3e9ff; }
    DataTable > .datatable--header { background: #2a1744; color: #00e5ff; text-style: bold; }
    DataTable > .datatable--cursor { background: #5b2a86; color: #ffffff; }
    DataTable > .datatable--even-row { background: #231240; }

    ConfirmScreen { align: center middle; background: #140a24 70%; }
    #confirm { width: 58; height: auto; padding: 1 2; border: heavy #ff3b5c;
               background: #1d1033; text-align: center; }
    """

    def __init__(self):
        super().__init__()
        st = storage.get_settings()
        self.lang = st.get("lang") if st.get("lang") in LANGS else "tr"
        self.duration = st.get("duration") if st.get("duration") in DURATIONS else 30
        self.mode = st.get("mode") if st.get("mode") in MODE_INFO else "normal"
        self.limit = st.get("limit") if st.get("limit") in LIMITS else 30
        lesson = st.get("lesson")
        self.lesson = lesson if isinstance(lesson, int) and lesson >= 1 else 1
        self.fingers = bool(st.get("fingers", False))
        sw = st.get("switch")
        self.sound = sound.KeySound(sw if sw in sound.SWITCHES else "brown")

    def lesson_level(self):
        """Seçili ders; açılmamış dersse en yüksek açık derse çekilir."""
        top = storage.unlocked_lesson(self.lang)
        return max(1, min(self.lesson, top))

    def save_settings(self):
        try:
            storage.save_settings({
                "lang": self.lang, "duration": self.duration, "mode": self.mode,
                "limit": self.limit, "lesson": self.lesson, "fingers": self.fingers,
                "switch": self.sound.switch})
        except OSError:
            pass                      # ayar kaydedilemese de oyun çalışmaya devam eder

    def on_mount(self):
        self.push_screen(HomeScreen())


def run():
    KiviApp().run()
