"""临时测试脚本：模拟 Claude 调用 MCP Server"""
import subprocess
import json

proc = subprocess.Popen(
    [
        r"C:\Users\Lenovo\Desktop\make_money\verilog-mcp-server\venv\Scripts\python.exe",
        r"C:\Users\Lenovo\Desktop\make_money\verilog-mcp-server\server.py",
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding="utf-8",
)

msgs = [
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"},
        },
    },
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "generate_testbench",
            "arguments": {
                "verilog_module_code": "module counter(input clk, rst_n); output reg [7:0] count; endmodule"
            },
        },
    },
]

for msg in msgs:
    proc.stdin.write(json.dumps(msg) + "\n")
proc.stdin.flush()
proc.stdin.close()

out = proc.stdout.read()
err = proc.stderr.read()
print("=== STDOUT ===")
print(out)
print("=== STDERR ===")
print(err)
print("=== RC:", proc.wait(timeout=5))
