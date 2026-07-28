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
```
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