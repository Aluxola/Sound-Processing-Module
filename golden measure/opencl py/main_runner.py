# main_runner.py
import numpy as np
import time
import os

try:
    from audio_generator import generate_audio_text_file, load_wav_to_float_array
    from sequential_processors import load_audio_from_text, sequential_min_max_amplitude, sequential_interval_min_max_amplitude
    from opencl_processors import OpenCLProcessor
except ImportError as e:
    print(f"Import Error: {e}. Make sure all Python files (audio_generator.py, sequential_processors.py, opencl_processors.py) are in the same directory or your PYTHONPATH is configured.")
    exit()

# --- Configuration ---
YOUR_WAV_FILE_PATH = "test.wav"  # << CHANGE THIS to your WAV file or set to None
GENERATED_AUDIO_FILENAME = "audio_samples_10s_44100hz.txt"
DEFAULT_DURATION_S = 10
DEFAULT_SAMPLE_RATE = 44100  # Hz
ACTUAL_SAMPLE_RATE = DEFAULT_SAMPLE_RATE 
INTERVAL_LENGTH_S = 1.0  # seconds

def run_analysis():
    global ACTUAL_SAMPLE_RATE

    audio_data_np = None

    if YOUR_WAV_FILE_PATH and os.path.exists(YOUR_WAV_FILE_PATH):
        print(f"Loading WAV file: {YOUR_WAV_FILE_PATH}...")
        audio_data_np, sr_from_wav = load_wav_to_float_array(YOUR_WAV_FILE_PATH, target_sample_rate=None)
        if audio_data_np is not None:
            ACTUAL_SAMPLE_RATE = sr_from_wav
            print(f"Successfully loaded WAV. Sample rate: {ACTUAL_SAMPLE_RATE} Hz, Samples: {len(audio_data_np)}")
        else:
            print(f"Failed to load WAV file: {YOUR_WAV_FILE_PATH}. Exiting.")
            return
    else:
        if YOUR_WAV_FILE_PATH:
            print(f"WAV file specified but not found: {YOUR_WAV_FILE_PATH}")
        
        print(f"Falling back to generated audio: {GENERATED_AUDIO_FILENAME}...")
        if not os.path.exists(GENERATED_AUDIO_FILENAME):
            print(f"Generating audio data: {GENERATED_AUDIO_FILENAME}...")
            generate_audio_text_file(GENERATED_AUDIO_FILENAME, duration_seconds=DEFAULT_DURATION_S, sample_rate=DEFAULT_SAMPLE_RATE)
        else:
            print(f"Using existing generated audio data: {GENERATED_AUDIO_FILENAME}")
        
        try:
            with open(GENERATED_AUDIO_FILENAME, 'r') as f:
                data = [float(line.strip()) for line in f]
            audio_data_np = np.array(data, dtype=np.float32)
            ACTUAL_SAMPLE_RATE = DEFAULT_SAMPLE_RATE
            print(f"Loaded generated audio. Sample rate: {ACTUAL_SAMPLE_RATE} Hz, Samples: {len(audio_data_np)}")
        except Exception as e:
            print(f"Failed to load generated audio file {GENERATED_AUDIO_FILENAME}: {e}. Exiting.")
            return

    if audio_data_np is None or audio_data_np.size == 0:
        print("No audio data loaded. Exiting.")
        return

    print(f"\nProcessing audio with {len(audio_data_np)} samples at {ACTUAL_SAMPLE_RATE} Hz.")
    print(f"Interval length for analysis: {INTERVAL_LENGTH_S}s")

    # --- 1. Min Max Amplitude ---
    print("\n" + "="*30)
    print("SECTION 1: Global Min Max Amplitude")
    print("="*30)

    # Sequential
    print("\n--- Sequential Global Min/Max ---")
    s_min, s_max, s_time = sequential_min_max_amplitude(audio_data_np)
    if s_min is not None:
        print(f"Sequential Min: {s_min:>6d}, Max: {s_max:>6d}")
        print(f"Sequential Processing Time: {s_time:.6f} seconds")
    else:
        print("Sequential global min/max failed.")

    # OpenCL
    print("\n--- OpenCL Global Min/Max ---")
    try:
        ocl_processor = OpenCLProcessor()
        
        cl_min, cl_max, cl_total_time, cl_kernel_time = ocl_processor.get_global_min_max(audio_data_np)
        if cl_min is not None:
            # Assuming get_global_min_max returns scaled integer values (to be updated in opencl_processors.py)
            print(f"OpenCL Min: {cl_min:>6d}, Max: {cl_max:>6d}")
            print(f"OpenCL Total Time (Host + Device): {cl_total_time:.6f} seconds")
            print(f"OpenCL Kernel-Only Execution Time: {cl_kernel_time:.6f} seconds")
            if s_time > 0 and cl_total_time > 0:
                 print(f"Speedup (Total Time vs Sequential): {s_time / cl_total_time:.2f}x")
        else:
            print("OpenCL global min/max processing failed.")

        # --- 2. Interval Based Min Max Amplitude ---
        print("\n" + "="*30)
        print("SECTION 2: Interval Based Min Max Amplitude")
        print("="*30)

        # Sequential
        print("\n--- Sequential Interval Min/Max & Filtering ---")
        s_int_mins, s_int_maxs, s_filt_mins, s_filt_maxs, s_int_time = \
            sequential_interval_min_max_amplitude(audio_data_np, ACTUAL_SAMPLE_RATE, INTERVAL_LENGTH_S)
        
        if s_int_mins:
            num_intervals_seq = len(s_int_mins)
            print(f"Sequential - Num Intervals: {num_intervals_seq}")
            print(f"Sequential Interval Processing Time: {s_int_time:.6f} seconds")
        else:
            print("Sequential interval processing failed.")

        # OpenCL
        print("\n--- OpenCL Interval Min/Max & Filtering ---")
        cl_int_mins, cl_int_maxs, cl_filt_mins, cl_filt_maxs, cl_int_total_time, cl_int_kernel_time = \
            ocl_processor.get_interval_min_max(audio_data_np, ACTUAL_SAMPLE_RATE, INTERVAL_LENGTH_S)

        if cl_int_mins:
            num_intervals_cl = len(cl_int_mins)
            print(f"OpenCL - Num Intervals: {num_intervals_cl}")
            print(f"OpenCL Interval Total Time (Host + Device): {cl_int_total_time:.6f} seconds")
            print(f"OpenCL Interval Kernel-Only Execution Time: {cl_int_kernel_time:.6f} seconds")
            if s_int_time > 0 and cl_int_total_time > 0:
                print(f"Speedup (Total Time vs Sequential): {s_int_time / cl_int_total_time:.2f}x")
        else:
            print("OpenCL interval processing failed.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if YOUR_WAV_FILE_PATH == "test.wav" and not os.path.exists("test.wav"):
        print("Creating a dummy 'test.wav' as it's specified and not found...")
        sr_test = 22050
        duration_test = 10
        frequency_test = 440
        t_test = np.linspace(0, duration_test, int(sr_test * duration_test), False)
        note_test = np.sin(frequency_test * t_test * 2 * np.pi)
        noise = np.random.normal(0, 0.1, len(note_test))
        note_test = note_test + noise
        note_test = np.clip(note_test, -1.0, 1.0)

        audio_test_int16 = (note_test * 32767).astype(np.int16)
        try:
            from scipy.io import wavfile as scipy_wavfile
            scipy_wavfile.write("test.wav", sr_test, audio_test_int16)
            print("'test.wav' created for demonstration.")
        except Exception as e_wav:
            print(f"Could not create dummy 'test.wav': {e_wav}. Please provide a WAV file or ensure scipy is installed.")
            
    run_analysis()