import numpy as np
import os
from scipy.io import wavfile # For reading WAV files
from scipy.signal import resample # For resampling if needed

def generate_audio_text_file(filename="audio_samples.txt", duration_seconds=10, sample_rate=44100):
    """
    Generates a text file with simulated audio samples.
    Each line contains one floating-point audio sample.

    Args:
        filename (str): The name of the file to create.
        duration_seconds (int): The duration of the simulated audio clip.
        sample_rate (int): The number of samples per second.
    """
    num_samples = duration_seconds * sample_rate
    # Generate random samples between -1.0 and 1.0
    audio_data = np.random.uniform(low=-1.0, high=1.0, size=num_samples).astype(np.float32)
    
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

    with open(filename, 'w') as f:
        for sample in audio_data:
            f.write(f"{sample}\n")
    print(f"Generated '{filename}' with {num_samples} samples.")

def load_wav_to_float_array(filepath, target_sample_rate=None):
    """
    Loads a WAV file, converts it to mono, normalizes to float32 between -1.0 and 1.0.
    Optionally resamples the audio to a target sample rate.

    Args:
        filepath (str): Path to the WAV file.
        target_sample_rate (int, optional): If provided, resamples the audio to this rate.

    Returns:
        tuple: (numpy.ndarray, int) - The audio data as a float32 NumPy array, and the sample rate.
               Returns (None, None) if loading fails.
    """
    try:
        sample_rate, data = wavfile.read(filepath)
        print(f"Original WAV file: Sample rate = {sample_rate} Hz, Data type = {data.dtype}, Shape = {data.shape}")

        # Convert to mono if stereo
        if data.ndim > 1:
            if data.shape[1] == 2: # Common stereo case
                print("Converting stereo to mono by averaging channels.")
                data = data.mean(axis=1)
            else: # More than 2 channels, just take the first one
                print(f"Multi-channel audio ({data.shape[1]} channels), taking the first channel.")
                data = data[:, 0]

        # Convert to float32 and normalize
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        elif data.dtype == np.uint8: # 8-bit WAV
            data = (data.astype(np.float32) - 128.0) / 128.0
        elif data.dtype != np.float32:
            # If it's already float but not float32, convert it.
            # If it's some other int type, this basic normalization might not be ideal.
            print(f"Warning: Unhandled WAV data type {data.dtype}. Attempting direct conversion to float32. Normalization might be incorrect.")
            data = data.astype(np.float32)
        
        # Ensure data is between -1.0 and 1.0 if it was already float (e.g. float64)
        if np.issubdtype(data.dtype, np.floating):
             max_val = np.max(np.abs(data))
             if max_val > 1.0: # Normalize if it's float but outside [-1,1]
                 print(f"Floating point data is outside [-1,1] (max abs: {max_val}). Normalizing.")
                 data = data / max_val
             elif max_val == 0: # Avoid division by zero for silent audio
                 print("Audio data is silent (all zeros).")


        # Resample if a target sample rate is provided and different from the original
        if target_sample_rate is not None and target_sample_rate != sample_rate:
            print(f"Resampling from {sample_rate} Hz to {target_sample_rate} Hz.")
            num_samples_resampled = int(len(data) * float(target_sample_rate) / sample_rate)
            data = resample(data, num_samples_resampled).astype(np.float32)
            current_sample_rate = target_sample_rate
        else:
            current_sample_rate = sample_rate
            
        print(f"Processed audio: Sample rate = {current_sample_rate} Hz, Data type = {data.dtype}, Shape = {data.shape}, Min = {np.min(data):.2f}, Max = {np.max(data):.2f}")
        return data.astype(np.float32), current_sample_rate

    except FileNotFoundError:
        print(f"Error: WAV file not found at '{filepath}'")
        return None, None
    except Exception as e:
        print(f"Error loading or processing WAV file '{filepath}': {e}")
        return None, None

if __name__ == "__main__":
    # Example of generating a text file (original functionality)
    # generate_audio_text_file("dummy_audio.txt", duration_seconds=2, sample_rate=8000)

    # Example of loading a WAV file
    # Create a dummy WAV file for testing if you don't have one
    # This requires scipy to write as well.
    if not os.path.exists("test.wav"):
        print("Creating a dummy 'test.wav' for demonstration...")
        sr_test = 22050
        duration_test = 2
        frequency_test = 440
        t_test = np.linspace(0, duration_test, int(sr_test * duration_test), False)
        note_test = np.sin(frequency_test * t_test * 2 * np.pi)
        # Scale to 16-bit integer range
        audio_test_int16 = (note_test * 32767 / np.max(np.abs(note_test))).astype(np.int16)
        wavfile.write("test.wav", sr_test, audio_test_int16)
        print("'test.wav' created.")

    print("\n--- Loading test.wav ---")
    audio_array, sr = load_wav_to_float_array("test.wav")
    if audio_array is not None:
        print(f"Successfully loaded 'test.wav'. Samples: {len(audio_array)}, Sample Rate: {sr}")
        # You can pass 'audio_array' and 'sr' to your processing functions.

    print("\n--- Loading test.wav and resampling to 16000 Hz ---")
    audio_array_resampled, sr_resampled = load_wav_to_float_array("test.wav", target_sample_rate=16000)
    if audio_array_resampled is not None:
        print(f"Successfully loaded and resampled 'test.wav'. Samples: {len(audio_array_resampled)}, Sample Rate: {sr_resampled}")

