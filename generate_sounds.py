"""Generate simple sound effect .wav files for the Xbox Controller Anki add-on."""
import struct
import wave
import math
import os

SAMPLE_RATE = 44100
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')


def generate_sine(freq, duration, volume=0.5, fade_ms=10):
    n_samples = int(SAMPLE_RATE * duration)
    fade_samples = int(SAMPLE_RATE * fade_ms / 1000)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        val = math.sin(2 * math.pi * freq * t) * volume
        if i < fade_samples:
            val *= i / fade_samples
        elif i > n_samples - fade_samples:
            val *= (n_samples - i) / fade_samples
        samples.append(val)
    return samples


def mix(samples_list):
    length = max(len(s) for s in samples_list)
    result = [0.0] * length
    for samples in samples_list:
        for i, v in enumerate(samples):
            result[i] += v
    peak = max(abs(v) for v in result) or 1.0
    return [v / peak * 0.9 for v in result]


def write_wav(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            wf.writeframes(struct.pack('<h', int(clamped * 32767)))


def generate_correct():
    """Crisp ascending ding."""
    s1 = generate_sine(880, 0.08, 0.6, fade_ms=5)
    s2 = generate_sine(1320, 0.12, 0.7, fade_ms=8)
    combined = s1 + s2
    return combined


def generate_wrong():
    """Low buzzy hum."""
    s1 = generate_sine(120, 0.5, 0.8, fade_ms=20)
    s2 = generate_sine(150, 0.5, 0.5, fade_ms=20)
    s3 = generate_sine(90, 0.4, 0.4, fade_ms=20)
    return mix([s1, s2, s3])


def generate_click():
    """Short neutral click."""
    s1 = generate_sine(600, 0.04, 0.5, fade_ms=3)
    s2 = generate_sine(800, 0.03, 0.3, fade_ms=3)
    return mix([s1, s2])


def generate_trigger():
    """Very short soft tick."""
    s1 = generate_sine(500, 0.025, 0.3, fade_ms=2)
    return s1


def main():
    print(f'Generating sounds in {OUTPUT_DIR}')
    write_wav(os.path.join(OUTPUT_DIR, 'correct.wav'), generate_correct())
    print('  correct.wav')
    write_wav(os.path.join(OUTPUT_DIR, 'wrong.wav'), generate_wrong())
    print('  wrong.wav')
    write_wav(os.path.join(OUTPUT_DIR, 'click.wav'), generate_click())
    print('  click.wav')
    write_wav(os.path.join(OUTPUT_DIR, 'trigger.wav'), generate_trigger())
    print('  trigger.wav')
    print('Done.')


if __name__ == '__main__':
    main()
