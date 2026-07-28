# AI Coding 链路设计文档

## 1. 项目概述

**项目名称**: AI Coding 链路
**项目类型**: Claude Code Skill / 命令行工具
**核心功能**: 根据效能平台需求单编号，自动读取需求、拆分任务、**使用 Claude Code 当前会话模型**生成代码、推送本地仓库
**目标用户**: 恒生内部开发团队
**使用方式**:
- **Skill 方式**（推荐）：在 Claude Code 中直接说 "处理需求 XXX"，使用当前会话模型，无需额外配置 API Key
- **CLI 方式**：运行 `python ai-coding.py <需求编号>`

## 2. 背景与目标

### 背景
恒生效能平台每天处理大量需求单，开发人员需要手动理解需求、定位代码、编写修改。流程重复且效率低下。

### 目标
- 自动化读取效能平台需求单
- AI 自动分析需求并拆分具体任务
- 并行调用 AI 生成代码
- 自动代码审查
- 推送本地仓库供人工复核

## 3. 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AI Coding 平台 (团队通用版)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     配置管理模块                              │   │
│  │  - 代码仓库路径映射 (需求单ID前缀 -> 仓库路径)                 │   │
│  │  - 效能平台 MCP 配置                                         │   │
│  │  - 团队成员权限配置                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              v                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │  需求读取    │ -> │  任务拆分    │ -> │  代码生成    │         │
│  │  模块        │    │  模块        │    │  模块        │         │
│  │(MCP接口)     │    │(AI分析)      │    │(子Agent)     │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│         │                   │                   │                  │
│         v                   v                   v                  │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                    任务队列 / 执行日志                     │       │
│  └─────────────────────────────────────────────────────────┘       │
│                              │                                      │
│                              v                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │  代码审查    │ -> │  差异生成    │ -> │  Git推送     │         │
│  │  模块        │    │  模块        │    │  模块        │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 模块说明

| 模块 | 功能 | 技术实现 |
|------|------|---------|
| **配置管理** | 仓库映射、MCP配置、任务配置 | YAML 配置文件 |
| **需求读取** | 通过 MCP 接口读取效能平台需求单 | 调用 get_story_info + get_task_list |
| **任务拆分** | 分析需求，拆分具体修改任务 | AI 分析 + 代码语义理解 |
| **代码生成** | 每个任务调用当前会话模型出码 | 使用 Claude Code 当前模型，无需额外 API Key |
| **代码审查** | Review 生成的代码质量 | AI 自动审查 |
| **差异生成** | 生成 Git diff | subprocess 调用 git |
| **Git推送** | 推送到本地仓库 | subprocess 调用 git |

## 4. 配置文件设计

### config.yaml

```yaml
# AI Coding 团队通用配置

# 效能平台 MCP 配置
mcp:
  access_key: "${ACCESS_KEY}"  # 环境变量
  base_url: "https://dev.hundsun.com/openapi/apis/v1/mcp"

# 代码仓库映射 (产品编号前缀 -> 仓库路径)
repositories:
  # O32 产品线
  "CP-S000128":
    path: "C:/Users/hspcadmin/Desktop/src"
    name: "O32投资管理系统"
    branch: "ai-coding-dev"

  # O-Trade 产品线
  "CP-S000256":
    path: "D:/repos/otrade"
    name: "O-Trade"
    branch: "develop"

# 任务配置
task:
  # 最大并行任务数
  max_parallel: 3
  # 代码审查规则文件
  review_rules: "./rules/code_review.yaml"

# Git 配置
git:
  # 是否自动 push 到远程
  auto_push: false
  # commit 消息模板
  commit_template: "AI Coding: {需求编号} - {任务描述}"
```

## 5. 工作流程（Skill 方式）

```
1. 用户说: "处理需求 202510284148，代码目录是 C:/src"
         │
         v
2. MCP 获取需求单详情
   - story_num, description, edit_description
         │
         v
3. AI 分析需求，生成任务清单
   - task_id, task_name, edit_description
   - 格式参考效能平台任务单
         │
         v
4. 用户给定代码仓库范围（如 C:/src）
   - AI 扫描目录，读取相关代码
         │
         v
5. AI 语义匹配
   - 理解需求要做什么
   - 理解代码逻辑
   - 匹配需要修改的位置（文件 + 函数）
         │
         v
6. 使用 Claude Code 当前会话模型生成代码
         │
         v
7. 代码审查
         │
         v
8. Git push 到本地仓库
         │
         v
9. 返回执行结果给用户
```

## 5.1 两种使用方式

### 方式 1：Skill 方式（推荐）

在 Claude Code 中直接对话：

```
用户: 处理需求 202510284148

AI: （自动执行上述流程）
```

**优势**：
- 使用 Claude Code 当前会话模型
- **无需配置 ANTHROPIC_API_KEY**
- 无缝集成到开发流程

### 方式 2：CLI 方式

```bash
cd ai-coding
python ai-coding.py 202510284148
```

**优势**：
- 适合自动化流水线
- 支持多厂商 LLM 配置

## 6. CLI 设计

### 命令行接口

```bash
# 处理需求单
ai-coding <需求编号> [options]

# 选项
--dry-run          # 预览模式，不实际执行
--parallel <num>   # 指定并行任务数 (默认3)
--no-review        # 跳过代码审查
--no-push          # 只生成 diff，不推送

# 管理命令
ai-coding --list              # 查看历史任务
ai-coding --config            # 查看当前配置
ai-coding --init              # 初始化配置文件
```

## 7. 数据结构

### Task (任务)

```python
class Task:
    task_id: str              # 任务ID
    story_num: str            # 需求编号
    file_path: str            # 文件路径
    function_name: str        # 函数名
    description: str          # 任务描述
    edit_description: str     # 修改说明 (来自需求单)
    status: str               # pending/running/completed/failed
    generated_code: str       # 生成的代码
    review_result: str        # 审查结果
```

### ExecutionLog (执行日志)

```python
class ExecutionLog:
    execution_id: str         # 执行ID
    story_num: str            # 需求编号
    start_time: datetime      # 开始时间
    end_time: datetime        # 结束时间
    tasks: List[Task]         # 任务列表
    status: str               # success/partial/failed
    git_commit_sha: str       # 提交的 commit SHA
```

## 8. 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| MCP 接口失败 | 重试3次，失败则终止 |
| 代码仓库不存在 | 提示配置错误 |
| 代码文件不存在 | 记录警告，跳过该文件 |
| AI 生成失败 | 记录错误，继续处理其他任务 |
| Git 推送失败 | 保留本地修改，提示手动处理 |

## 9. 安全考虑

- Access Key 通过环境变量读取，不写入配置文件
- 代码仓库路径需要配置白名单
- 执行日志需要定期清理

## 10. 实施计划

1. **配置管理模块** - 实现 YAML 配置读取、仓库映射
2. **需求读取模块** - MCP 接口封装
3. **任务拆分模块** - AI Prompt 设计
4. **代码生成模块** - 子 Agent 调用
5. **代码审查模块** - 规则引擎
6. **Git 推送模块** - git 命令封装
7. **CLI 入口** - 命令行参数解析

## 11. 验收标准

- [ ] 能通过需求编号读取效能平台需求单
- [ ] 能根据产品编号自动匹配代码仓库
- [ ] 能将需求拆分为具体任务
- [ ] 能并行生成代码
- [ ] 能自动审查代码
- [ ] 能推送到本地 Git 仓库
- [ ] CLI 命令可以正常使用
- [ ] 配置文件可以被团队成员自定义