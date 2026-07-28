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