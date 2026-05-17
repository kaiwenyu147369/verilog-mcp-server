# Hacker News — Show HN

## Title: Show HN: Verilog MCP Server — AI-assisted RTL linting and UVM scaffolding in Claude Code

**Body:**

I built an MCP (Model Context Protocol) server that adds Verilog/SystemVerilog development tools to Claude Code.

Three tools so far:
1. Testbench generator — paste a module, get clock/reset/DUT/VCD boilerplate
2. RTL linter — 7 checks (missing reset, case-default, latch risk, blocking/non-blocking assignment errors, multi-driver detection)
3. UVM environment generator — 10-component UVM scaffold from a single DUT (interface → transaction → sequence → driver → monitor → agent → scoreboard → env → test → top)

Why: chip design EDA workflows haven't changed much in decades. AI-assisted development exists for software but barely touches hardware design. MCP makes it possible to bring these tools into the editor without leaving your workflow.

Tech: Python MCP SDK 1.27.1, regex-based Verilog parser, MIT license. 810 lines.

Repo: https://github.com/kaiwenyu147369/verilog-mcp-server

It's early. The parser is regex, not a real SystemVerilog frontend. The scoreboard comparison is still TODO. But it's working end-to-end in Claude Code today.

I'm a first-year microelectronics student — this is my first indie hacker project. Would appreciate any feedback from folks doing real chip design work.

---

**Timing:** Post Tuesday-Thursday morning US Eastern time. Don't post on weekends.
**Expected traction:** HN audience overlaps partially with chip design. The "student builds tool" angle might help. Keep expectations low — this is a niche, not a general web dev tool.
