// audio_kernels.cl

/*
Kernel for Global Min/Max Amplitude.
This kernel uses a reduction strategy. Each work-group computes a local min/max.
These local min/max values are written to intermediate buffers.
The host code will then perform a final reduction on these intermediate results.
*/
__kernel void min_max_global_kernel(
    __global const float *audio_data, // Input audio samples
    __global float *group_mins,       // Output buffer for min value from each work-group
    __global float *group_maxs,       // Output buffer for max value from each work-group
    __local float *local_mins,        // Local memory for min reduction within a work-group
    __local float *local_maxs,        // Local memory for max reduction within a work-group
    const unsigned int n_samples     // Total number of samples
) {
    unsigned int local_id = get_local_id(0);
    unsigned int group_id = get_group_id(0);
    unsigned int local_size = get_local_size(0);
    unsigned int global_id = get_global_id(0);

    // Initialize local min/max with the first element this work-item will process
    // Each work-item might process multiple elements if n_samples > global_size
    float current_min = FLT_MAX;
    float current_max = -FLT_MAX;

    // Each work-item processes a stride of elements
    for (unsigned int i = global_id; i < n_samples; i += get_global_size(0)) {
        float sample = audio_data[i];
        current_min = fmin(current_min, sample);
        current_max = fmax(current_max, sample);
    }
    
    local_mins[local_id] = current_min;
    local_maxs[local_id] = current_max;

    // Synchronize work-items within the work-group
    barrier(CLK_LOCAL_MEM_FENCE);

    // Perform reduction in local memory
    for (unsigned int s = local_size / 2; s > 0; s >>= 1) {
        if (local_id < s) {
            local_mins[local_id] = fmin(local_mins[local_id], local_mins[local_id + s]);
            local_maxs[local_id] = fmax(local_maxs[local_id], local_maxs[local_id + s]);
        }
        barrier(CLK_LOCAL_MEM_FENCE);
    }

    // First work-item in each group writes the group's result to global memory
    if (local_id == 0) {
        group_mins[group_id] = local_mins[0];
        group_maxs[group_id] = local_maxs[0];
    }
}


/*
Kernel for Interval-Based Min/Max Amplitude.
Each work-item processes one interval.
*/
__kernel void min_max_interval_kernel(
    __global const float *audio_data,   // Input audio samples
    __global float *interval_mins,      // Output buffer for min value of each interval
    __global float *interval_maxs,      // Output buffer for max value of each interval
    const unsigned int samples_per_interval, // Number of samples in each interval
    const unsigned int num_intervals         // Total number of intervals to process
) {
    unsigned int interval_idx = get_global_id(0); // Each work-item handles one interval

    if (interval_idx < num_intervals) {
        float current_min = FLT_MAX;
        float current_max = -FLT_MAX;

        unsigned int start_sample_idx = interval_idx * samples_per_interval;
        // unsigned int end_sample_idx = start_sample_idx + samples_per_interval;
        // Ensure we don't read past the end of audio_data if the last interval is partial
        // However, the host code should prepare audio_data to be a multiple of samples_per_interval
        // or handle the last partial interval separately if strictness is required.
        // For simplicity, this kernel assumes full intervals.

        for (unsigned int i = 0; i < samples_per_interval; ++i) {
            float sample = audio_data[start_sample_idx + i];
            current_min = fmin(current_min, sample);
            current_max = fmax(current_max, sample);
        }
        interval_mins[interval_idx] = current_min;
        interval_maxs[interval_idx] = current_max;
    }
}
