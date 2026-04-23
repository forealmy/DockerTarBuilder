---
name: aliyun-acr-push
description: 阿里云镜像加速推送。将 Docker 镜像推送到阿里云 ACR 个人版。触发 GitHub Actions workflow，输入一个或多个镜像名后自动执行并返回可下载命令。支持多个镜像用英文逗号分隔，没有版本号时默认 :latest。
---

# 阿里云镜像加速推送

将 Docker 镜像推送到阿里云 ACR 个人版仓库。

## 首次使用配置

首次使用前需要完成以下配置之一：

### 方式一：使用 gh CLI（推荐）

1. 安装 GitHub CLI：https://cli.github.com/
2. 运行 `gh auth login` 完成登录
3. Skill 会自动检测并使用 gh

### 方式二：使用 GitHub Token

1. 创建 Personal Access Token（classic）：
   - GitHub → Settings → Developer settings → Personal access tokens → Generate new token
   - 所需权限：**workflow**
2. 设置环境变量 `GITHUB_TOKEN`：
   - Windows (PowerShell): `$env:GITHUB_TOKEN='ghp_xxx'`
   - Windows (CMD): `set GITHUB_TOKEN=ghp_xxx`
   - 持久化（Windows）: 系统属性 → 环境变量 → 新建用户变量

### 认证优先级

脚本自动选择认证方式，优先级为：**gh CLI** → **GITHUB_TOKEN**

首次运行时若未检测到认证，会自动输出配置指引。

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

1. **检测认证方式**：优先使用 gh CLI，次选 GITHUB_TOKEN 环境变量
2. 解析用户输入的镜像名列表，处理默认版本号
3. **检查历史记录**：查找 `memory/acr-push-history.json`，展示之前的执行历史
4. 触发 GitHub Actions workflow
5. **记录执行**：将本次执行信息写入历史记录文件
6. 返回执行结果和 Pull & Retag Commands
7. 返回时附带 GitHub 链接

## 触发命令

### 方式一：gh CLI

```bash
gh workflow run Push-to-ACRPersonalEdition.yml -f docker_images="python:3.14,nginx:latest" --repo forealmy/DockerTarBuilder
```

### 方式二：REST API（curl）

需要 `GITHUB_TOKEN` 环境变量：

```bash
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/forealmy/DockerTarBuilder/actions/workflows/Push-to-ACRPersonalEdition.yml/dispatches \
  -d '{"ref":"master","inputs":{"docker_images":"python:3.14,nginx:latest"}}'
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
GitHub 链接: https://github.com/forealmy/DockerTarBuilder/actions/runs/<run_id>

📤 Pull & Retag Commands：
sudo docker pull '<acr_image>' && sudo docker tag '<acr_image>' '<original>' && sudo docker rmi '<acr_image>'
```

## 构造 GitHub 链接

- 运行列表：`https://github.com/{owner}/{repo}/actions/workflows/Push-to-ACRPersonalEdition.yml`
- 特定运行：`https://github.com/{owner}/{repo}/actions/runs/{run_id}`

## 辅助脚本

提供脚本 `scripts/generate-links.py` 用于生成链接和 Pull 命令。

### 脚本功能

1. **检测认证状态**：`--check-auth` 输出当前可用认证方式和配置指引
2. **触发 workflow**：`--trigger` 自动选择认证方式触发
3. **根据镜像名生成 Pull 命令**：输入镜像名，生成 ACR pull 命令
4. **根据 run_id 生成链接**：输入 run_id，生成 GitHub 运行链接
5. **查看历史记录**：列出最近的运行记录

### 使用方法

```bash
# 检测可用认证方式（首次使用前必读）
python scripts/generate-links.py --check-auth

# 触发 workflow（自动选择 gh 或 API）
python scripts/generate-links.py -i "python:3.14,nginx:latest" --trigger

# 根据镜像名生成 pull 命令（不触发）
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
# 检测认证
$ python scripts/generate-links.py --check-auth
============================================================
✓ 检测到 gh CLI 已登录，将使用 gh 方式触发 workflow
============================================================

# 触发 workflow
$ python scripts/generate-links.py -i "python:3.14" --trigger
使用 gh CLI 触发 workflow...
✓ 触发成功，Run ID: 23351281994
  查看运行: https://github.com/forealmy/DockerTarBuilder/actions/runs/23351281994
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
