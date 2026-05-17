# Reddit Post — r/FPGA + r/chipdesign

This is the draft for posting to Reddit. Post to **r/FPGA** and **r/chipdesign** separately (not crosspost — copy-paste).

---

## Title: I built a free MCP server that generates Verilog testbenches, RTL linting, and UVM scaffolding inside Claude Code

**Body:**

I'm a first-year microelectronics student, and I've been frustrated with how much boilerplate we write in chip design courses. So over the past few weeks I built an MCP (Model Context Protocol) server that brings Verilog/SystemVerilog tooling directly into Claude Code.

**What it does:**
- `generate_testbench` — paste a Verilog module, get a complete testbench with clock, reset, DUT instantiation, and VCD dumping
- `check_lint` — 7 static checks: missing reset, case-without-default, latch inference risk, width mismatch, blocking assignment in sequential blocks, non-blocking in combinational blocks, and multi-driver detection
- `generate_uvm_env` — generates all 10 UVM components (interface, transaction, sequence, driver, monitor, agent, scoreboard, env, test, top) from a single DUT module

**Why MCP?** MCP lets Claude Code call these tools directly while you code. You don't leave your editor. Type "generate a testbench for this module" and Claude does it, using the actual tool (not guessing Verilog from training data).

**Repo:** https://github.com/kaiwenyu147369/verilog-mcp-server

**Tech:** Python MCP SDK 1.27.1, stdio JSON-RPC, 810 lines, 3 tools, MIT license.

It's early stage (v0.4.0). The port parser uses regex so complex parameterized ports might not parse perfectly. The UVM scoreboard comparison logic is TODO. But the fundamentals work — I've verified all 3 tools end-to-end in Claude Code.

Would love feedback from actual chip designers. What other Verilog/SystemVerilog tools would you want inside your editor?

---

**Posting tips:**
- r/FPGA: ~50K members, active, mostly FPGA engineers
- r/chipdesign: ~20K members, more ASIC-focused
- Post on a weekday morning US time for max visibility
- Set flair to "Tool" or "Project" if available
