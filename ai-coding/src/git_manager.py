"""Git 管理模块"""
import os
import subprocess
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