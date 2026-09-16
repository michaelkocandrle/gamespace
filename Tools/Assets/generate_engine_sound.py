"""Generates a seamless, deep engine rumble loop as a 16-bit mono WAV. Placeholder audio.

Runs with the system Python (numpy), NOT inside Unreal:

    python Tools/Assets/generate_engine_sound.py Intermediate/GeneratedAssets/engine_loop.wav

Character: distant low rumble and a soft hum, no whine and no hiss.

- Everything is filtered noise shaped in the frequency domain with smooth (Butterworth-style)
  slopes. The first version used pure sine partials, which stood 13-19 dB above their
  surroundings and read as a piercing turbine whine, and brick-wall band edges.
- The "hum" is narrow-band noise a few Hz wide around low harmonics rather than sines, so it
  has pitch without the tonal edge.
- A steep low-pass (8th order at 700 Hz) keeps the energy out of the 1-4 kHz range the ear is
  most sensitive to; the first version peaked there, like a vacuum cleaner.

The loop is seamless by construction: every component sits on exact FFT bins of the loop
length. 8 s rather than 4 s so the noise pattern does not audibly repeat.
"""

import sys
import wave

import numpy as np

RATE = 48000
SECONDS = 8.0
SEED = 20260917
PEAK_DBFS = -3.0


def lowpass(freqs, corner, order):
    return 1.0 / np.sqrt(1.0 + (freqs / corner) ** (2 * order))


def highpass(freqs, corner, order):
    ratio = (freqs / corner) ** (2 * order)
    return np.sqrt(ratio / (1.0 + ratio))


def shaped_noise(rng, n, magnitude):
    """Random-phase noise with the given magnitude per FFT bin; periodic over the loop."""
    phase = rng.uniform(0.0, 2.0 * np.pi, len(magnitude))
    signal = np.fft.irfft(magnitude * np.exp(1j * phase), n)
    return signal / np.sqrt(np.mean(signal ** 2))   # unit RMS, so mix weights mean loudness


def main(out_path):
    rng = np.random.default_rng(SEED)
    n = int(RATE * SECONDS)
    freqs = np.fft.rfftfreq(n, 1.0 / RATE)
    f = np.maximum(freqs, 1.0)

    # Deep rumble: darkened noise between ~40 and ~170 Hz. The high-pass stops sub-sonic energy
    # from eating headroom nobody can hear.
    rumble = shaped_noise(rng, n, f ** -0.6 * highpass(f, 40.0, 3) * lowpass(f, 170.0, 4))

    # Body: a quieter layer up to ~450 Hz so the engine still exists on small speakers,
    # which reproduce little below 100 Hz.
    body = shaped_noise(rng, n, f ** -0.5 * highpass(f, 90.0, 2) * lowpass(f, 450.0, 4))

    # Hum: narrow noise bands (3 Hz wide) around a low fundamental and its first harmonics.
    hum_mag = np.zeros_like(f)
    for harmonic, weight in ((1, 1.0), (2, 0.55), (3, 0.3), (4, 0.15)):
        hum_mag += weight * np.exp(-0.5 * ((freqs - 48.0 * harmonic) / 1.5) ** 2)
    hum = shaped_noise(rng, n, hum_mag)

    mix = 0.55 * rumble + 0.38 * body + 0.20 * hum

    # Global tilt away from the ear-sensitive band: nothing above ~1 kHz survives in any strength.
    spectrum = np.fft.rfft(mix) * lowpass(f, 700.0, 8)
    mix = np.fft.irfft(spectrum, n)

    # Slow "breathing", whole cycles over the loop: 0.25 Hz (2 cycles) and 0.625 Hz (5 cycles).
    t = np.arange(n) / RATE
    mix *= 1.0 + 0.10 * np.sin(2 * np.pi * 0.25 * t) + 0.05 * np.sin(2 * np.pi * 0.625 * t + 1.3)

    mix *= 10 ** (PEAK_DBFS / 20.0) / np.max(np.abs(mix))
    pcm = np.round(mix * 32767.0).astype("<i2")

    with wave.open(out_path, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())

    steps = np.abs(np.diff(pcm.astype(np.int32)))
    seam = abs(int(pcm[0]) - int(pcm[-1]))
    print("wrote %s  (%.1f s, %d Hz, peak %d, seam step %d vs p99 step %d)" % (
        out_path, SECONDS, RATE, np.max(np.abs(pcm)), seam, int(np.percentile(steps, 99))))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "engine_loop.wav")
