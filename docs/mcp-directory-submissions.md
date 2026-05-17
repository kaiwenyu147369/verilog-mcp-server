# MCP 目录提交指南

按优先级排序。每个目录耗时 2-5 分钟。

---

## 1. mcp.so（最优先）⭐⭐⭐⭐⭐

**链接：** https://mcp.so/submit

**操作：**
- 填入 GitHub 仓库地址：`https://github.com/kaiwenyu147369/verilog-mcp-server`
- 网站会自动解析 README 和 package info
- 确认信息无误后提交

---

## 2. Smithery.ai ⭐⭐⭐⭐

**链接：** https://smithery.ai/submit

**操作：**
- 注册/登录 Smithery
- Submit new server → 填入 GitHub URL
- 支持连接 GitHub 仓库实现自动更新

---

## 3. awesome-mcp-servers（GitHub PR）⭐⭐⭐⭐

你的 fork 已建好：https://github.com/kaiwenyu147369/awesome-mcp-servers

**操作：**
1. 打开 https://github.com/kaiwenyu147369/awesome-mcp-servers/edit/master/README.md
2. 搜索 `## Science` 或 `## Hardware` 找到合适分类
3. 如果没有 EDA/Hardware 分类，找到 "Legend" 后面的服务器列表区域，按字母序插入以下条目：

```markdown
- [Verilog MCP Server](https://github.com/kaiwenyu147369/verilog-mcp-server) 🚀 🎓 — AI-powered Verilog/SystemVerilog assistant for Claude Code. Generates testbenches, lint RTL code (7 rules), and scaffolds UVM verification environments (10 components).
```

4. 提交时选 "Create a new branch for this commit and start a pull request"
5. PR 标题：`Add Verilog MCP Server — EDA / chip design tools`
6. PR 描述：

```
Adds the Verilog MCP Server, a 3-tool server for chip designers:
- generate_testbench
- check_lint (7 RTL lint rules)
- generate_uvm_env (10 UVM components)

Category: Hardware / EDA tools. MIT licensed. v0.4.0.
```

7. 点 "Propose changes"

---

## 4. PulseMCP ⭐⭐⭐

**链接：** https://pulsemcp.com/submit

**操作：**
- 填表：名称、描述、GitHub URL、分类（选 "Hardware" 或 "Development Tools"）
