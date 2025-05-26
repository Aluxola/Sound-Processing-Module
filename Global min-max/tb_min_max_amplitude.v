`timescale 1ns / 1ps

module tb_min_max_amplitude();

    reg clk;
    reg rst;
    reg signed [15:0] sample_in;
    reg sample_valid;
    wire signed [15:0] min_out;
    wire signed [15:0] max_out;

    // Generate VCD file
    initial begin
        $dumpfile("simulation.vcd");
        $dumpvars(0, tb_min_max_amplitude);
    end

    min_max_amplitude uut (
        .clk(clk),
        .rst(rst),
        .sample_in(sample_in),
        .sample_valid(sample_valid),
        .min_out(min_out),
        .max_out(max_out)
    );

    // Clock generation - 10ns period (5ns high, 5ns low)
    initial clk = 0;
    always #5 clk = ~clk;

    // File variables
    integer file, status;
    integer sample_count;
    reg signed [15:0] sample;

    initial begin
        rst = 1;
        sample_valid = 0;
        sample_in = 0;

        // Open the file (relative path recommended)
        file = $fopen("audio_samples.txt", "r");

        if (file == 0) begin
            $display("ERROR: Failed to open audio_samples.txt");
            $finish;
        end else begin
            $display("Reading samples from audio_samples.txt...");
        end

        // Reset deassert
        #20 rst = 0;

        // Read and apply values
        sample_count = 0;
        while (!$feof(file)) begin
            status = $fscanf(file, "%d\n", sample);
            if (status == 1) begin
                @(posedge clk);
                sample_in = sample;
                sample_valid = 1;
                sample_count = sample_count + 1;
            end
        end

        @(posedge clk);
        sample_valid = 0;

        $fclose(file);

        // Display results
        #50;
        $display("== Results ==");
        $display("Samples processed: %0d", sample_count);
        $display("Minimum Amplitude = %d", min_out);
        $display("Maximum Amplitude = %d", max_out);
        
        $finish;
    end

endmodule
