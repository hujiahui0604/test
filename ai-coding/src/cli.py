"""CLI 入口"""
import argparse
import sys
import os
import json
from datetime import datetime
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


def confirm_task_fields(story_num: str) -> dict:
    """请求用户确认任务单字段"""
    print("\n" + "=" * 50)
    print("⚠️  请确认以下任务单字段（AI 无法自动生成）:")
    print("=" * 50)

    defaults = {
        "versionNO": "ALGOV202301.02.013M08",
        "modifierNo": "jinhx21900",
        "modifierName": "金华学",
        "projectNo": "2024120026",
        "projectName": "O32产品维护-OTRADE项目",
        "estimateWorkload": "4.0"
    }

    confirmed = {}
    for field, default in defaults.items():
        value = input(f"  {field} [{default}]: ").strip()
        confirmed[field] = value if value else default

    return confirmed


def backup_tasks(story_num: str, story, tasks: list, confirmed_fields: dict, repo_path: str):
    """本地备份任务单"""
    # 创建备份目录
    backup_dir = Path(repo_path).parent / "ai-coding" / "tasks"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{story_num}_{timestamp}.json"

    # 备份数据
    backup_data = {
        "story_num": story.story_num,
        "story_name": story.story_name,
        "product_no": story.product_no,
        "created_at": datetime.now().isoformat(),
        "tasks": [
            {
                "taskNums": t.task_id,
                "name": t.task_name,
                "description": t.description,
                "edit_description": t.edit_description,
                "file_path": t.file_path,
                "language": getattr(t, 'language', 'cpp'),
            }
            for t in tasks
        ],
        "confirmed_fields": confirmed_fields,
        "repo_path": repo_path
    }

    # 写入文件
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 任务单已备份到: {backup_file}")
    return str(backup_file)


def main():
    parser = argparse.ArgumentParser(
        description="AI Coding - 效能平台需求自动代码生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ai-coding.py 202510284148
  python ai-coding.py 202510284148 --dry-run
  python ai-coding.py 202510284148 --no-push
  python ai-coding.py 202510284148 --provider deepseek
  python ai-coding.py 202510284148 --config /path/to/config.yaml

支持的 LLM 厂商:
  anthropic, openai, ali, deepseek, kimi, minmax, glm
        """
    )
    parser.add_argument("story_num", help="效能平台需求编号")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际执行")
    parser.add_argument("--parallel", type=int, default=3, help="并行任务数")
    parser.add_argument("--no-review", action="store_true", help="跳过代码审查")
    parser.add_argument("--no-push", action="store_true", help="只生成代码，不推送")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--provider", choices=["claude-code", "anthropic", "openai", "ali", "deepseek", "kimi", "minmax", "glm"],
                        help="指定 LLM 厂商（覆盖配置文件）")
    parser.add_argument("--no-confirm", action="store_true", help="跳过用户确认步骤")

    args = parser.parse_args()

    # 加载配置
    config = get_config(args.config)

    # 如果指定了 provider，更新配置
    if args.provider:
        config._config["active_provider"] = args.provider

    # 显示启动信息
    provider = config.get_active_provider()
    model = config.get_active_model()
    is_claude_code = config.is_claude_code_mode()
    print(f"=== AI Coding 开始处理需求 {args.story_num} ===")
    print(f"  LLM 厂商: {provider} | 模型: {model}")
    if is_claude_code:
        print(f"  模式: Claude Code (无需 API Key)")

    # 1. 创建 MCP 客户端
    print("\n[1/8] 创建 MCP 客户端...")
    mcp_client = create_mcp_client(config)

    # 2. 读取需求
    print("[2/8] 读取需求单...")
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
    print("[3/8] 读取关联任务...")
    tasks = story_reader.read_tasks(story.product_no, args.story_num)
    print(f"  - 任务数: {len(tasks)}")

    # 4. 拆分任务 + 用户确认 + 备份
    print("[4/8] 拆分任务 + 用户确认 + 备份...")
    splitter = TaskSplitter()
    split_tasks = splitter.split(story, tasks, repo_path)
    print(f"  - 拆分为 {len(split_tasks)} 个子任务")

    # 4.1 用户确认字段（除非使用 --no-confirm）
    if not args.no_confirm:
        confirmed_fields = confirm_task_fields(args.story_num)
    else:
        confirmed_fields = {
            "versionNO": "ALGOV202301.02.013M08",
            "modifierNo": "jinhx21900",
            "modifierName": "金华学",
            "projectNo": "2024120026",
            "projectName": "O32产品维护-OTRADE项目",
            "estimateWorkload": "4.0"
        }

    # 4.2 本地备份任务单
    backup_file = backup_tasks(args.story_num, story, split_tasks, confirmed_fields, repo_path)

    if args.dry_run:
        print("\n=== 预览模式 ===")
        for task in split_tasks:
            print(f"  - {task.task_id}: {task.file_path}")
        return 0

    # 5. 生成代码
    print(f"[5/8] 生成代码 (厂商: {provider})...")
    generator = CodeGenerator(repo_path, config)
    generated_codes = []
    success_count = 0
    for task in split_tasks:
        code = generator.generate(task)
        status_icon = "✓" if code.status == "success" else "✗"
        print(f"  {status_icon} {task.task_id}: {code.status}")
        if code.status == "success":
            success_count += 1
        generated_codes.append(code)

    print(f"  - 成功: {success_count}/{len(split_tasks)}")

    # 6. 代码审查
    if not args.no_review:
        print("[6/8] 代码审查...")
        reviewer = CodeReviewer()
        for code in generated_codes:
            result = reviewer.review(code)
            print(f"  - {code.task_id}: {result.status}")

    # 7. Git 推送
    if not args.no_push:
        print("[7/8] Git 推送...")
        git_manager = GitManager(repo_path, branch)
        git_manager.apply_patches(generated_codes)
        commit_sha = git_manager.commit_and_push(args.story_num)
        print(f"  - 提交: {commit_sha}")

    print("\n=== 处理完成 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())