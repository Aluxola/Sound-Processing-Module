
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define TOTAL_SAMPLES 441000
#define INTERVAL_LEN 44100
#define NUM_INTERVALS (TOTAL_SAMPLES / INTERVAL_LEN)

short audio_data[TOTAL_SAMPLES];
short min_vals[NUM_INTERVALS];
short max_vals[NUM_INTERVALS];

void load_audio_data(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open input file");
        exit(1);
    }
    for (int i = 0; i < TOTAL_SAMPLES; i++) {
        fscanf(file, "%hd", &audio_data[i]);
    }
    fclose(file);
}

void compute_intervals() {
    for (int i = 0; i < NUM_INTERVALS; i++) {
        short min = 32767;
        short max = -32768;
        for (int j = 0; j < INTERVAL_LEN; j++) {
            short sample = audio_data[i * INTERVAL_LEN + j];
            if (sample < min) min = sample;
            if (sample > max) max = sample;
        }
        min_vals[i] = min;
        max_vals[i] = max;
        printf("Interval %d: Min = %d, Max = %d\n", i, min, max);
    }
}

void filter_and_print() {
    double min_sum = 0, max_sum = 0;
    for (int i = 0; i < NUM_INTERVALS; i++) {
        min_sum += min_vals[i];
        max_sum += max_vals[i];
    }
    double min_mean = min_sum / NUM_INTERVALS;
    double max_mean = max_sum / NUM_INTERVALS;

    double min_std_sum = 0, max_std_sum = 0;
    for (int i = 0; i < NUM_INTERVALS; i++) {
        min_std_sum += pow(min_vals[i] - min_mean, 2);
        max_std_sum += pow(max_vals[i] - max_mean, 2);
    }
    double min_std = sqrt(min_std_sum / NUM_INTERVALS);
    double max_std = sqrt(max_std_sum / NUM_INTERVALS);

    printf("\n--- Filtered Min Values ---\n");
    for (int i = 0; i < NUM_INTERVALS; i++) {
        if (min_vals[i] >= min_mean - min_std && min_vals[i] <= min_mean + min_std)
            printf("Filtered Min[%d] = %d\n", i, min_vals[i]);
    }

    printf("\n--- Filtered Max Values ---\n");
    for (int i = 0; i < NUM_INTERVALS; i++) {
        if (max_vals[i] >= max_mean - max_std && max_vals[i] <= max_mean + max_std)
            printf("Filtered Max[%d] = %d\n", i, max_vals[i]);
    }
}

int main() {
    load_audio_data("audio_samples.txt");
    compute_intervals();
    filter_and_print();
    return 0;
}
