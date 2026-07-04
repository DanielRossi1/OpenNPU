// mac_unit.v
// This is a MAC (Multiply-Accumulate unit) which follows a stream interface:
// an element (a,b) per cycle when valid_in=1.
// When last=1 over the last element, the cycle will stop with 'done', and
// acc_out will collect the final result (scalar product)
module mac_unit #(
    parameter DATA_W = 8, // 8-bits operator
    parameter ACC_W = 32  // 32-bits accumulator
)
(
    input wire clk,
    input wire rst_n, // asynchronous reset active low
    input wire valid_in, // 1 = a,b valid for this cycle
    input wire signed [DATA_W - 1 : 0] a,
    input wire signed [DATA_W - 1 : 0] b,
    input wire last, // 1 over the last element of the sum
    output reg done, // 1 when the result is ready
    output reg signed [ACC_W - 1 : 0] acc_out // output register
);

reg signed [ACC_W - 1 : 0] acc;
wire signed [2 * DATA_W - 1 : 0] raw_prod = a * b;
wire signed [ACC_W - 1 : 0] prod = {{(ACC_W - 2 * DATA_W){raw_prod[2 * DATA_W - 1]}}, raw_prod};

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        acc <= {ACC_W{1'b0}};
        acc_out <= {ACC_W{1'b0}};
        done <= 1'b0;
    end else begin
        done <= 1'b0;
        if (valid_in) begin
            if (last) begin
                // accumulate the last term and share the result
                acc_out <= acc + prod;
                acc <= {ACC_W{1'b0}}; // ready for next dot product
                done <= 1'b1;
            end else begin
                acc <= acc + prod;
            end
        end
    end
end

endmodule
