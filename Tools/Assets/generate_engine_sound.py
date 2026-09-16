"""Generates a seamless engine / thruster loop as a 16-bit mono WAV. Placeholder audio.

Runs with the system Python (numpy), NOT inside Unreal:

    python Tools/Assets/generate_engine_sound.py Intermediate/GeneratedAssets/engine_loop.wav

The loop is seamless by construction: every component is synthesised in the frequency domain
on exact FFT bins of the loop length, so each one completes a whole number of cycles and the
last sample flows straight into the first. SpaceshipPawn raises pitch with throttle, which
turns the tonal whine into the audible "spool up".
"""

import sys
import wave

import numpy as np

RATE = 48000
SECONDS = 4.0
SEED = 20260916


def band_noise(rng, n, lo_hz, hi_hz, tilt):
    """Random-phase noise between lo_hz and hi_hz, periodic over the loop. tilt < 0 darkens."""
    freqs = np.fft.rfftfreq(n, 1.0 / RATE)
    spectrum = np.zeros(len(freqs), dtype=np.complex128)
    band = (freqs >= lo_hz) & (freqs <= hi_hz)
    magnitude = np.power(np.maximum(freqs[band], 1.0), tilt)
    phase = rng.uniform(0.0, 2.0 * np.pi, band.sum())
    spectrum[band] = magnitude * np.exp(1j * phase)
    signal = np.fft.irfft(spectrum, n)
    return signal / np.max(np.abs(signal))


def tone(n, hz, amplitude):
    """A sine on an exact bin of the loop, so it is periodic too."""
    cycles = round(hz * SECONDS)
    t = np.arange(n) / n
    return amplitude * np.sin(2.0 * np.pi * cycles * t)


def main(out_path):
    rng = np.random.default_rng(SEED)
    n = int(RATE * SECONDS)
    t = np.arange(n) / n

    # Rumble starts at 45 Hz with a gentle tilt: laptop speakers and most headphones reproduce
    # little below ~80 Hz, and a steep low end made the first version nearly inaudible there.
    rumble = band_noise(rng, n, 45.0, 320.0, -0.4)      # body of the engine
    roar = band_noise(rng, n, 250.0, 2200.0, -0.5)      # combustion texture
    hiss = band_noise(rng, n, 2500.0, 9000.0, -0.3)     # exhaust / thruster gas

    whine = (tone(n, 220.0, 1.0) + tone(n, 440.0, 0.45) + tone(n, 660.0, 0.2)
             + tone(n, 1320.0, 0.08))
    whine /= np.max(np.abs(whine))

    # Slow flutter, a whole number of cycles over the loop (3 per second, 12 total).
    flutter = 1.0 + 0.12 * np.sin(2.0 * np.pi * 12 * t)

    mix = (0.45 * rumble + 0.40 * roar + 0.12 * hiss) * flutter + 0.16 * whine
    mix *= 0.7 / np.max(np.abs(mix))  # about -3 dBFS peak
    pcm = np.round(mix * 32767.0).astype("<i2")

    with wave.open(out_path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(pcm.tobytes())

    steps = np.abs(np.diff(pcm.astype(np.int32)))
    seam = abs(int(pcm[0]) - int(pcm[-1]))
    print("wrote %s  (%.1f s, %d Hz, peak %d, seam step %d vs median step %d / p99 %d)" % (
        out_path, SECONDS, RATE, np.max(np.abs(pcm)), seam, int(np.median(steps)), int(np.percentile(steps, 99))))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "engine_loop.wav")
