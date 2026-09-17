"""Generates the ship's placeholder sounds as 16-bit mono WAVs. Runs with the system Python
(numpy + scipy), NOT inside Unreal:

    python Tools/Assets/generate_ship_sounds.py Intermediate/GeneratedAssets

then import them (editor closed):

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\build_ship_audio.py

Loops (seamless: every component sits on exact FFT bins of the loop length, and every
modulation completes whole cycles in it):

    engine_loop.wav    thrusters: a soft roar centred low-mid, rumble below, a faint tonal
                       whirr for identity. Volume and pitch follow what the thrusters do.
    engine_hum.wav     reactor hum under everything while piloted: a low harmonic drone,
                       gently beating, no hiss.
    boost_loop.wav     afterburner: brighter blast, a low pulsing thump, sparse crackle.
    cruise_loop.wav    cruise drive: a fifths chord drone with slow chorus and a breathing
                       band of air on top.

One-shots:

    boost_start.wav    ignition thump and burst.
    cruise_charge.wav  3 s riser: a rising tone with quickening tremolo and a sweeping noise band.
    cruise_engage.wav  deep boom with a falling whoosh.
    cruise_drop.wav    falling tone and whoosh, a thump at the start.

Design rules learned from the first engine loop: keep energy out of 2-5 kHz (it reads as a
vacuum cleaner or a whine), use narrow noise bands or low partials rather than bright sines, and
give every sound a slope above ~1 kHz. The script prints the band balance of each file.
"""

import os
import sys
import wave

import numpy as np
from scipy.signal import istft, stft

RATE = 48000
SEED = 20260917


# ---------------------------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------------------------

def lowpass(f, corner, order):
    return 1.0 / np.sqrt(1.0 + (f / corner) ** (2 * order))


def highpass(f, corner, order):
    ratio = (np.maximum(f, 1e-6) / corner) ** (2 * order)
    return np.sqrt(ratio / (1.0 + ratio))


def bump(f, centre, octaves, gain):
    """Smooth peak of `gain` (linear, added to 1) at centre, `octaves` wide."""
    return 1.0 + gain * np.exp(-0.5 * (np.log2(np.maximum(f, 1.0) / centre) / (octaves / 2.0)) ** 2)


def unit_rms(x):
    return x / max(np.sqrt(np.mean(x ** 2)), 1e-12)


class Loop(object):
    """Frequency-domain helpers for a loop of `seconds`: everything they make repeats seamlessly."""

    def __init__(self, rng, seconds):
        self.rng = rng
        self.seconds = seconds
        self.n = int(round(RATE * seconds))
        self.t = np.arange(self.n) / RATE
        self.freqs = np.fft.rfftfreq(self.n, 1.0 / RATE)
        self.f = np.maximum(self.freqs, 1.0)

    def noise(self, magnitude):
        phase = self.rng.uniform(0.0, 2.0 * np.pi, len(magnitude))
        return unit_rms(np.fft.irfft(magnitude * np.exp(1j * phase), self.n))

    def narrow(self, centre, width_hz):
        """Noise a few Hz wide: pitch without the edge of a pure sine."""
        return self.noise(np.exp(-0.5 * ((self.freqs - centre) / width_hz) ** 2))

    def tone(self, frequency, phase=0.0):
        cycles = round(frequency * self.seconds)  # whole cycles, so the loop closes
        return np.sin(2.0 * np.pi * cycles / self.seconds * self.t + phase)

    def lfo(self, rate_hz, depth, phase=0.0):
        cycles = max(1, round(rate_hz * self.seconds))
        return 1.0 + depth * np.sin(2.0 * np.pi * cycles / self.seconds * self.t + phase)

    def filtered(self, x, response):
        return np.fft.irfft(np.fft.rfft(x) * response, self.n)


def sweep_noise(rng, n, start_hz, end_hz, octaves, curve=1.0):
    """Noise band whose centre glides from start_hz to end_hz (log scale) over n samples."""
    x = rng.standard_normal(n + 4096)
    freqs, times, spectrum = stft(x, RATE, nperseg=2048, noverlap=1536)
    progress = np.clip(times / (n / RATE), 0.0, 1.0) ** curve
    centres = start_hz * (end_hz / start_hz) ** progress
    distance = np.log2(np.maximum(freqs, 1.0))[:, None] - np.log2(centres)[None, :]
    mask = np.exp(-0.5 * (distance / (octaves / 2.0)) ** 2)
    _, y = istft(spectrum * mask, RATE, nperseg=2048, noverlap=1536)
    return unit_rms(y[:n])


def glide_tone(n, start_hz, end_hz, curve=1.0, harmonics=((1, 1.0),)):
    """A tone gliding exponentially from start_hz to end_hz, with optional harmonics."""
    progress = (np.arange(n) / max(n - 1, 1)) ** curve
    frequency = start_hz * (end_hz / start_hz) ** progress
    phase = 2.0 * np.pi * np.cumsum(frequency) / RATE
    return sum(weight * np.sin(k * phase) for k, weight in harmonics)


def brickless_lowpass(x, corner, order):
    freqs = np.fft.rfftfreq(len(x), 1.0 / RATE)
    return np.fft.irfft(np.fft.rfft(x) * lowpass(np.maximum(freqs, 1.0), corner, order), len(x))


def fade(x, in_ms=2.0, out_ms=30.0):
    n_in = int(RATE * in_ms / 1000.0)
    n_out = int(RATE * out_ms / 1000.0)
    y = x.copy()
    if n_in:
        y[:n_in] *= np.linspace(0.0, 1.0, n_in)
    if n_out:
        y[-n_out:] *= np.linspace(1.0, 0.0, n_out) ** 2
    return y


def normalise(x, rms_dbfs=None, peak_dbfs=-1.0):
    y = x.copy()
    if rms_dbfs is not None:
        y *= 10 ** (rms_dbfs / 20.0) / max(np.sqrt(np.mean(y ** 2)), 1e-12)
    peak = np.max(np.abs(y))
    limit = 10 ** (peak_dbfs / 20.0)
    if peak > limit:
        y *= limit / peak
    return y


# ---------------------------------------------------------------------------------------------
# Sounds
# ---------------------------------------------------------------------------------------------

def engine_loop(rng):
    L = Loop(rng, 8.0)
    f = L.f
    roar = L.noise(f ** -0.35 * highpass(f, 70.0, 2) * lowpass(f, 1400.0, 3) * bump(f, 260.0, 1.2, 1.2))
    rumble = L.noise(f ** -0.6 * highpass(f, 35.0, 3) * lowpass(f, 140.0, 4))
    whirr = 0.7 * L.narrow(190.0, 3.0) + 0.4 * L.narrow(380.0, 4.0)
    mix = 0.62 * roar + 0.45 * rumble + 0.16 * unit_rms(whirr)
    mix *= L.lfo(6.25, 0.05) * L.lfo(0.25, 0.06, 1.1)
    mix = L.filtered(mix, lowpass(f, 3000.0, 4))
    return normalise(mix, rms_dbfs=-18.0, peak_dbfs=-1.0), True


def engine_hum(rng):
    L = Loop(rng, 6.0)
    f0 = 43.5
    # The fundamental is felt more than heard (and small speakers drop it): the body of the hum
    # is in the 2nd to 5th partials.
    tone = sum(w * L.tone(f0 * k, phase=0.7 * k) for k, w in ((1, 0.55), (2, 0.8), (3, 0.65), (4, 0.45), (5, 0.28), (6, 0.16), (7, 0.08)))
    # A copy of the second partial half a hertz higher beats slowly against it: the hum "breathes".
    tone += 0.3 * L.tone(f0 * 2 + 0.5)
    soft = sum(w * L.narrow(f0 * k, 1.2) for k, w in ((2, 0.8), (3, 0.6), (4, 0.3)))
    texture = L.noise(highpass(L.f, 700.0, 2) * lowpass(L.f, 1800.0, 3))
    mix = unit_rms(tone) + 0.35 * unit_rms(soft) + 0.02 * texture
    mix *= L.lfo(0.5, 0.07)
    mix = L.filtered(mix, lowpass(L.f, 900.0, 4))
    return normalise(mix, rms_dbfs=-18.0, peak_dbfs=-1.0), True


def boost_loop(rng):
    L = Loop(rng, 6.0)
    f = L.f
    blast = L.noise(f ** -0.3 * highpass(f, 120.0, 2) * lowpass(f, 2800.0, 3) * bump(f, 650.0, 1.5, 1.0))
    thump = L.noise(highpass(f, 40.0, 3) * lowpass(f, 120.0, 4)) * L.lfo(11.0, 0.45)
    # Crackle: sparse clicks, filtered in the frequency domain so they wrap round the loop too.
    clicks = np.zeros(L.n)
    count = int(28 * L.seconds)
    clicks[rng.integers(0, L.n, count)] = rng.uniform(0.3, 1.0, count) * rng.choice([-1.0, 1.0], count)
    crackle = unit_rms(L.filtered(clicks, highpass(f, 1500.0, 2) * lowpass(f, 6000.0, 2)))
    mix = 0.7 * blast + 0.45 * thump + 0.09 * crackle
    mix = L.filtered(mix, lowpass(f, 4000.0, 3))
    return normalise(mix, rms_dbfs=-17.0, peak_dbfs=-1.0), True


def cruise_loop(rng):
    L = Loop(rng, 8.0)
    f = L.f
    drone = 0.0
    for frequency, weight in ((55.0, 0.55), (82.5, 0.5), (110.0, 0.7), (165.0, 0.4), (220.0, 0.25)):
        # Each voice twice, an eighth of a hertz apart: a slow chorus that closes over the loop.
        drone = drone + weight * (L.tone(frequency) + 0.8 * L.tone(frequency + 0.125, phase=1.3))
    pad = (0.12 * L.tone(220.0) + 0.08 * L.tone(330.0, phase=0.4)) * L.lfo(0.5, 0.4)
    air = L.noise(highpass(f, 1200.0, 2) * lowpass(f, 3800.0, 3)) * L.lfo(0.25, 0.5)
    mix = unit_rms(drone) + 0.18 * unit_rms(pad) + 0.05 * air
    mix = L.filtered(mix, lowpass(f, 5000.0, 3))
    return normalise(mix, rms_dbfs=-18.0, peak_dbfs=-1.0), True


def boost_start(rng):
    n = int(RATE * 0.9)
    t = np.arange(n) / RATE
    thump = glide_tone(n, 110.0, 45.0, curve=0.5) * np.exp(-t / 0.12)
    burst = sweep_noise(rng, n, 1100.0, 450.0, 1.6) * np.exp(-t / 0.3) * (1.0 - np.exp(-t / 0.01))
    rumble = brickless_lowpass(rng.standard_normal(n), 150.0, 4)
    rumble = unit_rms(rumble) * np.exp(-t / 0.4)
    mix = brickless_lowpass(1.0 * thump + 0.45 * burst + 0.35 * rumble, 3500.0, 3)
    return normalise(fade(mix, 2.0, 60.0), peak_dbfs=-2.0), False


def cruise_charge(rng):
    seconds = 3.0
    n = int(RATE * seconds)
    t = np.arange(n) / RATE
    p = t / seconds
    tone = glide_tone(n, 55.0, 440.0, curve=1.6, harmonics=((1, 1.0), (2, 0.4), (3, 0.18)))
    tremolo_phase = 2.0 * np.pi * np.cumsum(4.0 + 18.0 * p ** 2) / RATE
    tone *= (0.75 + 0.25 * np.sin(tremolo_phase)) * (0.15 + 0.85 * p ** 1.5)
    riser = sweep_noise(rng, n, 300.0, 2800.0, 1.2, curve=1.3) * p ** 2
    sub = brickless_lowpass(rng.standard_normal(n), 120.0, 4)
    sub = unit_rms(sub) * p
    mix = unit_rms(tone) * 0.8 + 0.35 * riser + 0.3 * sub
    mix = brickless_lowpass(mix, 5000.0, 3)
    return normalise(fade(mix, 20.0, 40.0), peak_dbfs=-2.0), False


def cruise_engage(rng):
    n = int(RATE * 1.8)
    t = np.arange(n) / RATE
    boom = glide_tone(n, 80.0, 32.0, curve=0.35, harmonics=((1, 1.0), (2, 0.25))) * np.exp(-t / 0.45) * (1.0 - np.exp(-t / 0.004))
    sub = unit_rms(brickless_lowpass(rng.standard_normal(n), 200.0, 4)) * np.exp(-t / 0.5)
    whoosh = sweep_noise(rng, n, 1800.0, 300.0, 1.4, curve=0.6) * np.exp(-t / 0.35)
    mix = 1.0 * boom + 0.4 * sub + 0.35 * whoosh
    mix = brickless_lowpass(mix, 3500.0, 3)
    return normalise(fade(mix, 1.0, 80.0), peak_dbfs=-2.0), False


def cruise_drop(rng):
    n = int(RATE * 1.5)
    t = np.arange(n) / RATE
    tone = glide_tone(n, 330.0, 55.0, curve=0.7, harmonics=((1, 1.0), (2, 0.3))) * np.exp(-t / 0.5)
    whoosh = sweep_noise(rng, n, 2500.0, 250.0, 1.5, curve=0.8) * np.exp(-t / 0.45) * (1.0 - np.exp(-t / 0.02))
    thump = glide_tone(n, 70.0, 40.0) * np.exp(-t / 0.15)
    mix = 0.55 * unit_rms(tone) + 0.45 * whoosh + 0.8 * thump
    mix = brickless_lowpass(mix, 5000.0, 3)
    return normalise(fade(mix, 1.0, 80.0), peak_dbfs=-2.0), False


SOUNDS = {
    "engine_loop": engine_loop,
    "engine_hum": engine_hum,
    "boost_loop": boost_loop,
    "cruise_loop": cruise_loop,
    "boost_start": boost_start,
    "cruise_charge": cruise_charge,
    "cruise_engage": cruise_engage,
    "cruise_drop": cruise_drop,
}


# ---------------------------------------------------------------------------------------------

def band_balance(x):
    power = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / RATE)
    total = max(power.sum(), 1e-12)
    edges = ((0, 100), (100, 500), (500, 2000), (2000, 5000), (5000, RATE / 2))
    return "  ".join("%s %2.0f%%" % ("%d-%dk" % (lo // 1000, hi // 1000) if lo >= 2000 else "%d-%d" % (lo, hi) if hi <= 2000 else "%dk+" % (lo // 1000),
                                   100.0 * power[(freqs >= lo) & (freqs < hi)].sum() / total) for lo, hi in edges)


def write_wav(path, samples):
    pcm = np.round(np.clip(samples, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(path, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())
    return pcm


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for index, (name, build) in enumerate(SOUNDS.items()):
        rng = np.random.default_rng(SEED + index)
        samples, looping = build(rng)
        pcm = write_wav(os.path.join(out_dir, name + ".wav"), samples)
        info = "%-14s %4.1f s  %s  rms %5.1f dBFS  peak %5.1f dBFS  %s" % (
            name, len(pcm) / RATE, "loop" if looping else "once",
            20 * np.log10(max(np.sqrt(np.mean(samples ** 2)), 1e-9)), 20 * np.log10(max(np.max(np.abs(samples)), 1e-9)),
            band_balance(samples))
        if looping:
            steps = np.abs(np.diff(pcm.astype(np.int32)))
            info += "  seam %d (p99 step %d)" % (abs(int(pcm[0]) - int(pcm[-1])), int(np.percentile(steps, 99)))
        print(info)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "GeneratedAssets")
