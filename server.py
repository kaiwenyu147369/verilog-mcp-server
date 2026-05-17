"""
Verilog / SystemVerilog AI 辅助 MCP Server
工具: generate_testbench, check_lint, generate_uvm_env
v0.4.0
"""

import re
import asyncio

from mcp.server import Server, InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import types

# ============================================================
# 1. Server 初始化
# ============================================================
server = Server("verilog-mcp-server")

init_options = InitializationOptions(
    server_name="verilog-mcp-server",
    server_version="0.4.0",
    capabilities=types.ServerCapabilities(
        tools=types.ToolsCapability(),
    ),
)

# ============================================================
# 2. 工具注册
# ============================================================
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_testbench",
            description="输入一段 Verilog 模块代码，返回对应的 testbench 框架",
            inputSchema={
                "type": "object",
                "properties": {
                    "verilog_module_code": {
                        "type": "string",
                        "description": "Verilog 模块的完整代码",
                    }
                },
                "required": ["verilog_module_code"],
            },
        ),
        types.Tool(
            name="check_lint",
            description="检查 Verilog / SystemVerilog 代码中的常见问题：缺失 reset、latch 风险、case 缺 default、位宽不匹配等",
            inputSchema={
                "type": "object",
                "properties": {
                    "verilog_code": {
                        "type": "string",
                        "description": "需要检查的 Verilog / SystemVerilog 代码",
                    }
                },
                "required": ["verilog_code"],
            },
        ),
        types.Tool(
            name="generate_uvm_env",
            description="输入一个 DUT 的 Verilog 模块代码，生成对应的 UVM 验证环境骨架（Interface / Transaction / Sequence / Driver / Monitor / Agent / Scoreboard / Environment / Test / Top）",
            inputSchema={
                "type": "object",
                "properties": {
                    "verilog_module_code": {
                        "type": "string",
                        "description": "DUT 的 Verilog 模块完整代码",
                    }
                },
                "required": ["verilog_module_code"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "generate_testbench":
        result = generate_testbench(arguments["verilog_module_code"])
    elif name == "check_lint":
        result = check_lint(arguments["verilog_code"])
    elif name == "generate_uvm_env":
        result = generate_uvm_env(arguments["verilog_module_code"])
    else:
        raise ValueError(f"未知工具: {name}")
    return [types.TextContent(type="text", text=result)]


# ============================================================
# 3. 公共解析函数
# ============================================================

def _strip_comments(code: str) -> str:
    """去除单行和多行注释"""
    code = re.sub(r"//.*", "", code)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    return code


def _parse_ports(port_text: str) -> list[dict]:
    """
    从端口声明文本中提取每个端口的 name / direction / width。

    支持两种风格:
      - 新式: input clk, input rst_n, output [7:0] count
      - 旧式: input clk, rst_n, output reg [7:0] a, b
    返回 [{"direction": "input", "width": "7:0"|None, "name": "clk"}, ...]
    """
    port_text = " ".join(port_text.split())
    # 去掉 reg/wire/logic/signed 关键字
    port_text = re.sub(r"\b(reg|wire|logic|signed)\b\s*", "", port_text)

    ports = []
    # 在每个方向关键字之前切分
    segments = re.split(r"\s*(?=(?:input|output|inout)\b)", port_text)

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        m = re.match(r"(input|output|inout)\s+(.*)", seg)
        if not m:
            continue
        direction = m.group(1)
        rest = m.group(2).strip()

        current_width = None
        for part in rest.split(","):
            part = part.strip()
            if not part:
                continue
            # 检查是否有 [width]
            wm = re.match(r"\[([^\]]+)\]\s*(.*)", part)
            if wm:
                current_width = wm.group(1)
                name = wm.group(2).strip()
            else:
                name = part
            if name:
                ports.append(
                    {"direction": direction, "width": current_width, "name": name}
                )

    return ports


def _parse_module(code: str) -> dict | None:
    """
    解析 Verilog module 声明，返回:
      {"name": str, "ports": list[dict], "has_param": bool}
    解析失败返回 None。
    """
    clean = _strip_comments(code)
    m = re.search(
        r"module\s+(\w+)\s*(?:#\s*\(.*?\)\s*)?\s*\((.*?)\)\s*;",
        clean,
        re.DOTALL,
    )
    if not m:
        return None

    return {
        "name": m.group(1),
        "ports": _parse_ports(m.group(2)),
        "has_param": "#" in clean[m.start() : m.start() + 200],
    }


# ============================================================
# 4. generate_testbench
# ============================================================

def generate_testbench(verilog_module_code: str) -> str:
    mod = _parse_module(verilog_module_code)
    if not mod:
        return "// Error: 无法解析 module 声明，请检查代码格式"
    if not mod["ports"]:
        return f"// Error: 模块 '{mod['name']}' 的端口列表解析失败"

    return _build_testbench(mod["name"], mod["ports"])


def _build_testbench(module_name: str, ports: list[dict]) -> str:
    inputs = [p for p in ports if p["direction"] == "input"]
    outputs = [p for p in ports if p["direction"] == "output"]
    inouts = [p for p in ports if p["direction"] == "inout"]

    tb_name = f"{module_name}_tb"
    L = []

    def emit(*lines: str):
        L.extend(lines)

    emit(f"// Testbench for '{module_name}'")
    emit("// Auto-generated by Verilog MCP Server")
    emit("")
    emit("`timescale 1ns / 1ps")
    emit("")
    emit(f"module {tb_name};")
    emit("")

    # 信号声明
    for p in inputs:
        w = f"[{p['width']}] " if p["width"] else ""
        emit(f"    reg  {w}{p['name']};")
    for p in outputs:
        w = f"[{p['width']}] " if p["width"] else ""
        emit(f"    wire {w}{p['name']};")
    for p in inouts:
        w = f"[{p['width']}] " if p["width"] else ""
        emit(f"    wire {w}{p['name']};")
    emit("")

    # DUT 实例化
    emit("    // ---- DUT 实例化 ----")
    connections = ", ".join(f".{p['name']}({p['name']})" for p in ports)
    emit(f"    {module_name} u_dut (")
    emit(f"        {connections}")
    emit(f"    );")
    emit("")

    # 识别 clock / reset
    clk = next((p for p in ports if p["name"].lower() in ("clk", "clock")), None)
    rst = next(
        (p for p in ports if p["name"].lower() in ("rst", "reset", "rst_n", "reset_n")),
        None,
    )
    rst_low = rst and rst["name"].endswith("_n")

    if clk:
        emit("    // ---- Clock: 10ns 周期 (100MHz) ----")
        emit(f"    always #5 {clk['name']} = ~{clk['name']};")
        emit("")

    emit("    // ---- 测试激励 ----")
    emit("    initial begin")
    emit(f'        $dumpfile("{tb_name}.vcd");')
    emit(f"        $dumpvars(0, {tb_name});")
    emit("")

    for p in inputs:
        is_clk = clk and p["name"] == clk["name"]
        is_rst = rst and p["name"] == rst["name"]
        if is_clk:
            emit(f"        {p['name']} = 1'b0;")
        elif is_rst:
            emit(f"        {p['name']} = 1'b{'0' if rst_low else '1'};  // 复位激活")
        else:
            default = "1'b0" if not p["width"] else "'b0"
            emit(f"        {p['name']} = {default};")

    if rst:
        emit("")
        emit("        // 释放复位")
        emit("        #100;")
        emit(f"        {rst['name']} = 1'b{'1' if rst_low else '0'};")

    emit("")
    emit("        // TODO: 在这里写入你的测试激励")
    emit("        #100;")
    emit("")
    emit("        #200 $finish;")
    emit("    end")
    emit("")
    emit("endmodule")

    return "\n".join(L)


# ============================================================
# 5. check_lint
# ============================================================

def check_lint(verilog_code: str) -> str:
    """检查 Verilog 代码，返回 lint 报告"""
    code = verilog_code
    clean = _strip_comments(code)
    issues = []
    warnings = []
    info = []

    # ---- 检查 1: always_ff 没有复位 ----
    # 匹配: always @(posedge clk) 如果没有随后跟 if (rst) 或 if (!rst_n)
    seq_blocks = re.finditer(
        r"always\s*@\s*\(\s*(?:posedge|negedge)\s+(\w+)\s*\)",
        clean,
    )
    for sb in seq_blocks:
        clk_name = sb.group(1)
        # 从这个 always 往后找 200 个字符，看有没有 reset 相关
        trail = clean[sb.start() : sb.start() + 300]
        has_rst = bool(re.search(r"\b(?:rst|reset)\b", trail, re.IGNORECASE))
        has_if_rst = bool(
            re.search(
                r"if\s*\(\s*!?\s*(?:rst|reset)", trail, re.IGNORECASE
            )
        )
        if not has_rst:
            warnings.append(
                f"[W{len(warnings)+1}] always @(posedge {clk_name}) 未检测到复位信号 — 建议为时序逻辑添加复位"
            )
        elif has_rst and not has_if_rst:
            info.append(
                f"[I{len(info)+1}] 检测到复位信号但未找到 'if (rst)' 模式，请人工确认"
            )

    # ---- 检查 2: case 语句缺少 default ----
    case_matches = list(re.finditer(r"\b(case|casez|casex)\s*\(.+?\)", clean))
    for cm in case_matches:
        # 找到对应的 endcase
        end_pos = clean.find("endcase", cm.end())
        if end_pos == -1:
            continue
        block = clean[cm.start() : end_pos]
        if "default" not in block:
            kind = cm.group(1)
            issues.append(
                f"[I{len(issues)+1}] {kind} 语句缺少 default 分支 — "
                f"可能导致综合出 latch 或仿真出现 X 态"
            )

    # ---- 检查 3: always @(*) 中信号赋值不完整（latch 风险） ----
    comb_blocks = re.finditer(
        r"always\s*@\s*\(\s*\*\s*\)", clean
    )
    for cb in comb_blocks:
        # 粗略检查：always @(*) 中没有 else 的 if
        end_pos = clean.find("end", cb.end())
        if end_pos == -1:
            end_pos = cb.end() + 500
        block = clean[cb.start() : end_pos + 3]
        # 数 if 和 else 的数量
        if_count = len(re.findall(r"\bif\s*\(", block))
        else_count = len(re.findall(r"\belse\b", block))
        if if_count > else_count:
            warnings.append(
                f"[W{len(warnings)+1}] always @(*) 块中 if 语句 ({if_count}个) 多于 else ({else_count}个) "
                f"— 可能综合出 latch"
            )

    # ---- 检查 4: 位宽不匹配（简单启发式） ----
    # 查找 assign lhs = rhs 中 lhs 和 rhs 位宽可能不一致
    assigns = re.finditer(
        r"assign\s+(\w+)\s*=\s*(.+?);", clean
    )
    # 需要知道信号位宽，但这里没有完整的符号表
    # 只做最基础的检查：rhs 中有常量位宽与 lhs 不同
    for am in assigns:
        lhs = am.group(1)
        rhs = am.group(2)
        # rhs 中有显式位宽常量: N'dX
        rhs_width = re.search(r"(\d+)\s*'[bdh]", rhs)
        if rhs_width:
            w = int(rhs_width.group(1))
            if w == 1:
                continue  # 1-bit 常量通常没问题
        # 检查 rhs 中是否有缩减操作（结果永远是 1-bit）
        if re.search(r"[\&\|\^]~?\s*\w+", rhs):
            info.append(
                f"[I{len(info)+1}] assign {lhs} = ... 包含按位运算，请确认位宽匹配"
            )

    # ---- 检查 5: 时序 always 块中使用阻塞赋值 ----
    seq_blocks_ba = re.finditer(
        r"always\s*@\s*\(\s*(?:posedge|negedge)\s+\w+\s*\)",
        clean,
    )
    for sb in seq_blocks_ba:
        end_pos = clean.find("end", sb.end())
        if end_pos == -1:
            end_pos = sb.end() + 1000
        block = clean[sb.start() : end_pos + 3]
        # 去掉注释后的内容，查找阻塞赋值（= 但不是 <= == >= !=）
        # 匹配: 信号名 = 表达式; （排除 <= == >= != =~）
        blocking = re.findall(r"(?<![<>=!])\s=\s(?!~)", block)
        nonblocking = re.findall(r"<=", block)
        if blocking and len(blocking) > len(nonblocking):
            warnings.append(
                f"[W{len(warnings)+1}] 时序 always 块中检测到阻塞赋值（=），"
                f"建议使用非阻塞赋值（<=）以避免竞争"
            )

    # ---- 检查 6: 组合 always 块中使用非阻塞赋值 ----
    comb_blocks_nba = re.finditer(
        r"always\s*@\s*\(\s*\*\s*\)", clean
    )
    for cb in comb_blocks_nba:
        end_pos = clean.find("end", cb.end())
        if end_pos == -1:
            end_pos = cb.end() + 1000
        block = clean[cb.start() : end_pos + 3]
        if re.search(r"<=", block):
            warnings.append(
                f"[W{len(warnings)+1}] 组合 always @(*) 块中检测到非阻塞赋值（<=），"
                f"应使用阻塞赋值（=）"
            )

    # ---- 检查 7: 同一信号被多个 always 块驱动 ----
    always_blocks = list(
        re.finditer(
            r"always\s*[(@].*?end\b",
            clean,
            re.DOTALL,
        )
    )
    lhs_map: dict[str, list[int]] = {}
    for i, ab in enumerate(always_blocks):
        # 提取每个 always 块中赋值语句的左值
        assigns = re.findall(r"^\s*(\w+)\s*(?:<)?=", ab.group(0), re.MULTILINE)
        for sig in set(assigns):
            if sig not in lhs_map:
                lhs_map[sig] = []
            lhs_map[sig].append(i)
    for sig, blocks in lhs_map.items():
        if len(blocks) > 1:
            issues.append(
                f"[I{len(issues)+1}] 信号 '{sig}' 在 {len(blocks)} 个 always 块中被赋值 — "
                f"多个驱动可能导致竞争或综合错误"
            )

    # ---- 组装报告 ----
    lines = [
        f"// Lint Report — {len(issues)} 个严重问题, "
        f"{len(warnings)} 个警告, {len(info)} 个提示",
        "// ====",
    ]

    if issues:
        lines.append("")
        lines.append("// [ISSUES] 需要修复:")
        for s in issues:
            lines.append(s)
        lines.append("")

    if warnings:
        lines.append("// [WARNINGS] 建议检查:")
        for s in warnings:
            lines.append(s)
        lines.append("")

    if info:
        lines.append("// [INFO] 提示:")
        for s in info:
            lines.append(s)
        lines.append("")

    if not issues and not warnings and not info:
        lines.append("// [OK] 未检测到明显问题")

    return "\n".join(lines)


# ============================================================
# 6. generate_uvm_env
# ============================================================

def generate_uvm_env(verilog_module_code: str) -> str:
    mod = _parse_module(verilog_module_code)
    if not mod:
        return "// Error: 无法解析 module 声明"
    if not mod["ports"]:
        return f"// Error: 模块 '{mod['name']}' 的端口列表解析失败"

    return _build_uvm_env(mod["name"], mod["ports"])


def _build_uvm_env(name: str, ports: list[dict]) -> str:
    """生成完整 UVM 验证环境，按文件分段输出"""
    inputs = [p for p in ports if p["direction"] == "input"]
    outputs = [p for p in ports if p["direction"] == "output"]
    all_ports = ports

    clk = next((p for p in ports if p["name"].lower() in ("clk", "clock")), None)
    rst = next(
        (p for p in ports if p["name"].lower() in ("rst", "reset", "rst_n", "reset_n")),
        None,
    )
    # 非时钟/非复位的纯数据信号
    data_inputs = [
        p for p in inputs if p != clk and (not rst or p != rst)
    ]
    data_outputs = [p for p in outputs if p != clk and (not rst or p != rst)]

    B = []  # 输出缓冲区

    def sep(title: str):
        B.append(f"// {'='*60}")
        B.append(f"// ===== FILE: {title} =====")
        B.append(f"// {'='*60}")
        B.append("")

    def emit(*lines: str):
        B.extend(lines)

    # ================================================================
    # 1. Interface
    # ================================================================
    sep(f"{name}_if.sv // Interface")

    emit(f"interface {name}_if (input {clk['name']}" if clk else f"interface {name}_if (")
    if rst:
        emit(f", input {rst['name']}")
    emit(");")
    emit("")
    # 信号声明
    for p in all_ports:
        w = f"[{p['width']}] " if p["width"] else "  "
        emit(f"    logic {w}{p['name']};")
    emit("")

    # Clocking block
    if clk:
        emit(f"    // ---- Clocking block (Driver 侧) ----")
        emit(f"    clocking drv_cb @(posedge {clk['name']});")
        for p in data_inputs:
            w = f"[{p['width']}] " if p["width"] else "      "
            emit(f"        output {w}{p['name']};")
        emit(f"    endclocking")
        emit("")
        emit(f"    // ---- Clocking block (Monitor 侧) ----")
        emit(f"    clocking mon_cb @(posedge {clk['name']});")
        for p in all_ports:
            w = f"[{p['width']}] " if p["width"] else "      "
            emit(f"        input {w}{p['name']};")
        emit(f"    endclocking")
    emit("")
    emit("endinterface")

    # ================================================================
    # 2. Transaction
    # ================================================================
    sep(f"{name}_transaction.sv // UVM Sequence Item")

    emit(f"class {name}_transaction extends uvm_sequence_item;")
    emit(f"    `uvm_object_utils({name}_transaction)")
    emit("")
    # 数据字段（映射 DUT 数据端口）
    for p in data_inputs + data_outputs:
        w = f"[{p['width']}] " if p["width"] else "        "
        emit(f"    rand logic {w}{p['name']};")
    emit("")
    # Constraint
    emit("    // ---- 约束（按需修改）----")
    emit("    constraint c_default {")
    if data_inputs:
        emit(f"        // TODO: 添加有效数据约束")
    emit("    }")
    emit("")
    emit(f"    function new(string name = \"{name}_transaction\");")
    emit(f"        super.new(name);")
    emit(f"    endfunction")
    emit("")
    # do_print
    emit("    function void do_print(uvm_printer printer);")
    emit("        super.do_print(printer);")
    emit("        printer.print_string(\"kind\", \"transaction\");")
    for p in data_inputs + data_outputs:
        emit(f'        printer.print_field_int(\"{p["name"]}\", {p["name"]}, $bits({p["name"]}));')
    emit("    endfunction")
    emit("")
    emit("endclass")

    # ================================================================
    # 3. Sequence
    # ================================================================
    sep(f"{name}_sequence.sv // UVM Sequence")

    emit(f"class {name}_sequence extends uvm_sequence #({name}_transaction);")
    emit(f"    `uvm_object_utils({name}_sequence)")
    emit("")
    emit(f"    function new(string name = \"{name}_sequence\");")
    emit(f"        super.new(name);")
    emit(f"    endfunction")
    emit("")
    emit("    task body();")
    emit(f"        {name}_transaction tx;")
    emit("")
    emit("        repeat (10) begin")
    emit(f"            tx = {name}_transaction::type_id::create(\"tx\");")
    emit("            start_item(tx);")
    emit("            if (!tx.randomize()) begin")
    emit('                `uvm_error("SEQ", "Randomization failed")')
    emit("            end")
    emit("            finish_item(tx);")
    emit("        end")
    emit("    endtask")
    emit("")
    emit("endclass")

    # ================================================================
    # 4. Driver
    # ================================================================
    sep(f"{name}_driver.sv // UVM Driver")

    emit(f"class {name}_driver extends uvm_driver #({name}_transaction);")
    emit(f"    `uvm_component_utils({name}_driver)")
    emit("")
    emit(f"    virtual {name}_if vif;")
    emit("")
    emit(f"    function new(string name = \"{name}_driver\", uvm_component parent = null);")
    emit(f"        super.new(name, parent);")
    emit(f"    endfunction")
    emit("")
    emit("    virtual function void build_phase(uvm_phase phase);")
    emit("        super.build_phase(phase);")
    emit("        if (!uvm_config_db #(virtual {0}_if)::get(this, \"\", \"vif\", vif)) begin".format(name))
    emit('            `uvm_fatal("DRV", "No virtual interface in config_db")')
    emit("        end")
    emit("    endfunction")
    emit("")
    emit("    virtual task run_phase(uvm_phase phase);")
    emit(f"        {name}_transaction tx;")
    emit("        forever begin")
    emit("            seq_item_port.get_next_item(tx);")
    emit("            // TODO: 驱动信号到 interface")
    # Drive data inputs
    for p in data_inputs:
        emit(f"            vif.drv_cb.{p['name']} <= tx.{p['name']};")
    emit("            seq_item_port.item_done();")
    emit("        end")
    emit("    endtask")
    emit("")
    emit("endclass")

    # ================================================================
    # 5. Monitor
    # ================================================================
    sep(f"{name}_monitor.sv // UVM Monitor")

    emit(f"class {name}_monitor extends uvm_monitor;")
    emit(f"    `uvm_component_utils({name}_monitor)")
    emit("")
    emit(f"    virtual {name}_if vif;")
    emit(f"    uvm_analysis_port #({name}_transaction) item_collected_port;")
    emit("")
    emit(f"    function new(string name = \"{name}_monitor\", uvm_component parent = null);")
    emit(f"        super.new(name, parent);")
    emit(f"    endfunction")
    emit("")
    emit("    virtual function void build_phase(uvm_phase phase);")
    emit("        super.build_phase(phase);")
    emit("        item_collected_port = new(\"item_collected_port\", this);")
    emit("        if (!uvm_config_db #(virtual {0}_if)::get(this, \"\", \"vif\", vif)) begin".format(name))
    emit('            `uvm_fatal("MON", "No virtual interface in config_db")')
    emit("        end")
    emit("    endfunction")
    emit("")
    emit("    virtual task run_phase(uvm_phase phase);")
    emit(f"        {name}_transaction tx;")
    emit("        forever begin")
    emit("            @(vif.mon_cb);")
    emit(f"            tx = {name}_transaction::type_id::create(\"tx\");")
    for p in data_inputs + data_outputs:
        emit(f"            tx.{p['name']} = vif.mon_cb.{p['name']};")
    emit("            item_collected_port.write(tx);")
    emit("        end")
    emit("    endtask")
    emit("")
    emit("endclass")

    # ================================================================
    # 6. Agent
    # ================================================================
    sep(f"{name}_agent.sv // UVM Agent")

    emit(f"class {name}_agent extends uvm_agent;")
    emit(f"    `uvm_component_utils({name}_agent)")
    emit("")
    emit(f"    {name}_driver     drv;")
    emit(f"    {name}_monitor    mon;")
    emit(f"    uvm_sequencer #({name}_transaction)  sqr;")
    emit(f"    virtual {name}_if  vif;")
    emit("")
    emit(f"    function new(string name = \"{name}_agent\", uvm_component parent = null);")
    emit(f"        super.new(name, parent);")
    emit(f"    endfunction")
    emit("")
    emit("    virtual function void build_phase(uvm_phase phase);")
    emit("        super.build_phase(phase);")
    emit("")
    emit("        if (!uvm_config_db #(virtual {0}_if)::get(this, \"\", \"vif\", vif)) begin".format(name))
    emit('            `uvm_fatal("AGT", "No virtual interface in config_db")')
    emit("        end")
    emit(f"        uvm_config_db #(virtual {name}_if)::set(this, \"*\", \"vif\", vif);")
    emit("")
    # Active vs passive
    emit("        if (get_is_active() == UVM_ACTIVE) begin")
    emit(f"            drv = {name}_driver::type_id::create(\"drv\", this);")
    emit(f"            sqr = uvm_sequencer #({name}_transaction)::type_id::create(\"sqr\", this);")
    emit("        end")
    emit(f"        mon = {name}_monitor::type_id::create(\"mon\", this);")
    emit("    endfunction")
    emit("")
    emit("    virtual function void connect_phase(uvm_phase phase);")
    emit("        super.connect_phase(phase);")
    emit("        if (get_is_active() == UVM_ACTIVE) begin")
    emit("            drv.seq_item_port.connect(sqr.seq_item_export);")
    emit("        end")
    emit("    endfunction")
    emit("")
    emit("endclass")

    # ================================================================
    # 7. Scoreboard
    # ================================================================
    sep(f"{name}_scoreboard.sv // UVM Scoreboard")

    emit(f"class {name}_scoreboard extends uvm_scoreboard;")
    emit(f"    `uvm_component_utils({name}_scoreboard)")
    emit("")
    emit(f"    uvm_analysis_imp #({name}_transaction, {name}_scoreboard) item_imp;")
    emit("")
    emit(f"    function new(string name = \"{name}_scoreboard\", uvm_component parent = null);")
    emit(f"        super.new(name, parent);")
    emit(f"    endfunction")
    emit("")
    emit("    virtual function void build_phase(uvm_phase phase);")
    emit("        super.build_phase(phase);")
    emit(f"        item_imp = new(\"item_imp\", this);")
    emit("    endfunction")
    emit("")
    emit("    virtual function void write({0}_transaction tx);".format(name))
    emit("        // TODO: 实现比对逻辑")
    emit('        `uvm_info("SCB", $sformatf("Received tx: %s", tx.convert2string()), UVM_MEDIUM)')
    emit("    endfunction")
    emit("")
    emit("endclass")

    # ================================================================
    # 8. Environment
    # ================================================================
    sep(f"{name}_env.sv // UVM Environment")

    emit(f"class {name}_env extends uvm_env;")
    emit(f"    `uvm_component_utils({name}_env)")
    emit("")
    emit(f"    {name}_agent       agent;")
    emit(f"    {name}_scoreboard  scb;")
    emit("")
    emit(f"    function new(string name = \"{name}_env\", uvm_component parent = null);")
    emit(f"        super.new(name, parent);")
    emit(f"    endfunction")
    emit("")
    emit("    virtual function void build_phase(uvm_phase phase);")
    emit("        super.build_phase(phase);")
    emit(f"        agent = {name}_agent::type_id::create(\"agent\", this);")
    emit(f"        scb   = {name}_scoreboard::type_id::create(\"scb\", this);")
    emit("    endfunction")
    emit("")
    emit("    virtual function void connect_phase(uvm_phase phase);")
    emit("        super.connect_phase(phase);")
    emit("        agent.mon.item_collected_port.connect(scb.item_imp);")
    emit("    endfunction")
    emit("")
    emit("endclass")

    # ================================================================
    # 9. Test
    # ================================================================
    sep(f"{name}_test.sv // UVM Test")

    emit(f"class {name}_test extends uvm_test;")
    emit(f"    `uvm_component_utils({name}_test)")
    emit("")
    emit(f"    {name}_env     env;")
    emit(f"    {name}_sequence seq;")
    emit("")
    emit(f"    function new(string name = \"{name}_test\", uvm_component parent = null);")
    emit(f"        super.new(name, parent);")
    emit(f"    endfunction")
    emit("")
    emit("    virtual function void build_phase(uvm_phase phase);")
    emit("        super.build_phase(phase);")
    emit(f"        env = {name}_env::type_id::create(\"env\", this);")
    emit("    endfunction")
    emit("")
    emit("    virtual task run_phase(uvm_phase phase);")
    emit("        super.run_phase(phase);")
    emit("        phase.raise_objection(this);")
    emit(f"        seq = {name}_sequence::type_id::create(\"seq\");")
    emit("        seq.start(env.agent.sqr);")
    emit("        #1000;")
    emit("        phase.drop_objection(this);")
    emit("    endtask")
    emit("")
    emit("endclass")

    # ================================================================
    # 10. Top-level Testbench
    # ================================================================
    sep(f"{name}_tb_top.sv // 顶层 Testbench")

    emit("`include \"uvm_macros.svh\"")
    emit("import uvm_pkg::*;")
    emit("")
    emit(f"// 以下 include 在实际项目中改为 `include")
    emit(f"// `include \"{name}_transaction.sv\"")
    emit(f"// `include \"{name}_sequence.sv\"")
    emit(f"// `include \"{name}_driver.sv\"")
    emit(f"// `include \"{name}_monitor.sv\"")
    emit(f"// `include \"{name}_agent.sv\"")
    emit(f"// `include \"{name}_scoreboard.sv\"")
    emit(f"// `include \"{name}_env.sv\"")
    emit(f"// `include \"{name}_test.sv\"")
    emit("")
    emit(f"module {name}_tb_top;")
    emit("")
    # 参数声
    if clk:
        emit(f"    reg {clk['name']};")
    if rst:
        emit(f"    reg {rst['name']};")
    emit("")
    # Clock
    if clk:
        emit(f"    // ---- Clock: 10ns 周期 (100MHz) ----")
        emit(f"    always #5 {clk['name']} = ~{clk['name']};")
        emit("")
    # Reset
    if rst:
        rst_low = rst["name"].endswith("_n")
        emit(f"    // ---- Reset ----")
        emit(f"    initial begin")
        emit(f"        {rst['name']} = 1'b{'0' if rst_low else '1'};")
        emit(f"        #100 {rst['name']} = 1'b{'1' if rst_low else '0'};")
        emit(f"    end")
        emit("")
    # Interface 实例
    emit(f"    {name}_if dut_if (")
    if clk:
        emit(f"        .{clk['name']}({clk['name']})")
        if rst:
            emit(f"        ,.{rst['name']}({rst['name']})")
    elif rst:
        emit(f"        .{rst['name']}({rst['name']})")
    emit(f"    );")
    emit("")
    # DUT 实例化
    emit(f"    // ---- DUT 实例化 ----")
    emit(f"    {name} u_dut (")
    dut_conns = ", ".join(f".{p['name']}(dut_if.{p['name']})" for p in all_ports)
    emit(f"        {dut_conns}")
    emit(f"    );")
    emit("")
    # UVM 启动
    emit(f"    initial begin")
    emit(f"        uvm_config_db #(virtual {name}_if)::set(null, \"*\", \"vif\", dut_if);")
    emit(f"        run_test(\"{name}_test\");")
    emit(f"    end")
    emit("")
    emit("endmodule")

    return "\n".join(B)


# ============================================================
# 7. 启动入口
# ============================================================

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, init_options)


if __name__ == "__main__":
    asyncio.run(main())
