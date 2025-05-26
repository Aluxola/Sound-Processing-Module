import wave
import struct
import numpy as np

WAV_FILE = "input.wav"
TXT_FILE = "audio_samples.txt"

def wav_to_txt(wav_path, txt_path):
    with wave.open(wav_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        duration = n_frames / framerate

        assert sampwidth == 2, "Only 16-bit WAV supported"
        assert n_channels == 1, "Only mono WAV supported"
        assert framerate == 44100, "Must be 44.1 kHz audio"
        assert int(duration) == 10, "Must be 10 seconds long"

        print(f"Loaded {wav_path}: {duration}s, {n_frames} frames")

        frames = wf.readframes(n_frames)
        samples = struct.unpack("<{}h".format(n_frames), frames)

        # Save to txt
        with open(txt_path, "w") as f:
            for s in samples:
                f.write(f"{s}\n")

        print(f"Saved {n_frames} samples to {txt_path}")

        # Optional: print interval stats
        print("Min/Max per second (optional check):")
        for i in range(10):
            chunk = samples[i*44100 : (i+1)*44100]
            print(f"Interval {i+1}: min={min(chunk)}, max={max(chunk)}")

if __name__ == "__main__":
    wav_to_txt(WAV_FILE, TXT_FILE)
