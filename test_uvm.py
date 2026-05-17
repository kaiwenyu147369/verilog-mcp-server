from server import generate_uvm_env

code = """
module counter (
    input        clk,
    input        rst_n,
    input  [7:0] max_val,
    input        en,
    output reg [7:0] count,
    output       overflow
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'd0;
        else if (en && count >= max_val)
            count <= 8'd0;
        else if (en)
            count <= count + 1'd1;
    end
    assign overflow = (count >= max_val);
endmodule
"""

result = generate_uvm_env(code)
print(result)
print()
print("=== 总行数:", len(result.split("\n")), "===")
