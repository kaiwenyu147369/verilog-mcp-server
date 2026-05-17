"""临时测试：端口解析 + lint"""
import sys
sys.path.insert(0, r"C:\Users\Lenovo\Desktop\make_money\verilog-mcp-server")

from server import generate_testbench, check_lint

# 测试 1: 旧式端口写法
code1 = """
module simple (
    input clk, rst_n, en,
    output reg [7:0] result
);
    always @(posedge clk) begin
        result <= result + 1;
    end
endmodule
"""
print("=== 测试 1: 旧式端口 ===")
print(generate_testbench(code1))
print()
print("=== 测试 2: check_lint ===")
print(check_lint(code1))

# 测试 3: 有问题的代码
print()
print("=== 测试 3: lint 检查有问题的代码 ===")
bad_code = """
module bad (
    input clk, rst_n,
    input [3:0] sel,
    output reg [7:0] out
);
    always @(*) begin
        if (sel == 4'h0)
            out = 8'h00;
        else if (sel == 4'h1)
            out = 8'h01;
    end

    always @(posedge clk) begin
        out <= out + 1;
    end

    case (sel)
        4'h0: out = 8'hff;
        4'h1: out = 8'hee;
    endcase
endmodule
"""
print(check_lint(bad_code))
