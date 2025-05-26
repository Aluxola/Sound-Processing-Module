`timescale 1ns / 1ps

module min_max_amplitude(
    input wire clk,
    input wire rst,             // Active high reset
    input wire signed [15:0] sample_in,
    input wire sample_valid,    // Asserted when sample_in is valid
    output reg signed [15:0] min_out,
    output reg signed [15:0] max_out
);

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            min_out <= 16'sh7FFF; // Initialize to max positive value
            max_out <= -16'sh8000; // Initialize to min negative value
        end else if (sample_valid) begin
            if (sample_in < min_out)
                min_out <= sample_in;
            if (sample_in > max_out)
                max_out <= sample_in;
        end
    end

endmodule
