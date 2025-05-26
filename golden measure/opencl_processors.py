import numpy as np
import pyopencl as cl
import time

class OpenCLProcessor:
    def __init__(self):
        # Initialize OpenCL context and command queue
        self.ctx = cl.create_some_context()
        self.queue = cl.CommandQueue(self.ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
        # Load and build the OpenCL program
        with open("audio_kernels.cl", 'r') as f:
            self.program = cl.Program(self.ctx, f.read()).build()

    def get_global_min_max(self, audio_data):
        """
        Computes global min/max amplitude using OpenCL kernel.
        
        Args:
            audio_data: NumPy array of float32 audio samples in [-1.0, 1.0].
        
        Returns:
            Tuple (min_val_int, max_val_int, total_time, kernel_time):
                - min_val_int: Minimum amplitude scaled to 16-bit integer.
                - max_val_int: Maximum amplitude scaled to 16-bit integer.
                - total_time: Total execution time including host and device operations.
                - kernel_time: Kernel execution time on the device.
        """
        if audio_data.size == 0:
            return None, None, 0.0, 0.0

        start_time = time.time()
        
        # Convert audio_data to float32 and ensure contiguous array
        audio_data = np.array(audio_data, dtype=np.float32, order='C')
        n_samples = audio_data.size

        # Define work-group size (tune based on device, 256 is a common choice)
        local_size = 256
        global_size = max(local_size, (n_samples + local_size - 1) // local_size * local_size)
        num_groups = global_size // local_size

        # Allocate device buffers
        mf = cl.mem_flags
        audio_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=audio_data)
        group_mins_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, num_groups * np.float32().nbytes)
        group_maxs_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, num_groups * np.float32().nbytes)
        local_mins = cl.LocalMemory(local_size * np.float32().nbytes)
        local_maxs = cl.LocalMemory(local_size * np.float32().nbytes)

        # Execute the kernel
        kernel = self.program.min_max_global_kernel
        kernel.set_args(audio_buf, group_mins_buf, group_maxs_buf, local_mins, local_maxs, np.uint32(n_samples))
        event = cl.enqueue_nd_range_kernel(self.queue, kernel, (global_size,), (local_size,), wait_for=None)
        
        # Wait for kernel completion and get execution time
        event.wait()
        kernel_time = (event.profile.end - event.profile.start) * 1e-9  # Convert nanoseconds to seconds

        # Read results back to host
        group_mins = np.empty(num_groups, dtype=np.float32)
        group_maxs = np.empty(num_groups, dtype=np.float32)
        cl.enqueue_copy(self.queue, group_mins, group_mins_buf)
        cl.enqueue_copy(self.queue, group_maxs, group_maxs_buf)
        self.queue.finish()

        # Perform final reduction on host
        min_val = np.min(group_mins)
        max_val = np.max(group_maxs)

        # Scale to 16-bit integer range
        min_val_int = int(min_val * 32768)
        max_val_int = int(max_val * 32768)

        total_time = time.time() - start_time
        return min_val_int, max_val_int, total_time, kernel_time

    def get_interval_min_max(self, audio_data, sample_rate, interval_length_seconds):
        """
        Computes interval-based min/max amplitudes and filters them using OpenCL kernel.
        
        Args:
            audio_data: NumPy array of float32 audio samples in [-1.0, 1.0].
            sample_rate: Samples per second (e.g., 44100 Hz).
            interval_length_seconds: Length of each interval in seconds (e.g., 1.0).
        
        Returns:
            Tuple (interval_mins, interval_maxs, filtered_mins, filtered_maxs, total_time, kernel_time):
                - interval_mins: List of min amplitudes per interval (16-bit int).
                - interval_maxs: List of max amplitudes per interval (16-bit int).
                - filtered_mins: Filtered min amplitudes within one std dev (16-bit int).
                - filtered_maxs: Filtered max amplitudes within one std dev (16-bit int).
                - total_time: Total execution time including host and device operations.
                - kernel_time: Kernel execution time on the device.
        """
        if audio_data.size == 0:
            return [], [], [], [], 0.0, 0.0

        start_time = time.time()

        # Convert audio_data to float32 and ensure contiguous array
        audio_data = np.array(audio_data, dtype=np.float32, order='C')
        samples_per_interval = int(sample_rate * interval_length_seconds)
        if samples_per_interval == 0:
            print("Error: Interval length is too short for the given sample rate, resulting in 0 samples per interval.")
            return [], [], [], [], 0.0, 0.0

        num_intervals = (audio_data.size + samples_per_interval - 1) // samples_per_interval  # Handle partial last interval

        # Allocate device buffers
        mf = cl.mem_flags
        audio_buf = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=audio_data)
        interval_mins_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, num_intervals * np.float32().nbytes)
        interval_maxs_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, num_intervals * np.float32().nbytes)

        # Execute the kernel
        kernel = self.program.min_max_interval_kernel
        kernel.set_args(audio_buf, interval_mins_buf, interval_maxs_buf, np.uint32(samples_per_interval), np.uint32(num_intervals))
        event = cl.enqueue_nd_range_kernel(self.queue, kernel, (num_intervals,), None, wait_for=None)
        
        # Wait for kernel completion and get execution time
        event.wait()
        kernel_time = (event.profile.end - event.profile.start) * 1e-9  # Convert nanoseconds to seconds

        # Read results back to host
        interval_mins = np.empty(num_intervals, dtype=np.float32)
        interval_maxs = np.empty(num_intervals, dtype=np.float32)
        cl.enqueue_copy(self.queue, interval_mins, interval_mins_buf)
        cl.enqueue_copy(self.queue, interval_maxs, interval_maxs_buf)
        self.queue.finish()

        # Scale to 16-bit integer range
        interval_mins_int = (interval_mins * 32768).astype(np.int32)
        interval_maxs_int = (interval_maxs * 32768).astype(np.int32)

        # Print first 10 intervals
        for i in range(min(10, len(interval_mins_int))):
            print(f"Interval {i}: Min = {interval_mins_int[i]:>6d}, Max = {interval_maxs_int[i]:>6d}")

        # Filtering with original interval indices
        filtered_mins_with_idx = []
        if len(interval_mins_int) > 1:
            mean_mins = np.mean(interval_mins_int)
            std_mins = np.std(interval_mins_int)
            lower_bound_mins = mean_mins - std_mins
            upper_bound_mins = mean_mins + std_mins
            for idx, m in enumerate(interval_mins_int):
                if lower_bound_mins <= m <= upper_bound_mins:
                    filtered_mins_with_idx.append((idx, m))
        elif len(interval_mins_int) == 1:
            filtered_mins_with_idx = [(0, interval_mins_int[0])]

        filtered_maxs_with_idx = []
        if len(interval_maxs_int) > 1:
            mean_maxs = np.mean(interval_maxs_int)
            std_maxs = np.std(interval_maxs_int)
            lower_bound_maxs = mean_maxs - std_maxs
            upper_bound_maxs = mean_maxs + std_maxs
            for idx, m in enumerate(interval_maxs_int):
                if lower_bound_maxs <= m <= upper_bound_maxs:
                    filtered_maxs_with_idx.append((idx, m))
        elif len(interval_maxs_int) == 1:
            filtered_maxs_with_idx = [(0, interval_maxs_int[0])]

        # Print filtered results
        print("\n--- Filtered Results ---")
        for idx, val in filtered_mins_with_idx:
            print(f"Filtered Min[{idx}] = {val:>6d}")
        for idx, val in filtered_maxs_with_idx:
            print(f"Filtered Max[{idx}] = {val:>6d}")

        total_time = time.time() - start_time
        filtered_mins = [val for _, val in filtered_mins_with_idx]
        filtered_maxs = [val for _, val in filtered_maxs_with_idx]
        return list(interval_mins_int), list(interval_maxs_int), filtered_mins, filtered_maxs, total_time, kernel_time