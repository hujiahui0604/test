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
            # 多厂商 LLM 配置
            "providers": {
                # Claude Code 模式 - 使用当前会话模型，无需 API Key
                "claude-code": {
                    "enabled": True,
                    "model": "current-session"
                },
                "anthropic": {
                    "enabled": False,
                    "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
                    "model": "claude-sonnet-4-6"
                },
                "openai": {
                    "enabled": False,
                    "api_key": os.environ.get("OPENAI_API_KEY", ""),
                    "model": "gpt-4o"
                },
                "ali": {
                    "enabled": False,
                    "api_key": os.environ.get("DASHSCOPE_API_KEY", ""),
                    "model": "qwen-turbo"
                },
                "deepseek": {
                    "enabled": False,
                    "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
                    "model": "deepseek-chat"
                },
                "kimi": {
                    "enabled": False,
                    "api_key": os.environ.get("MOONSHOT_API_KEY", ""),
                    "model": "moonshot-v1-8k"
                },
                "minmax": {
                    "enabled": False,
                    "api_key": os.environ.get("MINMAX_API_KEY", ""),
                    "model": "abab6.5s-chat"
                },
                "glm": {
                    "enabled": False,
                    "api_key": os.environ.get("ZHIPU_API_KEY", ""),
                    "model": "glm-4"
                }
            },
            # 默认使用 claude-code 模式（无需 API Key）
            "active_provider": "claude-code",
            # MCP 配置
            "mcp": {
                "access_key": os.environ.get("ACCESS_KEY", ""),
                "base_url": "https://dev.hundsun.com/openapi/apis/v1/mcp"
            },
            # 仓库配置
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

    def get_anthropic_api_key(self) -> str:
        """获取 Anthropic API Key"""
        key = self._config.get("anthropic", {}).get("api_key", "")
        if key.startswith("${") and key.endswith("}"):
            env_var = key[2:-1]
            return os.environ.get(env_var, "")
        return key

    def get_anthropic_model(self) -> str:
        """获取 Anthropic 模型"""
        return self._config.get("anthropic", {}).get("model", "claude-sonnet-4-6")

    # ===== 多厂商配置 =====

    def get_active_provider(self) -> str:
        """获取当前使用的厂商"""
        return self._config.get("active_provider", "anthropic")

    def get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """获取指定厂商的配置"""
        providers = self._config.get("providers", {})
        return providers.get(provider, {})

    def get_active_provider_config(self) -> Optional[Dict[str, Any]]:
        """获取当前厂商的完整配置"""
        active = self.get_active_provider()
        return self.get_provider_config(active)

    def get_active_api_key(self) -> str:
        """获取当前厂商的 API Key"""
        config = self.get_active_provider_config()
        if not config:
            return ""

        api_key = config.get("api_key", "")
        # 从环境变量读取 ${VAR} 格式
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            return os.environ.get(env_var, "")
        return api_key

    def get_active_model(self) -> str:
        """获取当前厂商的模型"""
        config = self.get_active_provider_config()
        if not config:
            return ""
        return config.get("model", "")

    def is_provider_enabled(self, provider: str) -> bool:
        """检查厂商是否启用"""
        config = self.get_provider_config(provider)
        return config.get("enabled", False) if config else False

    def is_claude_code_mode(self) -> bool:
        """检查是否使用 Claude Code 模式（无需 API Key）"""
        return self.get_active_provider() == "claude-code"


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """获取配置实例"""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config