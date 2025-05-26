
module min_max (
    input clk,
    input rst,
    input valid,
    input signed [15:0] sample,
    input interval_done,
    output reg signed [15:0] min_val,
    output reg signed [15:0] max_val,
    output reg ready
);

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            min_val <= 16'sh7FFF;
            max_val <= -16'sh8000;
            ready <= 0;
        end else if (valid) begin
            if (sample < min_val) min_val <= sample;
            if (sample > max_val) max_val <= sample;
        end

        if (interval_done) begin
            ready <= 1;
        end else if (ready) begin
            min_val <= 16'sh7FFF;
            max_val <= -16'sh8000;
            ready <= 0;
        end
    end
endmodule
