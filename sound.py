# -*- coding: utf-8 -*-
"""Mekanik klavye sesleri — harici bağımlılık yok.

Sesler ilk kullanımda standart kütüphaneyle (wave + math) sentezlenir ve geçici
dizine yazılır; sonra işletim sistemine göre çalınır:
  Windows -> winsound, macOS -> afplay, Linux -> paplay / aplay / play.
"""

import math
import os
import random
import shutil
import struct
import subprocess
import tempfile
import wave

RATE = 22050
VARIANTS = 3
VERSION = "v1"

# Her switch: görünen ad, kısa açıklama ve ses olayları.
# olay = (gecikme_ms, gürültü_gücü, gürültü_süresi_ms, ton_hz, ton_gücü, ton_süresi_ms, yumuşaklık)
SWITCHES = {
    "off": ("Sessiz", "ses yok", []),
    "blue": ("Mavi", "tık sesli (clicky)", [
        (0, 0.55, 5, 4300, 0.55, 9, 0.85),     # keskin 'tık'
        (38, 0.50, 9, 2100, 0.40, 14, 0.55),   # 'klak' (dibe vurma)
        (38, 0.25, 22, 420, 0.45, 40, 0.15),
    ]),
    "red": ("Kırmızı", "yumuşak, lineer", [
        (0, 0.28, 12, 210, 0.75, 38, 0.10),
        (0, 0.18, 6, 1300, 0.20, 10, 0.35),
    ]),
    "brown": ("Kahverengi", "dokunsal (tactile)", [
        (0, 0.35, 8, 1500, 0.30, 12, 0.45),
        (14, 0.30, 14, 260, 0.65, 30, 0.12),
    ]),
    "black": ("Siyah", "ağır, derin 'thock'", [
        (0, 0.30, 16, 130, 0.90, 60, 0.08),
        (0, 0.15, 8, 900, 0.20, 12, 0.25),
    ]),
}
ORDER = ["off", "blue", "red", "brown", "black"]


def _synth(events, pitch=1.0, gain=1.0, seed=0):
    rnd = random.Random(seed)
    total_ms = max(d + max(nd, td) * 3 for d, _, nd, _, _, td, _ in events) + 20
    n = int(RATE * total_ms / 1000)
    buf = [0.0] * n
    for delay, namp, nms, hz, tamp, tms, soft in events:
        start = int(RATE * delay / 1000)
        lp = 0.0
        for i in range(n - start):
            t = i / RATE
            noise = rnd.uniform(-1, 1) * math.exp(-t * 1000 / max(nms, 1) / 1.0)
            lp += soft * (noise - lp) if soft < 1 else noise      # tek kutuplu alçak geçiren
            tone = math.sin(2 * math.pi * hz * pitch * t) * math.exp(-t * 1000 / max(tms, 1))
            buf[start + i] += namp * lp + tamp * tone
    peak = max(max(abs(x) for x in buf), 1e-6)
    scale = 0.9 * 32767 * min(gain, 1.0) / peak
    return b"".join(struct.pack("<h", int(x * scale)) for x in buf)


def _write_wav(path, frames):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(frames)


class KeySound:
    """Switch seçimine göre tuş sesi çalar. Ses yoksa/başarısızsa sessizce geçer."""

    def __init__(self, switch="brown"):
        self.switch = switch if switch in SWITCHES else "brown"
        self._dir = os.path.join(tempfile.gettempdir(), f"kivi_sounds_{VERSION}")
        self._cache = {}
        self._player = self._find_player()

    @staticmethod
    def _find_player():
        if os.name == "nt":
            return "winsound"
        for cmd in ("afplay", "paplay", "aplay", "play"):
            if shutil.which(cmd):
                return cmd
        return None

    @property
    def available(self):
        return self._player is not None

    def cycle(self):
        self.switch = ORDER[(ORDER.index(self.switch) + 1) % len(ORDER)]
        return self.switch

    def label(self):
        name, desc, _ = SWITCHES[self.switch]
        return f"{name} · {desc}"

    def _files(self, switch, kind):
        key = (switch, kind)
        if key not in self._cache:
            os.makedirs(self._dir, exist_ok=True)
            events = SWITCHES[switch][2]
            paths = []
            for v in range(VARIANTS):
                path = os.path.join(self._dir, f"{switch}_{kind}_{v}.wav")
                if not os.path.exists(path):
                    rnd = random.Random(sum(map(ord, switch + kind)) * 31 + v)
                    pitch = {"key": 1.0, "space": 0.72, "back": 0.9}[kind] * rnd.uniform(0.93, 1.07)
                    _write_wav(path, _synth(events, pitch=pitch, seed=v + 1))
                paths.append(path)
            self._cache[key] = paths
        return self._cache[key]

    def play(self, kind="key"):
        """kind: 'key' (harf), 'space' (boşluk/enter), 'back' (silme)."""
        if self.switch == "off" or not self._player:
            return
        try:
            path = random.choice(self._files(self.switch, kind))
            if self._player == "winsound":
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC
                                   | winsound.SND_NODEFAULT)
            else:
                subprocess.Popen([self._player, path], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception:
            pass
