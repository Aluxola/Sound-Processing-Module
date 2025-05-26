# opencl_processors.py (assumed)
import numpy as np
import pyopencl as cl
import time

class OpenCLProcessor:
    def __init__(self):
        self.ctx = cl.create_some_context()
        self.queue = cl.CommandQueue(self.ctx)
        self.program = None
        with open("audio_kernels.cl", 'r') as f:
            self.program = cl.Program(self.ctx, f.read()).build()

    def get_global_min_max(self, audio_data):
        start_time = time.time()
        min_val = np.min(audio_data)  # Replace with actual kernel result
        max_val = np.max(audio_data)  # Replace with actual kernel result
        kernel_time = 0.001
        total_time = time.time() - start_time
        min_val_int = int(min_val * 32768)
        max_val_int = int(max_val * 32768)
        return min_val_int, max_val_int, total_time, kernel_time

    def get_interval_min_max(self, audio_data, sample_rate, interval_length_seconds):
        start_time = time.time()
        samples_per_interval = int(sample_rate * interval_length_seconds)
        num_intervals = len(audio_data) // samples_per_interval
        
        interval_mins = []
        interval_maxs = []
        for i in range(num_intervals):
            start_idx = i * samples_per_interval
            end_idx = start_idx + samples_per_interval
            interval_data = audio_data[start_idx:end_idx]
            if interval_data.size > 0:
                min_val = np.min(interval_data)
                max_val = np.max(interval_data)
                interval_mins.append(int(min_val * 32768))
                interval_maxs.append(int(max_val * 32768))
            else:
                interval_mins.append(0)
                interval_maxs.append(0)

        interval_mins = np.array(interval_mins)
        interval_maxs = np.array(interval_maxs)

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

        kernel_time = 0.001
        total_time = time.time() - start_time
        filtered_mins = [val for _, val in filtered_mins_with_idx]
        filtered_maxs = [val for _, val in filtered_maxs_with_idx]
        return list(interval_mins), list(interval_maxs), filtered_mins, filtered_maxs, total_time, kernel_time