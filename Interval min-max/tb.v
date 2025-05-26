`timescale 1ns / 1ps

module tb;
    reg clk = 0;
    reg rst = 1;
    reg signed [15:0] audio_sample;
    reg sample_valid;

    top dut (
        .clk(clk),
        .rst(rst),
        .audio_sample(audio_sample),
        .sample_valid(sample_valid)
    );

    always #5 clk = ~clk; // 100MHz

    integer file, status;
    reg [15:0] sample_data;
    integer i;

    initial begin
        $dumpfile("waveform.vcd");
        $dumpvars(0, tb);

        #20 rst = 0;
        file = $fopen("audio_samples.txt", "r");
        if (file == 0) begin
            $display("Failed to open input file.");
            $finish;
        end

        for (i = 0; i < 441000; i = i + 1) begin
            @(posedge clk);
            status = $fscanf(file, "%d\n", sample_data);
            audio_sample = sample_data;
            sample_valid = 1;
        end

        $fclose(file);
        sample_valid = 0;
    end
endmodule
