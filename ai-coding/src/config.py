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
        return str(home / ".ai-coding" / "config.yaml")

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
        # 从环境变量读取 ${VAR} 格式
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