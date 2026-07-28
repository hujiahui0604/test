"""代码生成模块 - 支持多厂商 LLM"""
import os
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass

# 处理相对导入
if __name__ != "__main__" and "." in __name__:
    from .task_splitter import SplitTask
    from .config import get_config
else:
    from task_splitter import SplitTask
    from config import get_config


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

    def __init__(self, repo_path: str, config=None):
        self.repo_path = repo_path
        self.config = config or get_config()
        # 获取当前厂商配置
        self.provider = self.config.get_active_provider()
        self.api_key = self.config.get_active_api_key()
        self.model = self.config.get_active_model()

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

        # 3. 返回结果
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
```{task.language if hasattr(task, 'language') else ''}
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
        # Claude Code 模式：生成可导入 Claude Code 的 prompt 文件
        if self.provider == "claude-code":
            return self._generate_claude_code_prompt(prompt)

        if not self.api_key:
            print(f"警告: {self.provider} API Key 未配置，使用模拟结果")
            return self._generate_mock_patch()

        # 根据厂商调用不同的 API
        if self.provider == "anthropic":
            return self._call_anthropic(prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt)
        elif self.provider == "ali":
            return self._call_ali(prompt)
        elif self.provider == "deepseek":
            return self._call_deepseek(prompt)
        elif self.provider == "kimi":
            return self._call_kimi(prompt)
        elif self.provider == "minmax":
            return self._call_minmax(prompt)
        elif self.provider == "glm":
            return self._call_glm(prompt)
        else:
            print(f"未知厂商: {self.provider}，使用模拟结果")
            return self._generate_mock_patch()

    def _generate_claude_code_prompt(self, prompt: str) -> str:
        """生成 Claude Code Prompt 模式 - 输出可导入的 prompt 文件"""
        # Claude Code 模式下，生成一个可以直接导入的 prompt
        # 用户可以将这个 prompt 复制到 Claude Code 中执行
        return f"""
# AI Coding 任务 - 请在 Claude Code 中执行

## 任务说明

{prompt}

## 执行步骤

1. 理解上述需求
2. 分析代码逻辑
3. 生成代码修改
4. 输出完整的修改后的代码或 diff

## 输出格式

请按以下格式输出：
```
## 修改后的代码
```语言
[完整的修改后代码]
```

或使用 diff 格式：
```
## Diff
```diff
[diff 内容]
```
```
"""

    def _call_anthropic(self, prompt: str) -> str:
        """调用 Anthropic Claude API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text
        except Exception as e:
            print(f"Anthropic API 调用失败: {e}")
            return self._generate_mock_patch()

    def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096
            )

            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API 调用失败: {e}")
            return self._generate_mock_patch()

    def _call_ali(self, prompt: str) -> str:
        """调用阿里通义千问 API"""
        try:
            import dashscope
            dashscope.api_key = self.api_key

            from dashscope import Generation
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=4096
            )

            if response.status_code == 200:
                return response.output.text
            else:
                print(f"阿里 API 调用失败: {response.code} - {response.message}")
                return self._generate_mock_patch()
        except Exception as e:
            print(f"阿里 API 调用失败: {e}")
            return self._generate_mock_patch()

    def _call_deepseek(self, prompt: str) -> str:
        """调用 DeepSeek API"""
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"DeepSeek API 调用失败: {e}")
            return self._generate_mock_patch()

    def _call_kimi(self, prompt: str) -> str:
        """调用 Kimi (月之暗面) API"""
        try:
            response = requests.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Kimi API 调用失败: {e}")
            return self._generate_mock_patch()

    def _call_minmax(self, prompt: str) -> str:
        """调用 MiniMax API"""
        try:
            response = requests.post(
                "https://api.minimax.chat/v1/text/chatcompletion_pro",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"MiniMax API 调用失败: {e}")
            return self._generate_mock_patch()

    def _call_glm(self, prompt: str) -> str:
        """调用智谱 GLM API"""
        try:
            response = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"GLM API 调用失败: {e}")
            return self._generate_mock_patch()

    def _generate_mock_patch(self) -> str:
        """生成模拟补丁（用于测试）"""
        return """
// TODO: AI 生成的代码应该在这里
// 当前为模拟结果（请配置 API Key 生效）
"""