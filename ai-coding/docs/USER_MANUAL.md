# AI Coding CLI 使用手册

## 概述

AI Coding 是一个命令行工具，根据效能平台需求单编号，自动：
1. 读取需求单详情（MCP 接口）
2. 分析代码位置
3. 调用 AI 生成代码修改
4. 推送到本地 Git 仓库

---

## 环境准备

### 1. 安装 Python

要求 Python 3.8+

```bash
# 检查版本
python --version

# 如果没有，安装 Python: https://www.python.org/downloads/
```

### 2. 克隆项目

```bash
git clone <项目仓库地址>
cd ai-coding
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

依赖列表：
- `pyyaml` - 配置文件解析
- `requests` - HTTP 请求
- `gitpython` - Git 操作

**按需安装的 SDK：**
- `anthropic` - Anthropic Claude（默认）
- `openai` - OpenAI GPT
- `dashscope` - 阿里通义千问

其他厂商使用 HTTP API，无需额外安装。

---

## 配置

### 1. 配置效能平台 Access Key

```bash
# Windows CMD
set ACCESS_KEY=你的效能平台AccessKey

# Windows PowerShell
$env:ACCESS_KEY="你的效能平台AccessKey"

# Linux/Mac
export ACCESS_KEY=你的效能平台AccessKey
```

**如何获取 Access Key？**
- 登录效能平台
- 进入「开放接口」或「个人设置」
- 创建/复制 Access Key

### 2. 配置 LLM 厂商 API Key

AI Coding 支持多厂商大模型，按需配置。

#### 2.1 选择厂商

| 厂商 | 环境变量 | 模型示例 |
|------|----------|----------|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | claude-sonnet-4-6 |
| OpenAI (GPT) | `OPENAI_API_KEY` | gpt-4o |
| 阿里通义千问 | `DASHSCOPE_API_KEY` | qwen-turbo |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat |
| Kimi (月之暗面) | `MOONSHOT_API_KEY` | moonshot-v1-8k |
| MiniMax | `MINMAX_API_KEY` | abab6.5s-chat |
| 智谱GLM | `ZHIPU_API_KEY` | glm-4 |

#### 2.2 配置步骤

**步骤 1：设置环境变量**

```bash
# 选择一个厂商配置（以 Anthropic 为例）
# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-api03-xxx

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-api03-xxx"

# Linux/Mac
export ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

**步骤 2：在 config.yaml 中启用厂商**

编辑 `config.yaml`：

```yaml
# 启用 Anthropic
providers:
  anthropic:
    enabled: true           # 改为 true
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-sonnet-4-6"

# 设置当前使用的厂商
active_provider: "anthropic"
```

#### 2.3 各厂商 API Key 获取方式

| 厂商 | 获取地址 |
|------|----------|
| Anthropic | https://console.anthropic.com/ |
| OpenAI | https://platform.openai.com/ |
| 阿里通义 | https://dashscope.console.aliyun.com/ |
| DeepSeek | https://platform.deepseek.com/ |
| Kimi | https://platform.moonshot.cn/ |
| MiniMax | https://platform.minimax.io/ |
| 智谱GLM | https://open.bigmodel.cn/ |

#### 2.4 切换厂商

修改 `config.yaml` 中的 `active_provider`：

```yaml
# 切换到 OpenAI
active_provider: "openai"

# 切换到阿里通义
active_provider: "ali"
```

**费用说明（仅供参考）：**
- Anthropic Claude: 约 $3/百万输入tokens
- OpenAI GPT-4o: 约 $5/百万输入tokens
- 阿里通义: 约 ¥1/百万输入tokens

### 3. 配置代码仓库映射（可选）

默认配置在 `config.yaml`：

```yaml
# 效能平台 MCP 配置
mcp:
  access_key: "${ACCESS_KEY}"
  base_url: "https://dev.hundsun.com/openapi/apis/v1/mcp"

# Anthropic API 配置
anthropic:
  api_key: "${ANTHROPIC_API_KEY}"
  model: "claude-sonnet-4-6"

# 代码仓库映射 (产品编号前缀 -> 仓库路径)
repositories:
  "CP-S000128":
    path: "C:/Users/hspcadmin/Desktop/src"
    name: "O32投资管理系统"
    branch: "ai-coding-dev"
```

**配置说明：**

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `product_no` 前缀 | 效能平台产品编号前缀 | `CP-S000128` |
| `path` | 代码仓库本地路径 | `C:/src` |
| `branch` | Git 分支名 | `ai-coding-dev` |

**添加新仓库：**

```yaml
repositories:
  "CP-S000128":
    path: "你的O32代码路径"
    branch: "ai-coding-dev"
  "CP-S000256":
    path: "你的O-Trade代码路径"
    branch: "develop"
  # 添加更多...
```

---

## 使用方法

### 基本用法

```bash
python ai-coding.py <需求编号>
```

示例：
```bash
python ai-coding.py 202510284148
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `story_num` | 效能平台需求编号（必填） | - |
| `--dry-run` | 预览模式，不实际执行 | false |
| `--parallel <num>` | 并行任务数 | 3 |
| `--no-review` | 跳过代码审查 | false |
| `--no-push` | 只生成代码，不推送 | false |
| `--config <path>` | 指定配置文件路径 | ~/.ai-coding/config.yaml |

### 使用示例

**1. 完整执行（推荐）**

```bash
python ai-coding.py 202510284148
```

输出：
```
=== AI Coding 开始处理需求 202510284148 ===
[1/6] 创建 MCP 客户端...
[2/6] 读取需求单...
  - 需求: convert_date_format变化时IV计算不正确
  - 类型: 缺陷
  - 产品: CP-S000128
  - 代码仓库: C:/Users/hspcadmin/Desktop/src
[3/6] 读取关联任务...
  - 任务数: 3
[4/6] 拆分任务...
  - 拆分为 5 个子任务
[5/6] 生成代码...
  - 处理任务: TASK_001
  - 处理任务: TASK_002
  - 处理任务: TASK_003
[6/6] 代码审查...
  - TASK_001: approved
  - TASK_002: approved
  - TASK_003: approved
[7/7] Git 推送...
  - 提交: abc1234

=== 处理完成 ===
```

**2. 预览模式（查看任务列表）**

```bash
python ai-coding.py 202510284148 --dry-run
```

只显示任务列表，不实际生成代码。

**3. 跳过代码审查**

```bash
python ai-coding.py 202510284148 --no-review
```

**4. 只生成代码，不推送**

```bash
python ai-coding.py 202510284148 --no-push
```

代码生成后保存在本地，不提交到 Git。

---

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
4. AI 生成代码（调用 Claude API）
    ↓
5. 代码审查（可选）
    ↓
6. Git 推送（add → commit → push）
```

---

## 常见问题

### Q1: 提示 "ANTHROPIC_API_KEY not set"

**原因：** 没有配置 Anthropic API Key

**解决：**
```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-api03-xxx

# Linux/Mac
export ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

---

### Q2: 提示 "ACCESS_KEY not set"

**原因：** 没有配置效能平台 Access Key

**解决：**
```bash
set ACCESS_KEY=你的AccessKey
```

---

### Q3: 提示 "未找到产品 XXX 对应的仓库配置"

**原因：** 需求的产品编号没有配置对应的仓库路径

**解决：**
在 `config.yaml` 中添加仓库配置：

```yaml
repositories:
  "CP-S000128":  # 产品编号前缀
    path: "你的代码仓库路径"
    branch: "你的分支名"
```

---

### Q4: 提示 "文件不存在"

**原因：** 需求中标记的修改文件在本地代码仓库中不存在

**解决：**
1. 确认仓库路径配置正确
2. 同步最新代码到本地
3. 如果文件确实不存在，该任务会跳过

---

### Q5: Git 推送失败

**原因：** 网络问题或权限问题

**解决：**
1. 检查网络连接
2. 使用 `--no-push` 参数跳过推送
3. 手动执行 `git push`

---

### Q6: AI 生成代码不正确

**原因：** AI 理解需求可能有偏差

**解决：**
1. 使用 `--dry-run` 预览生成的内容
2. 检查需求描述是否清晰
3. 人工审核生成的代码
4. 如有问题，手动修改后提交

---

## 配置文件位置

配置文件按以下顺序查找：

1. 命令行 `--config` 指定的路徑
2. `~/.ai-coding/config.yaml`（用户家目录）
3. 项目目录下的 `config.yaml`

**推荐：**
- 个人配置放在 `~/.ai-coding/config.yaml`
- 项目默认配置用项目目录的 `config.yaml`

---

## 环境变量持久化

### Windows

**方法 1：临时（当前终端有效）**
```bash
set ACCESS_KEY=xxx
set ANTHROPIC_API_KEY=xxx
```

**方法 2：永久（系统设置）**
1. 打开「系统属性」→「高级」→「环境变量」
2. 新建用户变量
3. 重启终端生效

### Linux/Mac

**方法 1：临时**
```bash
export ACCESS_KEY=xxx
export ANTHROPIC_API_KEY=xxx
```

**方法 2：永久（~/.bashrc 或 ~/.zshrc）**
```bash
echo 'export ACCESS_KEY=xxx' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY=xxx' >> ~/.bashrc
source ~/.bashrc
```

---

## 日志说明

运行时会输出详细日志：

- `[1/6] 创建 MCP 客户端` - MCP 连接状态
- `[2/6] 读取需求单` - 需求基本信息
- `[3/6] 读取关联任务` - 任务数量
- `[4/6] 拆分任务` - 拆分结果
- `[5/6] 生成代码` - AI 生成进度
- `[6/6] 代码审查` - 审查结果
- `[7/7] Git 推送` - 提交状态

---

## 后续优化

如有以下需求，可联系开发者：

- [ ] 封装成 MCP 服务（团队共用 API Key）
- [ ] 支持其他大模型（OpenAI、阿里通义等）
- [ ] 添加代码测试
- [ ] 支持更多 Git 平台（GitLab、Gitee）
- [ ] Web 界面

---

## 反馈与支持

如有问题或建议，请提交 Issue 或联系开发者。

---

**祝使用愉快！**