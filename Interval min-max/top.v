
module top (
    input clk,  // 100MHz
    input rst,
    input signed [15:0] audio_sample,
    input sample_valid
);
    parameter INTERVAL_LEN = 44100;
    parameter NUM_INTERVALS = 10;

    reg [31:0] sample_count;
    reg [31:0] interval_index;
    wire interval_done;
    wire signed [15:0] min_out, max_out;
    wire ready;

    reg signed [15:0] min_arr [0:NUM_INTERVALS-1];
    reg signed [15:0] max_arr [0:NUM_INTERVALS-1];
    reg [31:0] stored_intervals = 0;

    assign interval_done = (sample_count == INTERVAL_LEN - 1);

    min_max u_minmax (
        .clk(clk),
        .rst(rst),
        .valid(sample_valid),
        .sample(audio_sample),
        .interval_done(interval_done),
        .min_val(min_out),
        .max_val(max_out),
        .ready(ready)
    );

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            sample_count <= 0;
            interval_index <= 0;
        end else if (sample_valid) begin
            if (interval_done) begin
                sample_count <= 0;
                interval_index <= interval_index + 1;
            end else begin
                sample_count <= sample_count + 1;
            end
        end
    end

    // store min/max and compute filtering
    real min_sum = 0, max_sum = 0;
    real min_mean, max_mean, min_std, max_std;
    integer i;

    always @(posedge clk) begin
        if (ready && stored_intervals < NUM_INTERVALS) begin
            min_arr[stored_intervals] <= min_out;
            max_arr[stored_intervals] <= max_out;
            $display("Interval %0d: Min = %0d, Max = %0d", stored_intervals, min_out, max_out);
            stored_intervals <= stored_intervals + 1;
        end

        // After all intervals processed, compute stats
        if (stored_intervals == NUM_INTERVALS) begin
            for (i = 0; i < NUM_INTERVALS; i = i + 1) begin
                min_sum = min_sum + min_arr[i];
                max_sum = max_sum + max_arr[i];
            end
            min_mean = min_sum / NUM_INTERVALS;
            max_mean = max_sum / NUM_INTERVALS;

            min_sum = 0;
            max_sum = 0;
            for (i = 0; i < NUM_INTERVALS; i = i + 1) begin
                min_sum = min_sum + (min_arr[i] - min_mean) * (min_arr[i] - min_mean);
                max_sum = max_sum + (max_arr[i] - max_mean) * (max_arr[i] - max_mean);
            end

            min_std = $sqrt(min_sum / NUM_INTERVALS);
            max_std = $sqrt(max_sum / NUM_INTERVALS);

            $display("\n--- Filtered Results ---");
            for (i = 0; i < NUM_INTERVALS; i = i + 1) begin
                if ((min_arr[i] >= min_mean - min_std) && (min_arr[i] <= min_mean + min_std))
                    $display("Filtered Min[%0d] = %0d", i, min_arr[i]);
                if ((max_arr[i] >= max_mean - max_std) && (max_arr[i] <= max_mean + max_std))
                    $display("Filtered Max[%0d] = %0d", i, max_arr[i]);
            end

            $finish;
        end
    end
endmodule
