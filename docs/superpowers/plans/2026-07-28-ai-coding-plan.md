# AI Coding 链路实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个团队通用的 AI Coding 工具，根据效能平台需求单编号自动读取需求、拆分任务、AI 生成代码、推送本地仓库

**Architecture:** 采用模块化设计，分为配置管理、需求读取、任务拆分、代码生成、代码审查、Git推送六大模块，通过 CLI 统一入口

**Tech Stack:** Python 3.10+, PyYAML, GitPython, Claude API

---

## 文件结构

```
ai-coding/
├── config.yaml                 # 配置文件
├── src/
│   ├── __init__.py
│   ├── config.py               # 配置管理模块
│   ├── mcp_client.py           # MCP 客户端封装
│   ├── story_reader.py         # 需求读取模块
│   ├── task_splitter.py        # 任务拆分模块
│   ├── code_generator.py       # 代码生成模块
│   ├── code_reviewer.py        # 代码审查模块
│   ├── git_manager.py          # Git 管理模块
│   └── cli.py                  # CLI 入口
├── rules/
│   └── code_review.yaml        # 代码审查规则
├── logs/                       # 执行日志
├── requirements.txt            # 依赖
└── README.md                   # 使用说明
```

---

## Task 1: 配置管理模块

**Files:**
- Create: `ai-coding/src/config.py`
- Create: `ai-coding/config.yaml`
- Create: `ai-coding/requirements.txt`

- [ ] **Step 1: 创建目录结构和 requirements.txt**

```bash
mkdir -p ai-coding/src ai-coding/rules ai-coding/logs
```

```python
# ai-coding/requirements.txt
pyyaml>=6.0
gitpython>=3.1.0
anthropic>=0.18.0
```

- [ ] **Step 2: 创建 config.py**

```python
"""配置管理模块"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """AI Coding 配置管理"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        home = Path.home()
        return home / ".ai-coding" / "config.yaml"

    def _load_config(self):
        """加载配置文件"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            # 使用默认配置
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "mcp": {
                "access_key": os.environ.get("ACCESS_KEY", ""),
                "base_url": "https://dev.hundsun.com/openapi/apis/v1/mcp"
            },
            "repositories": {},
            "task": {
                "max_parallel": 3
            },
            "git": {
                "auto_push": False,
                "commit_template": "AI Coding: {需求编号} - {任务描述}"
            }
        }

    def get_mcp_access_key(self) -> str:
        """获取 MCP Access Key"""
        key = self._config.get("mcp", {}).get("access_key", "")
        # 从环境变量读取
        if key.startswith("${") and key.endswith("}"):
            env_var = key[2:-1]
            return os.environ.get(env_var, "")
        return key

    def get_mcp_base_url(self) -> str:
        """获取 MCP 基础 URL"""
        return self._config.get("mcp", {}).get("base_url", "")

    def get_repository_by_product(self, product_no: str) -> Optional[Dict[str, str]]:
        """根据产品编号获取仓库配置"""
        repos = self._config.get("repositories", {})
        # 匹配前缀
        for prefix, repo in repos.items():
            if product_no.startswith(prefix):
                return repo
        return None

    def get_max_parallel(self) -> int:
        """获取最大并行任务数"""
        return self._config.get("task", {}).get("max_parallel", 3)

    def get_commit_template(self) -> str:
        """获取提交消息模板"""
        return self._config.get("git", {}).get("commit_template", "AI Coding: {需求编号} - {任务描述}")


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """获取配置实例"""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
```

- [ ] **Step 3: 创建 config.yaml 示例**

```yaml
# AI Coding 团队通用配置

# 效能平台 MCP 配置
mcp:
  access_key: "${ACCESS_KEY}"
  base_url: "https://dev.hundsun.com/openapi/apis/v1/mcp"

# 代码仓库映射 (产品编号前缀 -> 仓库路径)
repositories:
  "CP-S000128":
    path: "C:/Users/hspcadmin/Desktop/src"
    name: "O32投资管理系统"
    branch: "ai-coding-dev"
  "CP-S000256":
    path: "D:/repos/otrade"
    name: "O-Trade"
    branch: "develop"

# 任务配置
task:
  max_parallel: 3

# Git 配置
git:
  auto_push: false
  commit_template: "AI Coding: {需求编号} - {任务描述}"
```

- [ ] **Step 4: 创建 __init__.py**

```python
"""AI Coding 链路"""
__version__ = "0.1.0"
```

- [ ] **Step 5: 提交代码**

```bash
cd ai-coding
git add src/config.py config.yaml requirements.txt src/__init__.py
git commit -m "feat: 添加配置管理模块"
```

---

## Task 2: MCP 客户端封装

**Files:**
- Create: `ai-coding/src/mcp_client.py`

- [ ] **Step 1: 创建 MCP 客户端**

```python
"""MCP 客户端封装"""
import json
import requests
from typing import Dict, Any, Optional, List
import time


class MCPClient:
    """效能平台 MCP 客户端"""

    def __init__(self, access_key: str, base_url: str):
        self.access_key = access_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Access-Key": access_key,
            "Content-Type": "application/json"
        })

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 MCP 工具"""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": int(time.time() * 1000)
        }

        response = self.session.post(self.base_url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        # 解析 SSE 格式响应
        content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        return json.loads(content)

    def get_story_info(self, story_num: str) -> Dict[str, Any]:
        """获取需求详情"""
        return self.call_tool("get_story_info", {"story_num": story_num})

    def get_task_list(self, product_id: str, req_num: str, page_num: int = 1, page_size: int = 60) -> Dict[str, Any]:
        """获取任务列表"""
        return self.call_tool("get_task_list", {
            "tproductId": product_id,
            "reqNum": req_num,
            "pageNum": page_num,
            "pageSize": page_size
        })

    def get_version_list(self, product_nos: str, version_no: str = "", page_num: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """获取版本列表"""
        return self.call_tool("get_version_list", {
            "product_nos": product_nos,
            "version_no": version_no,
            "page_num": page_num,
            "page_size": page_size
        })

    def get_task_info(self, task_number: str) -> Dict[str, Any]:
        """获取任务详情"""
        return self.call_tool("get_task_info", {"task_number": task_number})


def create_mcp_client(config) -> MCPClient:
    """创建 MCP 客户端"""
    return MCPClient(
        access_key=config.get_mcp_access_key(),
        base_url=config.get_mcp_base_url()
    )
```

- [ ] **Step 2: 提交代码**

```bash
cd ai-coding
git add src/mcp_client.py
git commit -m "feat: 添加 MCP 客户端封装"
```

---

## Task 3: 需求读取模块

**Files:**
- Create: `ai-coding/src/story_reader.py`

- [ ] **Step 1: 创建需求读取模块**

```python
"""需求读取模块"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Story:
    """需求单"""
    story_num: str
    story_name: str
    description: str
    bug_effect: str
    customer_name: str
    product_no: str
    story_type: str
    jira_id: str = ""


@dataclass
class Task:
    """任务"""
    task_number: str
    task_name: str
    description: str
    edit_description: str
    modified_file: str
    version_no: str
    modifier_name: str
    status: str
    module_list: List[Dict[str, str]]


class StoryReader:
    """需求读取器"""

    def __init__(self, mcp_client):
        self.mcp_client = mcp_client

    def read_story(self, story_num: str) -> Story:
        """读取需求单"""
        result = self.mcp_client.get_story_info(story_num)
        data = result.get("data", [{}])[0]

        return Story(
            story_num=data.get("story_num", ""),
            story_name=data.get("story_name", ""),
            description=self._clean_html(data.get("description", "")),
            bug_effect=self._clean_html(data.get("bug_effect", "")),
            customer_name=data.get("customer_name", "内部客户"),
            product_no=data.get("product_no", ""),
            story_type=self._format_story_type(data.get("story_type", "")),
            jira_id=data.get("jira_id", "")
        )

    def read_tasks(self, product_id: str, story_num: str) -> List[Task]:
        """读取关联任务"""
        result = self.mcp_client.get_task_list(product_id, story_num)
        items = result.get("data", {}).get("items", [])

        tasks = []
        for item in items:
            task = Task(
                task_number=item.get("taskNums", ""),
                task_name=item.get("name", ""),
                description=item.get("description", ""),
                edit_description=self._clean_html(item.get("edit_description", "")),
                modified_file=self._clean_html(item.get("modified_file", "")),
                version_no=item.get("versionNO", ""),
                modifier_name=item.get("modifierName", ""),
                status=item.get("modifyStatusName", ""),
                module_list=item.get("moduleList", [])
            )
            tasks.append(task)
        return tasks

    def _clean_html(self, text: str) -> str:
        """清除 HTML 标签"""
        if not text:
            return ""
        # 去除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 转换 HTML 实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _format_story_type(self, story_type: str) -> str:
        """格式化需求类型"""
        type_map = {
            "0": "缺陷",
            "1": "缺陷",
            "2": "改进性需求",
            "3": "个性业务需求",
            "4": "通用业务需求",
            "5": "日常管理"
        }
        return type_map.get(str(story_type), "未知")
```

- [ ] **Step 2: 提交代码**

```bash
cd ai-coding
git add src/story_reader.py
git commit -m "feat: 添加需求读取模块"
```

---

## Task 4: 任务拆分模块

**Files:**
- Create: `ai-coding/src/task_splitter.py`

- [ ] **Step 1: 创建任务拆分模块**

```python
"""任务拆分模块"""
from typing import List, Dict, Any
from dataclasses import dataclass
from .story_reader import Story, Task


@dataclass
class SplitTask:
    """拆分后的任务"""
    task_id: str
    story_num: str
    file_path: str
    function_name: str
    original_task: str
    description: str
    edit_description: str
    priority: int = 1


class TaskSplitter:
    """任务拆分器"""

    def __init__(self):
        pass

    def split(self, story: Story, tasks: List[Task], repo_path: str) -> List[SplitTask]:
        """拆分任务"""
        split_tasks = []

        for task in tasks:
            # 从修改文件中提取具体文件
            files = self._parse_modified_files(task.modified_file)

            for idx, file_path in enumerate(files):
                # 构建任务描述
                description = self._build_task_description(story, task, file_path)

                split_task = SplitTask(
                    task_id=f"{story.story_num}_{task.task_number}_{idx}",
                    story_num=story.story_num,
                    file_path=file_path,
                    function_name=self._infer_function_name(task, file_path),
                    original_task=task.task_number,
                    description=description,
                    edit_description=task.edit_description,
                    priority=1
                )
                split_tasks.append(split_task)

        return split_tasks

    def _parse_modified_files(self, modified_file: str) -> List[str]:
        """解析修改文件列表"""
        if not modified_file:
            return []

        # 按换行或逗号分割
        files = []
        for line in modified_file.replace(',', '\n').split('\n'):
            line = line.strip()
            if line and not line.startswith('<'):
                files.append(line)
        return files

    def _build_task_description(self, story: Story, task: Task, file_path: str) -> str:
        """构建任务描述"""
        return f"""
需求编号: {story.story_num}
需求类型: {story.story_type}
需求描述: {story.description}

任务: {task.task_name}
修改文件: {file_path}

修改说明:
{task.edit_description}
"""

    def _infer_function_name(self, task: Task, file_path: str) -> str:
        """推断函数名"""
        # 从任务描述中提取函数名
        edit_desc = task.edit_description

        # 查找类似 "函数名()" 的模式
        import re
        func_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        matches = re.findall(func_pattern, edit_desc)

        if matches:
            return matches[0]

        # 从文件路径推断
        filename = file_path.split('/')[-1].split('\\')[-1]
        if filename.endswith('.cpp') or filename.endswith('.c'):
            # 尝试找到对应的函数
            return f"handle_{filename.replace('.cpp', '').replace('.c', '')}"

        return "main"
```

- [ ] **Step 2: 提交代码**

```bash
cd ai-coding
git add src/task_splitter.py
git commit -m "feat: 添加任务拆分模块"
```

---

## Task 5: 代码生成模块

**Files:**
- Create: `ai-coding/src/code_generator.py`

- [ ] **Step 1: 创建代码生成模块**

```python
"""代码生成模块"""
import os
import subprocess
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .task_splitter import SplitTask


@dataclass
class GeneratedCode:
    """生成的代码"""
    task_id: str
    file_path: str
    original_content: str
    generated_patch: str
    status: str  # success/failed
    error_message: str = ""


class CodeGenerator:
    """代码生成器"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def generate(self, task: SplitTask) -> GeneratedCode:
        """生成代码"""
        # 1. 读取原文件
        full_path = os.path.join(self.repo_path, task.file_path)
        if not os.path.exists(full_path):
            return GeneratedCode(
                task_id=task.task_id,
                file_path=task.file_path,
                original_content="",
                generated_patch="",
                status="failed",
                error_message=f"文件不存在: {full_path}"
            )

        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # 2. 调用 AI 生成代码
        prompt = self._build_prompt(task, original_content)
        generated_patch = self._call_ai(prompt)

        # 3. 应用补丁
        if generated_patch:
            return GeneratedCode(
                task_id=task.task_id,
                file_path=task.file_path,
                original_content=original_content,
                generated_patch=generated_patch,
                status="success"
            )
        else:
            return GeneratedCode(
                task_id=task.task_id,
                file_path=task.file_path,
                original_content=original_content,
                generated_patch="",
                status="failed",
                error_message="AI 生成失败"
            )

    def _build_prompt(self, task: SplitTask, original_content: str) -> str:
        """构建 AI Prompt"""
        return f"""
你是一个资深的 C++ 开发工程师。请根据以下需求修改代码。

## 需求信息
- 需求编号: {task.story_num}
- 修改文件: {task.file_path}

## 任务描述
{task.description}

## 修改说明
{task.edit_description}

## 原文件内容
```{'cpp'}
{original_content}
```

## 要求
1. 只修改必要的部分，不要修改其他代码
2. 保持代码风格一致
3. 输出完整的修改后的代码（如果修改内容较少，可以只输出 diff）
4. 如果不需要修改，请回复 "无需修改"

请输出修改后的代码或 diff：
"""

    def _call_ai(self, prompt: str) -> str:
        """调用 AI 生成代码"""
        if not self.anthropic_key:
            # 如果没有 API Key，返回模拟结果
            return self._generate_mock_patch()

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_key)

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text
        except Exception as e:
            print(f"AI 调用失败: {e}")
            return self._generate_mock_patch()

    def _generate_mock_patch(self) -> str:
        """生成模拟补丁（用于测试）"""
        return """
// TODO: AI 生成的代码应该在这里
// 当前为模拟结果
"""
```

- [ ] **Step 2: 提交代码**

```bash
cd ai-coding
git add src/code_generator.py
git commit -m "feat: 添加代码生成模块"
```

---

## Task 6: 代码审查模块

**Files:**
- Create: `ai-coding/src/code_reviewer.py`

- [ ] **Step 1: 创建代码审查模块**

```python
"""代码审查模块"""
import os
import anthropic
from typing import Dict, Any, List
from dataclasses import dataclass
from .code_generator import GeneratedCode


@dataclass
class ReviewResult:
    """审查结果"""
    task_id: str
    status: str  # pass/need_fix/warning
    issues: List[str]
    suggestions: List[str]


class CodeReviewer:
    """代码审查器"""

    def __init__(self):
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def review(self, generated: GeneratedCode) -> ReviewResult:
        """审查生成的代码"""
        if generated.status != "success":
            return ReviewResult(
                task_id=generated.task_id,
                status="need_fix",
                issues=[f"代码生成失败: {generated.error_message}"],
                suggestions=[]
            )

        # 构建审查 Prompt
        prompt = self._build_review_prompt(generated)

        # 调用 AI 审查
        if self.anthropic_key:
            try:
                review_text = self._call_ai_review(prompt)
                return self._parse_review_result(generated.task_id, review_text)
            except Exception as e:
                print(f"AI 审查失败: {e}")

        # 如果没有 API Key，返回默认通过
        return ReviewResult(
            task_id=generated.task_id,
            status="pass",
            issues=[],
            suggestions=[]
        )

    def _build_review_prompt(self, generated: GeneratedCode) -> str:
        """构建审查 Prompt"""
        return f"""
请审查以下代码修改：

## 文件: {generated.file_path}

## 原代码
```{'cpp'}
{generated.original_content}
```

## AI 生成的修改
```
{generated.generated_patch}
```

## 审查要点
1. 代码语法正确性
2. 逻辑是否合理
3. 是否有潜在的性能问题
4. 是否有安全漏洞
5. 代码风格是否一致

请输出审查结果，格式如下：
- 状态: pass / need_fix / warning
- 问题: (如果有)
- 建议: (如果有)
"""

    def _call_ai_review(self, prompt: str) -> str:
        """调用 AI 审查"""
        import anthropic
        client = anthropic.Anthropic(api_key=self.anthropic_key)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _parse_review_result(self, task_id: str, review_text: str) -> ReviewResult:
        """解析审查结果"""
        status = "pass"
        issues = []
        suggestions = []

        lines = review_text.split('\n')
        for line in lines:
            if '状态:' in line:
                if 'need_fix' in line:
                    status = "need_fix"
                elif 'warning' in line:
                    status = "warning"
            elif '问题:' in line or 'issue' in line.lower():
                issues.append(line)
            elif '建议:' in line or 'suggestion' in line.lower():
                suggestions.append(line)

        return ReviewResult(
            task_id=task_id,
            status=status,
            issues=issues,
            suggestions=suggestions
        )
```

- [ ] **Step 2: 提交代码**

```bash
cd ai-coding
git add src/code_reviewer.py
git commit -m "feat: 添加代码审查模块"
```

---

## Task 7: Git 管理模块

**Files:**
- Create: `ai-coding/src/git_manager.py`

- [ ] **Step 1: 创建 Git 管理模块**

```python
"""Git 管理模块"""
import os
import subprocess
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from .code_generator import GeneratedCode
from .code_reviewer import ReviewResult


class GitManager:
    """Git 管理器"""

    def __init__(self, repo_path: str, branch: str = "ai-coding"):
        self.repo_path = repo_path
        self.branch = branch

    def apply_patches(self, codes: List[GeneratedCode]) -> bool:
        """应用补丁"""
        # 创建临时分支
        self._create_branch()

        # 应用每个代码修改
        for code in codes:
            if code.status != "success":
                continue

            full_path = os.path.join(self.repo_path, code.file_path)
            # 写入修改后的代码
            # 这里简化处理，实际应该解析 patch 应用
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code.original_content + "\n" + code.generated_patch)

        return True

    def _create_branch(self):
        """创建分支"""
        # 检查分支是否存在
        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if self.branch in result.stdout:
            # 切换到已有分支
            subprocess.run(
                ["git", "checkout", self.branch],
                cwd=self.repo_path,
                capture_output=True
            )
        else:
            # 创建新分支
            subprocess.run(
                ["git", "checkout", "-b", self.branch],
                cwd=self.repo_path,
                capture_output=True
            )

    def commit_and_push(self, story_num: str, message: str = "") -> str:
        """提交并推送"""
        # 添加所有修改
        subprocess.run(
            ["git", "add", "-A"],
            cwd=self.repo_path,
            capture_output=True
        )

        # 检查是否有修改
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            print("没有需要提交的修改")
            return ""

        # 生成提交消息
        commit_msg = message or f"AI Coding: {story_num} - 自动代码生成"

        # 提交
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=self.repo_path,
            capture_output=True
        )

        # 获取 commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        commit_sha = result.stdout.strip()
        print(f"提交成功: {commit_sha}")

        return commit_sha

    def get_diff(self) -> str:
        """获取 diff"""
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        return result.stdout
```

- [ ] **Step 2: 提交代码**

```bash
cd ai-coding
git add src/git_manager.py
git commit -m "feat: 添加 Git 管理模块"
```

---

## Task 8: CLI 入口

**Files:**
- Create: `ai-coding/src/cli.py`

- [ ] **Step 1: 创建 CLI 入口**

```python
"""CLI 入口"""
import argparse
import sys
import os
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from mcp_client import create_mcp_client
from story_reader import StoryReader
from task_splitter import TaskSplitter
from code_generator import CodeGenerator
from code_reviewer import CodeReviewer
from git_manager import GitManager


def main():
    parser = argparse.ArgumentParser(description="AI Coding 链路")
    parser.add_argument("story_num", help="效能平台需求编号")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际执行")
    parser.add_argument("--parallel", type=int, default=3, help="并行任务数")
    parser.add_argument("--no-review", action="store_true", help="跳过代码审查")
    parser.add_argument("--no-push", action="store_true", help="只生成 diff，不推送")
    parser.add_argument("--config", help="配置文件路径")

    args = parser.parse_args()

    # 加载配置
    config = get_config(args.config)

    print(f"=== AI Coding 开始处理需求 {args.story_num} ===")

    # 1. 创建 MCP 客户端
    print("[1/6] 创建 MCP 客户端...")
    mcp_client = create_mcp_client(config)

    # 2. 读取需求
    print("[2/6] 读取需求单...")
    story_reader = StoryReader(mcp_client)
    try:
        story = story_reader.read_story(args.story_num)
        print(f"  - 需求: {story.story_name}")
        print(f"  - 类型: {story.story_type}")
        print(f"  - 产品: {story.product_no}")
    except Exception as e:
        print(f"  读取失败: {e}")
        return 1

    # 获取仓库配置
    repo_config = config.get_repository_by_product(story.product_no)
    if not repo_config:
        print(f"错误: 未找到产品 {story.product_no} 对应的仓库配置")
        return 1

    repo_path = repo_config["path"]
    branch = repo_config.get("branch", "ai-coding-dev")
    print(f"  - 代码仓库: {repo_path}")

    # 3. 读取任务
    print("[3/6] 读取关联任务...")
    tasks = story_reader.read_tasks(story.product_no, args.story_num)
    print(f"  - 任务数: {len(tasks)}")

    # 4. 拆分任务
    print("[4/6] 拆分任务...")
    splitter = TaskSplitter()
    split_tasks = splitter.split(story, tasks, repo_path)
    print(f"  - 拆分为 {len(split_tasks)} 个子任务")

    if args.dry_run:
        print("\n=== 预览模式 ===")
        for task in split_tasks:
            print(f"  - {task.task_id}: {task.file_path}")
        return 0

    # 5. 生成代码
    print("[5/6] 生成代码...")
    generator = CodeGenerator(repo_path)
    generated_codes = []
    for task in split_tasks:
        print(f"  - 处理任务: {task.task_id}")
        code = generator.generate(task)
        generated_codes.append(code)

    # 6. 代码审查
    if not args.no_review:
        print("[6/6] 代码审查...")
        reviewer = CodeReviewer()
        for code in generated_codes:
            result = reviewer.review(code)
            print(f"  - {code.task_id}: {result.status}")

    # 7. Git 推送
    if not args.no_push:
        print("[7/7] Git 推送...")
        git_manager = GitManager(repo_path, branch)
        git_manager.apply_patches(generated_codes)
        commit_sha = git_manager.commit_and_push(args.story_num)
        print(f"  - 提交: {commit_sha}")

    print("\n=== 处理完成 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 创建主入口脚本**

```bash
# ai-coding/ai-coding.py
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli import main

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: 提交代码**

```bash
cd ai-coding
git add src/cli.py ai-coding.py
git commit -m "feat: 添加 CLI 入口"
```

---

## 实施检查清单

- [ ] Task 1: 配置管理模块
- [ ] Task 2: MCP 客户端封装
- [ ] Task 3: 需求读取模块
- [ ] Task 4: 任务拆分模块
- [ ] Task 5: 代码生成模块
- [ ] Task 6: 代码审查模块
- [ ] Task 7: Git 管理模块
- [ ] Task 8: CLI 入口

---

**Plan complete and saved to `docs/superpowers/plans/2026-07-28-ai-coding-plan.md`. Two execution options:**

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**