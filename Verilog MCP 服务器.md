# Verilog MCP 服务器 — 项目工作整理

> 最后更新：2026-05-17
> 版本：v0.4.0
> 仓库：https://github.com/kaiwenyu147369/verilog-mcp-server

---

## 一、项目概述

在 Claude Code 里运行的 Verilog / SystemVerilog AI 辅助工具。通过 MCP（Model Context Protocol）协议，提供 3 个工具、7 条 RTL 检查规则、10 组件 UVM 验证环境生成。

**为什么选这个项目**：芯片设计 AI 工具是蓝海，中文圈零竞争；直接服务本人的微电子专业课（数电、Verilog）。

**目标用户**：芯片设计工程师、微电子学生、EE 学院在校生。

**协议**：MIT License（最宽松开源协议，允许商用）。

---

## 二、技术架构

| 组件 | 详情 |
|------|------|
| 协议 | MCP（Model Context Protocol）stdio JSON-RPC |
| SDK | Python MCP SDK 1.27.1 |
| API 模式 | `@server.list_tools()` + `@server.call_tool()` 两段式装饰器 |
| 解析器 | 正则表达式（非完整 SystemVerilog parser） |
| 代码量 | 810+ 行 |
| 运行环境 | Windows venv，Python 3.x |
| 后端模型 | DeepSeek V4（通过 Anthropic 兼容层） |

### MCP 配置

`.mcp.json`（workspace 根目录）：
```json
{
  "mcpServers": {
    "verilog-mcp-server": {
      "command": "C:\\...\\venv\\Scripts\\python.exe",
      "args": ["C:\\...\\verilog-mcp-server\\server.py"]
    }
  }
}
```

`settings.json`：
```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["verilog-mcp-server"]
}
```

---

## 三、工具详解

### 1. `generate_testbench` — Testbench 生成
- 输入：Verilog 模块代码
- 输出：完整 testbench（timescale、信号声明、DUT 实例化、100MHz clock、reset 序列、VCD dump、finish）
- 自动识别 clock/reset 端口
- 自动检测低有效复位（`_n` 后缀）
- 支持新旧两种端口声明风格

### 2. `check_lint` — RTL 代码检查（7 条规则）

| # | 规则 | 严重级别 |
|---|------|----------|
| 1 | 时序 always 块缺少 reset | WARNING |
| 2 | case/casez/casex 缺少 default | ISSUE |
| 3 | 组合 always @(*) 中 if/else 不完整（latch 风险） | WARNING |
| 4 | assign 位宽不匹配（启发式） | INFO |
| 5 | 时序 always 块中使用阻塞赋值（=） | WARNING |
| 6 | 组合 always 块中使用非阻塞赋值（<=） | WARNING |
| 7 | 同一信号在多个 always 块中被驱动 | ISSUE |

### 3. `generate_uvm_env` — UVM 验证环境生成

一次生成 10 个组件文件：
```
Interface → Transaction → Sequence → Driver → Monitor
→ Agent → Scoreboard → Environment → Test → Top
```

关键设计决策：
- `drv_cb` 只含数据信号（不含 clock/reset）
- `mon_cb` 包含所有端口
- `do_print` 使用 `$bits()` 避免编译错误
- Scoreboard 比对逻辑留了 TODO

---

## 四、开发历程（4 个 Session，约 15 小时）

### Session 1：项目脚手架
- 调研 MCP 协议和 SDK
- `mkdir` 项目目录、`python -m venv venv`、`pip install mcp`
- SDK 1.27.1 API 与网上所有教程不同 → 翻源码解决
- 跑通 `generate_testbench`

### Session 2：Claude Code 端到端集成
- `.mcp.json` 位置踩坑（必须 workspace 根目录）
- `settings.json` 字段名踩坑（`mcpServers` → `enableAllProjectMcpServers`）
- 端到端验证：`tools/list` → `tools/call` → 返回结果

### Session 3：`check_lint` + `generate_uvm_env`
- 实现 4 条 lint 规则
- Windows GBK 编码下 emoji 崩 → 换 ASCII
- 旧式端口解析 `input clk, rst_n` 失败 → 方向关键字切分修复
- 实现 10 组件 UVM 环境生成
- drv_cb 纠正（去掉 clk/rst），`$bits()` 修复

### Session 4：Week 3+4 — 文档 + 发布
- README.md 编写
- lint 规则 4 条 → 7 条
- 端口解析支持 `signed` 关键字
- GitHub 仓库创建（git init + gh auth + repo create）
- GitHub Profile README 创建
- docs/ 目录：Reddit / HN / V2EX 分发帖 + 复盘博客 + MCP 目录提交指南
- 发布：GitHub topics（8 个）+ r/FPGA + r/chipdesign + mcp.so + awesome-mcp-servers PR

---

## 五、分发矩阵

| 渠道 | 状态 | 备注 |
|------|------|------|
| GitHub 仓库 | ✅ | https://github.com/kaiwenyu147369/verilog-mcp-server |
| GitHub Profile README | ✅ | https://github.com/kaiwenyu147369/kaiwenyu147369 |
| GitHub 8 topics | ✅ | mcp-server, verilog, systemverilog, chip-design, eda-tools, uvm, claude-code, mcp |
| Reddit r/FPGA | ✅ | 已发帖 |
| Reddit r/chipdesign | ✅ | 已发帖 |
| mcp.so | ✅ | 已提交 |
| awesome-mcp-servers PR | ✅ | 已提交 PR |
| V2EX | ⏸️ | 需要邀请码 |
| Hacker News | ⏸️ | 禁止注册 |
| Smithery.ai | ⏸️ | 不适合本地 stdio MCP |

---

## 六、已知局限

1. 端口解析用正则，不是完整 SystemVerilog tokenizer——复杂参数化端口可能失败
2. UVM Scoreboard 比对逻辑是 TODO
3. Lint 检查是启发式的，没有完整类型推导
4. 不支持 interface / modport / struct 端口

---

## 七、文件结构

```
verilog-mcp-server/
├── server.py              ← 主程序（810+ 行）
├── README.md              ← 项目文档（英文）
├── .gitignore
├── test_server.py         ← MCP 协议端到端测试
├── test_v2.py             ← 端口解析 + lint 测试
├── test_uvm.py            ← UVM 环境生成测试
├── docs/
│   ├── reddit-post.md     ← Reddit 分发帖
│   ├── hn-post.md         ← HN Show HN 帖
│   ├── v2ex-post.md       ← V2EX 分享创造帖
│   ├── blog-retrospective.md ← 复盘博客
│   └── mcp-directory-submissions.md ← MCP 目录提交指南
└── venv/                  ← Python 虚拟环境
```

---

## 八、后续路线图

| 优先级 | 任务 | 预计时间 |
|--------|------|----------|
| P0 | 发 dev.to 复盘博客 | 10 分钟 |
| P1 | 第 4 个工具：`generate_assertions`（SVA 断言生成） | 1 个 Session |
| P2 | 端口解析升级为简单 tokenizer（处理嵌套括号） | 1 个 Session |
| P3 | UVM Scoreboard 自动比对逻辑 | 1 个 Session |
| P4 | Lint 规则扩展：signed/unsigned 混用、跨时钟域检查 | 1 个 Session |
| P5 | 30s Demo GIF 录制 + 更新 README | 30 分钟 |

---

## 九、关键踩坑记录

1. **MCP SDK 1.27.1 API 变更**：`@server.tool()` 废弃，改为 `@server.list_tools()` + `@server.call_tool()`
2. **`.mcp.json` 位置**：必须放 workspace 根目录，不能放子目录
3. **settings.json schema**：配置用 `enableAllProjectMcpServers` + `enabledMcpjsonServers`，不是 `mcpServers`
4. **Windows GBK**：Python 输出 emoji 会 `UnicodeEncodeError`，CLI 工具全部用 ASCII
5. **端口解析**：旧式 `input clk, rst_n` 需要方向关键字切分，不能用简单逗号分割
6. **uvm_do_print**：`$sformatf` 内不能直接用宽度字符串 `"7:0"`，要用 `$bits()`
7. **drv_cb**：Driver 的 clocking block 不应该驱动 clk 和 rst
