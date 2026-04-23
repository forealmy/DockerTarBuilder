#!/usr/bin/env python3
"""
根据镜像名生成 GitHub Actions 运行链接。

根据 workflow 代码中的转换逻辑，将用户输入的镜像名转换为 ACR 镜像名，
并生成对应的 GitHub Actions 运行链接。

转换逻辑 (来自 workflow):
- 原镜像: python:3.14
- ACR 前缀: crpi-dsuujqmghq4pfebi.cn-hangzhou.personal.cr.aliyuncs.com/my-dify-prod
- 转换规则: 镜像名中的 "/" 转换为 "_0_"，然后清理特殊字符
- 例如: langgenius/dify-api:1.11.2 -> langgenius_0_dify-api:1.11.2
"""

import argparse
import json
import os
import re
from datetime import datetime, timezone, timedelta

# 默认值（可被命令行参数覆盖）
DEFAULT_ACR_REGISTRY = "crpi-dsuujqmghq4pfebi.cn-hangzhou.personal.cr.aliyuncs.com/my-dify-prod"
DEFAULT_GITHUB_REPO = "forealmy/DockerTarBuilder"
DEFAULT_WORKFLOW_FILE = "Push-to-ACRPersonalEdition.yml"


def normalize_image(image):
    """
    根据 workflow 代码中的转换逻辑处理镜像名。

    规则（完全匹配 Push-to-ACRPersonalEdition.yml）:
    1. 如果没有 tag，默认添加 :latest
    2. 将镜像名中的 "/" 替换为 "_0_"
    3. 清理特殊字符，只保留字母数字 . - 和 _
    4. 将 3 个及以上连续下划线合并为 2 个
    5. 去除首尾的横线和下划线
    """
    # 添加默认 tag
    if ":" not in image:
        image = f"{image}:latest"

    # 分离 repo 和 tag (最后一次出现的 : 是分隔符)
    repo_part, tag_part = image.rsplit(":", 1)

    # 转换 repo 部分：/ → _0_
    clean_repo = repo_part.replace("/", "_0_")
    # 只保留字母数字 . - 和 _
    clean_repo = re.sub(r'[^a-zA-Z0-9._-]', '', clean_repo)
    # 将 3 个及以上连续下划线合并为 2 个（等价于 sed 's/___*/__/g'）
    clean_repo = re.sub(r'___+', '__', clean_repo)
    # 去除首尾的横线和下划线
    clean_repo = clean_repo.strip('_-')

    if not clean_repo:
        clean_repo = "unknown"

    return f"{clean_repo}:{tag_part}"


def generate_acr_image(image, acr_registry):
    """生成 ACR 镜像完整地址"""
    acr_image = normalize_image(image)
    return f"{acr_registry}/{acr_image}"


def generate_pull_command(image, acr_registry):
    """生成 docker pull 命令"""
    acr_image = generate_acr_image(image, acr_registry)
    # 如果原镜像没有 tag，使用 latest
    if ":" not in image:
        original = f"{image}:latest"
    else:
        original = image

    return f"sudo docker pull '{acr_image}' && sudo docker tag '{acr_image}' '{original}' && sudo docker rmi '{acr_image}'"


def generate_links(images, github_repo=None, acr_registry=None, workflow_file=None):
    """
    根据镜像列表生成 GitHub 链接和 pull 命令。

    Args:
        images: 镜像名列表，可以是逗号分隔的字符串或列表
        github_repo: GitHub 仓库，格式 owner/repo
        acr_registry: ACR 仓库地址
        workflow_file: workflow 文件名

    Returns:
        dict: 包含链接和命令的字典
    """
    github_repo = github_repo or DEFAULT_GITHUB_REPO
    acr_registry = acr_registry or DEFAULT_ACR_REGISTRY
    workflow_file = workflow_file or DEFAULT_WORKFLOW_FILE

    # 如果是字符串，按逗号分割
    if isinstance(images, str):
        image_list = [i.strip() for i in images.split(",")]
    else:
        image_list = images

    # 处理每个镜像
    results = {
        "inputs": image_list,
        "workflow_url": f"https://github.com/{github_repo}/actions/workflows/{workflow_file}",
        "runs": [],
        "commands": []
    }

    for img in image_list:
        if not img:
            continue

        acr_img = generate_acr_image(img, acr_registry)
        pull_cmd = generate_pull_command(img, acr_registry)

        results["runs"].append({
            "input_image": img,
            "acr_image": acr_img,
            "run_url": None  # 运行后填充
        })
        results["commands"].append({
            "original": img,
            "acr": acr_img,
            "pull_command": pull_cmd
        })

    return results


def generate_link_from_run_id(run_id, github_repo=None):
    """根据 run_id 生成 GitHub 运行链接"""
    github_repo = github_repo or DEFAULT_GITHUB_REPO
    return {
        "run_id": run_id,
        "run_url": f"https://github.com/{github_repo}/actions/runs/{run_id}",
        "logs_url": f"https://github.com/{github_repo}/actions/runs/{run_id}"
    }


def main():
    parser = argparse.ArgumentParser(
        description="根据镜像名生成 GitHub Actions 链接和 Pull 命令"
    )
    parser.add_argument(
        "-i", "--images",
        help="镜像名，多个用逗号分隔，如: python:3.14,nginx:latest"
    )
    parser.add_argument(
        "-r", "--run-id",
        help="根据 run_id 生成链接"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="输出 JSON 格式"
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="列出最近的运行链接"
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_GITHUB_REPO,
        help=f"GitHub 仓库（格式: owner/repo），默认: {DEFAULT_GITHUB_REPO}"
    )
    parser.add_argument(
        "--acr",
        default=DEFAULT_ACR_REGISTRY,
        help=f"ACR 仓库地址，默认: {DEFAULT_ACR_REGISTRY}"
    )
    parser.add_argument(
        "--workflow",
        default=DEFAULT_WORKFLOW_FILE,
        help=f"Workflow 文件名，默认: {DEFAULT_WORKFLOW_FILE}"
    )

    args = parser.parse_args()

    if args.run_id:
        result = generate_link_from_run_id(args.run_id, github_repo=args.repo)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Run ID: {result['run_id']}")
            print(f"运行链接: {result['run_url']}")
            print(f"日志链接: {result['logs_url']}")

    elif args.images:
        result = generate_links(
            args.images,
            github_repo=args.repo,
            acr_registry=args.acr,
            workflow_file=args.workflow
        )
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"输入镜像: {', '.join(result['inputs'])}")
            print(f"Workflow 链接: {result['workflow_url']}")
            print("\n生成的 Pull 命令:")
            for cmd in result["commands"]:
                print(f"\n原镜像: {cmd['original']}")
                print(f"ACR 镜像: {cmd['acr']}")
                print(f"命令: {cmd['pull_command']}")

    elif args.list:
        # 读取历史记录：优先查找 memory/acr-push-history.json
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "acr-push-history.json"),
            os.path.join(os.path.expanduser("~"), ".qclaw", "workspace", "memory", "acr-push-history.json"),
        ]
        history_file = None
        for p in possible_paths:
            if os.path.exists(p):
                history_file = p
                break

        if history_file:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            print("最近的运行记录:")
            print("-" * 60)
            for item in history[:10]:
                ts = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                # 转换为北京时间
                beijing_tz = timezone(timedelta(hours=8))
                ts_beijing = ts.astimezone(beijing_tz)
                print(f"Run ID: {item['run_id']}")
                print(f"镜像: {item['images']}")
                print(f"时间: {ts_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"链接: {item.get('url', '')}")
                print("-" * 60)
        else:
            print("未找到历史记录文件")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
