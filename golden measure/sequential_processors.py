# sequential_processors.py
import numpy as np
import time
import math

def load_audio_from_text(filename="audio_samples.txt"):
    """Loads audio samples from a text file."""
    try:
        with open(filename, 'r') as f:
            data = [float(line.strip()) for line in f]
        return np.array(data, dtype=np.float32)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found. Please generate it first.")
        return np.array([], dtype=np.float32)
    except ValueError:
        print(f"Error: File '{filename}' contains non-numeric data.")
        return np.array([], dtype=np.float32)

def sequential_min_max_amplitude(audio_data):
    """
    Finds the minimum and maximum amplitude in the audio data sequentially.
    """
    if audio_data.size == 0:
        return None, None, 0.0
    
    start_time = time.time()
    min_val = np.min(audio_data)
    max_val = np.max(audio_data)
    end_time = time.time()
    
    processing_time = end_time - start_time
    # Scale to 16-bit integer range for display
    min_val_int = int(min_val * 32768)
    max_val_int = int(max_val * 32768)
    return min_val_int, max_val_int, processing_time

def sequential_interval_min_max_amplitude(audio_data, sample_rate, interval_length_seconds):
    """
    Finds min/max for intervals and filters them sequentially.
    Modified to show the actual interval indices for filtered results.
    """
    if audio_data.size == 0:
        return [], [], [], [], 0.0

    start_time = time.time()
    
    samples_per_interval = int(sample_rate * interval_length_seconds)
    num_intervals = len(audio_data) // samples_per_interval
    
    interval_mins = []
    interval_maxs = []
    
    if samples_per_interval == 0:
        print("Error: Interval length is too short for the given sample rate, resulting in 0 samples per interval.")
        return [], [], [], [], 0.0

    for i in range(num_intervals):
        start_idx = i * samples_per_interval
        end_idx = start_idx + samples_per_interval
        interval_data = audio_data[start_idx:end_idx]
        if interval_data.size > 0:
            min_val = np.min(interval_data)
            max_val = np.max(interval_data)
            # Scale to 16-bit integer range
            interval_mins.append(int(min_val * 32768))
            interval_maxs.append(int(max_val * 32768))
        else:
            interval_mins.append(0)
            interval_maxs.append(0)

    interval_mins = np.array(interval_mins)
    interval_maxs = np.array(interval_maxs)

    # Print interval min/max in the specified format (Intervals 0 to 9)
    for i in range(min(10, len(interval_mins))):
        print(f"Interval {i}: Min = {interval_mins[i]:>6d}, Max = {interval_maxs[i]:>6d}")

    # Filtering with original interval indices
    filtered_mins_with_idx = []
    if len(interval_mins) > 1:
        mean_mins = np.mean(interval_mins)
        std_mins = np.std(interval_mins)
        lower_bound_mins = mean_mins - std_mins
        upper_bound_mins = mean_mins + std_mins
        for idx, m in enumerate(interval_mins):
            if lower_bound_mins <= m <= upper_bound_mins:
                filtered_mins_with_idx.append((idx, m))
    elif len(interval_mins) == 1:
        filtered_mins_with_idx = [(0, interval_mins[0])]

    filtered_maxs_with_idx = []
    if len(interval_maxs) > 1:
        mean_maxs = np.mean(interval_maxs)
        std_maxs = np.std(interval_maxs)
        lower_bound_maxs = mean_maxs - std_maxs
        upper_bound_maxs = mean_maxs + std_maxs
        for idx, m in enumerate(interval_maxs):
            if lower_bound_maxs <= m <= upper_bound_maxs:
                filtered_maxs_with_idx.append((idx, m))
    elif len(interval_maxs) == 1:
        filtered_maxs_with_idx = [(0, interval_maxs[0])]

    # Print filtered results with original interval indices
    print("\n--- Filtered Results ---")
    for idx, val in filtered_mins_with_idx:
        print(f"Filtered Min[{idx}] = {val:>6d}")
    for idx, val in filtered_maxs_with_idx:
        print(f"Filtered Max[{idx}] = {val:>6d}")

    end_time = time.time()
    processing_time = end_time - start_time
            
    # Return the lists without indices for compatibility with main_runner.py
    filtered_mins = [val for _, val in filtered_mins_with_idx]
    filtered_maxs = [val for _, val in filtered_maxs_with_idx]
    return list(interval_mins), list(interval_maxs), filtered_mins, filtered_maxs, processing_time

if __name__ == "__main__":
    # Generate dummy data if it doesn't exist
    import os
    if not os.path.exists("audio_samples.txt"):
        from audio_generator import generate_audio_text_file
        generate_audio_text_file("audio_samples.txt")

    audio = load_audio_from_text("audio_samples.txt")
    if audio.size > 0:
        print("--- Sequential Min/Max Amplitude ---")
        s_min, s_max, s_time = sequential_min_max_amplitude(audio)
        print(f"Min: {s_min:>6d}, Max: {s_max:>6d}")
        print(f"Sequential Time: {s_time:.6f} seconds")
        print("\n")

        print("--- Sequential Interval-Based Min/Max Amplitude ---")
        sample_rate = 44100
        interval_len = 1.0
        s_int_mins, s_int_maxs, s_filt_mins, s_filt_maxs, s_int_time = \
            sequential_interval_min_max_amplitude(audio, sample_rate, interval_len)
        
        print(f"Sequential Interval Time: {s_int_time:.6f} seconds")