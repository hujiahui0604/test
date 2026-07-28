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
```
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