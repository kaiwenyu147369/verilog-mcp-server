# Verilog MCP Server

AI-powered Verilog / SystemVerilog development tools for Claude Code. Generate testbenches, lint RTL code, and scaffold UVM verification environments — all from within your editor.

> **Status:** v0.3.0 — 3 tools, end-to-end verified in Claude Code.

## Why

Chip design EDA tools are decades old. AI-assisted hardware development is a blue ocean. This MCP server brings Verilog / SystemVerilog code generation and linting directly into Claude Code, so you can:

- Generate testbench boilerplate from a module declaration in seconds
- Catch common RTL bugs (missing reset, latch inference, case without default) before simulation
- Scaffold a full UVM verification environment with proper clocking blocks, sequencers, and scoreboards

## Tools

| Tool | Description |
|------|-------------|
| `generate_testbench` | Generate a Verilog testbench skeleton from a module definition |
| `check_lint` | Static lint checks: missing reset, case-default, latch risk, width mismatch |
| `generate_uvm_env` | Generate a 10-component UVM verification environment |

### `generate_testbench`

Input: a Verilog module. Output: a complete testbench with clock generation, reset sequence, DUT instantiation, `$dumpfile` / `$dumpvars`, and a TODO placeholder for custom test stimuli.

- Auto-detects clock and reset ports
- Handles active-low reset (`rst_n` suffix)
- Supports both new-style (`input clk, input rst_n`) and old-style (`input clk, rst_n`) port declarations
- 100MHz default clock (10ns period)

### `check_lint`

Four categories of checks:

1. **Sequential always block without reset** — WARNING
2. **case/casez/casex without default** — ISSUE (latches / X-states)
3. **Incomplete if-assignments in combinational always blocks** — WARNING (latch inference risk)
4. **Width mismatch heuristics** — INFO

### `generate_uvm_env`

Generates 10 UVM component files separated by `// ===== FILE: filename.sv =====` markers:

`interface` → `transaction` → `sequence` → `driver` → `monitor` → `agent` → `scoreboard` → `environment` → `test` → `top`

- Proper `drv_cb` (outputs-only clocking block) and `mon_cb` (inputs-only) design
- `uvm_analysis_port` for monitor → scoreboard communication
- Active/passive agent mode
- TODO placeholders in scoreboard and constraints

## Installation

```bash
# 1. Clone
git clone https://github.com/kaiwenyu147369/verilog-mcp-server.git
cd verilog-mcp-server

# 2. Create virtual environment
python -m venv venv

# 3. Activate & install
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install mcp
```

## Usage with Claude Code

Add to your workspace `.mcp.json`:

```json
{
  "mcpServers": {
    "verilog-mcp-server": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\verilog-mcp-server\\server.py"]
    }
  }
}
```

Then in Claude Code settings (`~/.claude/settings.json`):

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["verilog-mcp-server"]
}
```

Restart VSCode, and the tools will appear in Claude Code.

## Quick Test

```bash
# Activate venv first, then:
python test_uvm.py
python test_v2.py
```

## Tech Stack

- **Python MCP SDK 1.27.1** — `@server.list_tools()` + `@server.call_tool()` (two-decorator API)
- **stdio JSON-RPC** — Claude Code communicates via stdin/stdout
- **Regex-based parsing** — No SystemVerilog compiler dependency

## Known Limitations

- Port parser uses regex, not a full SystemVerilog tokenizer — deeply nested parentheses in complex parameterized ports may not parse correctly
- UVM Scoreboard comparison logic is a TODO placeholder
- Lint checks are heuristic; no full elaboration or type system
- No interface / struct / modport support in port parsing

## Roadmap

- [ ] v0.4.0 — 4th tool (`generate_assertions` or `analyze_waveform`)
- [ ] Port parser upgrade to simple tokenizer
- [ ] Additional lint rules (blocking/non-blocking assignment check, signed/unsigned warnings)
- [ ] UVM Scoreboard auto-comparison logic
- [ ] Multi-file project support

## License

MIT
