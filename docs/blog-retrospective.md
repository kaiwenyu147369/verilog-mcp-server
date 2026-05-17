# 从 0 到 1：我如何用三周业余时间构建 Verilog MCP Server

> 一个微电子大一学生的第一个独立开发项目复盘

---

## 起点：为什么是 Verilog + MCP

2026 年 5 月，我决定做点什么。AI 对时代的冲击太大了，我不想做一个只会刷绩点的"传统好学生"——那不是我。

AI + 芯片设计的交集几乎是空白。MCP（Model Context Protocol）是 Anthropic 推出的开放协议，让 LLM 通过 stdio JSON-RPC 调用外部工具。这个生态 2026 年还非常早期，做的人少，竞争几乎为零。

我选了 Verilog / SystemVerilog 作为第一个切入点。原因很简单：我本专业就是微电子，数电课要写 Verilog，做这个项目等于一边写作业一边打磨产品——复合收益最大化。

---

## Week 1-2：从零学 MCP 到 3 个工具跑通

### 第一天：连 API 都变了

MCP Python SDK 的当前版本是 1.27.1。网上能找到的教程、博客、甚至官方文档的示例代码大多是这样写的：

```python
@server.tool()
async def my_tool():
    ...
```

我照着写，然后：

```
AttributeError: 'Server' object has no attribute 'tool'
```

SDK 1.27+ 废弃了 `@server.tool()` 快捷装饰器，改成了两段式 API：`@server.list_tools()` + `@server.call_tool()`。网上几乎没有文章提到这个变更。

这让一个编程水平 4/10 的人在一开始就撞了墙。但也教会我第一件事：**早期生态里，文档过期是常态。翻 SDK 源码比搜博客靠谱。**

### `.mcp.json` 放哪、settings.json 怎么写

Claude Code 通过项目根目录的 `.mcp.json` 发现 MCP Server。这个文件必须放在 workspace 根目录，不能放在子目录里。我最初建在 `verilog-mcp-server/` 下面，Claude Code 完全不识别。

settings.json 里的配置字段名字也不是直觉的 `mcpServers`——那会直接报 validation error。正确的 key 是 `enableAllProjectMcpServers` + `enabledMcpjsonServers`。

这些细节在文档里四散各处，踩坑后才凑齐。

### Windows GBK × Emoji

Lint 输出里我加了 `⚡⚠ℹ✓` emoji 做标记。Windows 中文版的默认编码是 GBK，Python print 的时候直接 `UnicodeEncodeError`。

换成 `[ISSUES]` `[WARNINGS]` `[INFO]` `[OK]` 纯 ASCII 解决。**教训：做 CLI 工具，Emoji 在 Windows 上是风险，不是美化。**

---

## 技术设计：800 行的取舍

### 选择 regex 而不是完整 SystemVerilog parser

写一个能处理所有 SystemVerilog 语法的 parser 是几个月的工作量——对我完全不现实。选择了正则表达式方案：

- 先用 `re.sub(r"//.*", "", code)` 去注释
- 再 `re.search(r"module\s+(\w+)\s*...", clean)` 提取模块签名
- 端口按方向关键字切分：`re.split(r"\s*(?=(?:input|output|inout)\b)", port_text)`

**缺点：** 嵌套括号、复杂的 parameterized port、interface port 会解析失败。
**优点：** 80% 的常见 Verilog 模块不需要这些高级特性。够用。

### check_lint 的 7 条规则

最初只有 4 条：缺 reset、case 缺 default、latch 风险、位宽不匹配。

Week 3 加了 3 条从实际教训中来的规则：

5. **时序块使用阻塞赋值** — `always @(posedge clk)` 里用 `=` 而不是 `<=`，仿真/综合行为可能不一致
6. **组合块使用非阻塞赋值** — `always @(*)` 里用 `<=`，多此一举且可能导致仿真偏差
7. **多驱动检测** — 同一个 reg 在多个 `always` 块中被赋值，综合器报错

这些规则不是从某本书上抄的，是我写数电作业时自己犯过的错。

### UVM 环境生成：从 DUT 到 10 个文件

UVM 验证的痛点不是写不出来，而是一个组件套一个组件的样板代码太多。`generate_uvm_env` 的输入是一个模块声明，输出是 10 个文件：

```
interface → transaction → sequence → driver → monitor → agent → scoreboard → env → test → top
```

两个设计决策：
- **`drv_cb` 只包含数据信号**，不包含 clock 和 reset——Driver 不应该驱动时钟
- **`mon_cb` 包含所有端口**——Monitor 需要采样完整波形
- **`do_print` 用 `$bits()`** 而不是原始宽度字符串——避免编译错误

Scoreboard 的比对逻辑留了 TODO——这个需要知道 DUT 的正确输出是什么，光靠端口列表推断不出来。

---

## 发布：GitHub + 分发

### 仓库优化

- 8 个 GitHub topics：`mcp-server` `verilog` `systemverilog` `chip-design` `eda-tools` `uvm` `claude-code` `mcp`
- Profile README + bio + location
- MIT License

### 分发策略

写完代码只是 50%。剩下 50% 是让人知道。

- **GitHub 平台自带分发**：topics、搜索排名
- **Reddit r/FPGA + r/chipdesign**：精准用户，一次性发帖，不持续运营
- **Hacker News Show HN**：开发者社区传播
- **V2EX 分享创造**：中文圈种子用户
- **MCP 社区目录**：mcp.so / Smithery / awesome-mcp-servers

全部是一次性发布，发完就走，不维护、不回评论超过 48 小时。

---

## 数据与反思

### 做了什么
- 3 周业余时间（~15 小时），从零 MCP 知识到 3 工具端到端跑通
- 810 行 Python，7 条 lint 规则，10 文件 UVM 环境生成

### 踩了什么坑
- MCP SDK API 1.27 和老版不兼容，网上文档基本过期
- `.mcp.json` 放错位置 Claude Code 不识别
- Windows GBK 编码下 Emoji 崩
- 端口解析从单方向切分进化到方向关键字感知切分

### 还没做完的
- Scoreboard 自动比对逻辑
- 正则 parser → 简单 tokenizer 升级
- 更多 lint 规则（signed/unsigned 混用、跨时钟域）
- 第四个工具（generate_assertions 或 analyze_waveform）

### 最重要的收获

**做就对了。** 编程 4/10 的大一学生也能在 3 周内做出一个能用的工具。AI（Claude Code）把门槛降到了让一个学微电子的学生可以同时做软件产品。

Chip design EDA 工具的现代化才刚刚开始。如果你也在做类似的事——欢迎交流。

---

*GitHub: [verilog-mcp-server](https://github.com/kaiwenyu147369/verilog-mcp-server)*
