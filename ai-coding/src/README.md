# AI Coding CLI

> 效能平台需求自动代码生成工具

根据效能平台需求单编号，自动读取需求、拆分任务、AI 生成代码、推送到本地 Git 仓库。

## 功能特性

- 📖 自动读取效能平台需求单（MCP 接口）
- 🤖 支持多厂商 LLM
- 🔄 任务自动拆分
- ✅ 代码自动审查
- 📦 Git 自动推送

## 支持的 LLM 厂商

| 厂商 | 环境变量 | 模型示例 |
|------|----------|----------|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | claude-sonnet-4-6 |
| OpenAI (GPT) | `OPENAI_API_KEY` | gpt-4o |
| 阿里通义千问 | `DASHSCOPE_API_KEY` | qwen-turbo |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat |
| Kimi (月之暗面) | `MOONSHOT_API_KEY` | moonshot-v1-8k |
| MiniMax | `MINMAX_API_KEY` | abab6.5s-chat |
| 智谱GLM | `ZHIPU_API_KEY` | glm-4 |

## 环境要求

- Python 3.8+
- Git

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/hujiahui0604/test.git
cd test/ai-coding
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 效能平台 Access Key
set ACCESS_KEY=你的效能平台AccessKey

# 选择一个 LLM 厂商的 API Key
set ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### 4. 配置代码仓库

编辑 `config.yaml`，添加你的代码仓库路径：

```yaml
repositories:
  "CP-S000128":  # 产品编号前缀
    path: "你的代码仓库路径"
    branch: "ai-coding-dev"
```

### 5. 运行

```bash
python ai-coding.py <需求编号>
```

示例：
```bash
python ai-coding.py 202510284148
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `story_num` | 效能平台需求编号（必填） | - |
| `--dry-run` | 预览模式，不实际执行 | false |
| `--parallel <num>` | 并行任务数 | 3 |
| `--no-review` | 跳过代码审查 | false |
| `--no-push` | 只生成代码，不推送 | false |
| `--config <path>` | 指定配置文件路径 | ~/.ai-coding/config.yaml |
| `--provider` | 指定 LLM 厂商 | config.yaml 中配置 |

### 使用示例

```bash
# 基本用法
python ai-coding.py 202510284148

# 预览模式（只显示任务，不生成代码）
python ai-coding.py 202510284148 --dry-run

# 指定厂商
python ai-coding.py 202510284148 --provider deepseek

# 跳过代码审查
python ai-coding.py 202510284148 --no-review

# 跳过 Git 推送
python ai-coding.py 202510284148 --no-push
```

## 工作流程

```
用户执行命令
    ↓
1. 读取需求单（MCP get_story_info）
    ↓
2. 读取关联任务（MCP get_task_list）
    ↓
3. AI 拆分任务（分析修改内容）
    ↓
4. AI 生成代码（调用 LLM API）
    ↓
5. 代码审查（可选）
    ↓
6. Git 推送（add → commit → push）
```

## 项目结构

```
ai-coding/
├── ai-coding.py          # 主入口
├── config.yaml           # 配置文件
├── requirements.txt      # 依赖
├── docs/
│   └── USER_MANUAL.md   # 详细使用手册
└── src/
    ├── config.py         # 配置管理
    ├── mcp_client.py     # MCP 客户端
    ├── story_reader.py   # 需求读取
    ├── task_splitter.py  # 任务拆分
    ├── code_generator.py # 代码生成
    ├── code_reviewer.py  # 代码审查
    ├── git_manager.py    # Git 管理
    └── cli.py            # CLI 入口
```

## 常见问题

### Q1: 提示 "API Key not set"

确保已配置环境变量：
```bash
set ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### Q2: 提示 "未找到产品对应的仓库配置"

在 `config.yaml` 中添加仓库配置：
```yaml
repositories:
  "CP-S000128":
    path: "你的代码仓库路径"
    branch: "你的分支"
```

### Q3: 提示 "文件不存在"

确认仓库路径配置正确，文件在本地代码仓库中存在。

## 文档

- [详细使用手册](docs/USER_MANUAL.md)

## License

MIT

---

**使用中有问题？请提交 Issue。**