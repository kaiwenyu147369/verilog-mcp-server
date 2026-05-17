# V2EX 帖子 — 分享创造节点

## 标题：Verilog MCP Server — 把 AI 辅助芯片设计工具塞进 Claude Code，大一学生的第一个独立开发项目

**正文：**

### 背景

我是电子科技大学格拉斯哥学院大一学生，微电子专业。上数电课、写 Verilog 的时候发现，testbench 和 UVM 验证环境的样板代码太多了——每个模块都要重复写差不多的东西。

正好最近在学 AI 工具链，发现 Anthropic 的 MCP（Model Context Protocol）协议可以让 Claude Code 在编辑器里直接调用外部工具。于是花了三周课余时间，做了这个 MCP Server。

### 它能干什么

在 Claude Code 里直接调用三个工具：

1. **生成 testbench** — 把 Verilog 模块代码扔进去，自动出 testbench：timescale、信号声明、DUT 实例化、clock 生成（100MHz）、reset 序列、VCD dump，全给你写好。支持新旧两种端口声明风格。

2. **RTL 代码检查** — 7 项自动检查：
   - 时序逻辑缺 reset → 警告
   - case 语句缺 default → 严重问题
   - 组合逻辑 if/else 不完整 → latch 风险警告
   - 位宽不匹配 → 提示
   - 时序块里用阻塞赋值 → 警告
   - 组合块里用非阻塞赋值 → 警告
   - 同一信号多 always 块驱动 → 严重问题

3. **生成 UVM 验证环境** — 10 个文件一次性生成：Interface / Transaction / Sequence / Driver / Monitor / Agent / Scoreboard / Environment / Test / Top，含 clocking block 和 analysis port

### 技术栈

- Python MCP SDK 1.27.1
- stdio JSON-RPC 和 Claude Code 通信
- 810 行代码，MIT 开源

### GitHub

https://github.com/kaiwenyu147369/verilog-mcp-server

### 局限（诚实交代）

- 端口解析用的正则，不是完整 SystemVerilog parser，复杂参数化端口可能解析失败
- UVM Scoreboard 的比对逻辑还是 TODO
- Lint 检查是启发式的，没有完整类型推导

---

**发布建议：** V2EX 的"分享创造"节点。标题带"大一学生"会增加点击率但不要过度依赖这个标签——重点是工具本身的价值。发完后不要反复顶帖。
