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