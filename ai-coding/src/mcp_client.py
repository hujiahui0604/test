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