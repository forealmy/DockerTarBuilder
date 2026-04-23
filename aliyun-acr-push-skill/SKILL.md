---
name: aliyun-acr-push
description: 阿里云镜像加速推送。将 Docker 镜像推送到阿里云 ACR 个人版。触发 GitHub Actions workflow，输入一个或多个镜像名后自动执行并返回可下载命令。支持多个镜像用英文逗号分隔，没有版本号时默认 :latest。
---

# 阿里云镜像加速推送

将 Docker 镜像推送到阿里云 ACR 个人版仓库。

## 使用场景

- 用户输入类似 `python:3.14`、`nginx`、`langgenius/dify-api:1.11.2` 等镜像名时触发
- 支持多个镜像，英文逗号分隔，如 `python:3.14,python:3.13,nginx`
- 没有版本号时默认使用 `:latest`
- 需要将公开镜像加速推送到阿里云 ACR 时使用

## 镜像名处理规则

Workflow 转换逻辑（完全对应 `Push-to-ACRPersonalEdition.yml`）：

1. 如果没有 tag，默认添加 `:latest`
2. `/` → `_0_`
3. 清理特殊字符，只保留 `a-zA-Z0-9._-`
4. 3 个及以上连续下划线合并为 2 个
5. 去除首尾的 `-` 和 `_`

示例：

| 原镜像 | 转换后 |
|--------|--------|
| `python:3.14` | `python:3.14` |
| `nginx` | `nginx:latest` |
| `langgenius/dify-api:1.11.2` | `langgenius_0_dify-api:1.11.2` |

## 执行流程

1. 解析用户输入的镜像名列表，处理默认版本号
2. **检查历史记录**：查找 `memory/acr-push-history.json`，展示之前的执行历史
3. 使用 gh CLI 触发 GitHub Actions workflow
4. 等待 workflow 运行完成
5. **记录执行**：将本次执行信息写入历史记录文件
6. 返回执行结果和 Pull & Retag Commands
7. 返回时附带 GitHub 链接

## 触发命令

```bash
gh workflow run Push-to-ACRPersonalEdition.yml -f docker_images="python:3.14,nginx:latest" --repo forealmy/DockerTarBuilder
```

## 参数

- `docker_images`: Docker 镜像列表，英文逗号分隔

## 目标仓库信息（可配置）

- GitHub 仓库: forealmy/DockerTarBuilder
- Workflow 文件: Push-to-ACRPersonalEdition.yml
- ACR 地址: crpi-dsuujqmghq4pfebi.cn-hangzhou.personal.cr.aliyuncs.com/my-dify-prod
- 环境: acr-prod（需在 GitHub Settings → Environments 配置 `ACR_TARGET_REGISTRY` 环境变量）

## 返回格式

```
✅ 触发成功！
Run ID: <run_id>
状态: ✅ 成功 (completed in <耗时>)
GitHub 链接: https://github.com/forealmy/DockerTarBuilder/actions/runs/<run_id>

📤 Pull & Retag Commands：
sudo docker pull '<acr_image>' && sudo docker tag '<acr_image>' '<original>' && sudo docker rmi '<acr_image>'
```

## 构造 GitHub 链接

根据 workflow 代码，GitHub 运行链接格式为：
- 运行列表：`https://github.com/{owner}/{repo}/actions/workflows/Push-to-ACRPersonalEdition.yml`
- 特定运行：`https://github.com/{owner}/{repo}/actions/runs/{run_id}`

## 辅助脚本

提供脚本 `scripts/generate-links.py` 用于生成链接和 Pull 命令。

### 脚本功能

1. **根据镜像名生成 Pull 命令**：输入镜像名，生成 ACR pull 命令
2. **根据 run_id 生成链接**：输入 run_id，生成 GitHub 运行链接
3. **查看历史记录**：列出最近的运行记录

### 使用方法

```bash
# 根据镜像名生成 pull 命令
python scripts/generate-links.py -i "python:3.14"

# 多个镜像
python scripts/generate-links.py -i "python:3.14,nginx:latest,redis:7"

# 指定自定义仓库和 ACR 地址
python scripts/generate-links.py -i "python:3.14" \
  --repo owner/repo \
  --acr "crpi-xxx.cn-hangzhou.personal.cr.aliyuncs.com/my-namespace" \
  --workflow Push-to-ACRPersonalEdition.yml

# 根据 run_id 生成链接
python scripts/generate-links.py -r 23351281994

# 列出最近运行记录
python scripts/generate-links.py --list

# 输出 JSON 格式
python scripts/generate-links.py -i "python:3.14" --json
```

### 输出示例

```bash
# 输入
$ python scripts/generate-links.py -i "python:3.14,nginx"

# 输出
输入镜像: python:3.14, nginx:latest
Workflow 链接: https://github.com/forealmy/DockerTarBuilder/actions/workflows/Push-to-ACRPersonalEdition.yml

生成的 Pull 命令:

原镜像: python:3.14
ACR 镜像: crpi-dsuujqmghq4pfebi.cn-hangzhou.personal.cr.aliyuncs.com/my-dify-prod/python:3.14
命令: sudo docker pull 'crpi-.../python:3.14' && sudo docker tag '...' 'python:3.14' && sudo docker rmi '...'

原镜像: nginx:latest
ACR 镜像: crpi-dsuujqmghq4pfebi.cn-hangzhou.personal.cr.aliyuncs.com/my-dify-prod/nginx:latest
命令: sudo docker pull '...' && sudo docker tag '...' 'nginx:latest' && sudo docker rmi '...'
```

## 执行记录

每次触发时自动记录到本地文件：`memory/acr-push-history.json`

记录格式：
```json
{
  "run_id": "23351281994",
  "images": "python:3.14",
  "timestamp": "2026-03-20T16:02:01Z",
  "status": "success"
}
```

## gh CLI 路径

gh CLI 位于: `C:\Program Files\GitHub CLI\gh.exe`

注意：需要先将 GitHub CLI 加入 PATH 环境变量。
