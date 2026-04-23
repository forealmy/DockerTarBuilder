# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

DockerTarBuilder 是一个 GitHub Actions 工作流项目，用于将 Docker 镜像构建为离线压缩包（tar.gz），存储在 GitHub Release 或 Artifact 中。

## 核心工作流架构

### 按架构分类的工作流（`.github/workflows/`）

| 文件 | 架构 | 输出方式 | 适用场景 |
|------|------|----------|----------|
| `amd64.yml` | x86-64 | Artifact | <2GB 镜像 |
| `amd64-release.yml` | x86-64 | Release | <2GB 镜像 |
| `arm64.yml` | ARM64 | Artifact | <2GB 镜像 |
| `arm64-release.yml` | ARM64 | Release | <2GB 镜像 |
| `arm32.yml` | ARM32 | Artifact | <2GB 镜像 |
| `arm32-release.yml` | ARM32 | Release | <2GB 镜像 |
| `Push-to-ACRPersonalEdition.yml` | amd64 | 阿里云 ACR | 推送镜像到阿里云 |

### 选择工作流的规则

- 镜像 <2GB → 使用 `*release*.yml`（输出到 GitHub Release）
- 镜像 2-5GB → 使用 `*.yml`（输出到 Artifact，保留 1 天）
- 镜像 >5GB → 本项目不适用

## 工作流输入参数

所有工作流通过 `workflow_dispatch` 触发，接受 `docker_images` 参数：
- 格式：镜像名列表，英文逗号分隔
- 示例：`python:3.14,nginx:latest,redis:7`
- 不带版本号时默认 `:latest`

## 镜像名转换规则

镜像名中的 `/` 会转换为 `_`，用于文件名和 ACR 仓库路径：
- `langgenius/dify-api:1.11.2` → 存储为 `dify-api_1.11.2.tar.gz`
- `nginx:latest` → 存储为 `nginx_latest.tar.gz`

## 恢复离线镜像

从 Release/Artifact 下载 `.tar.gz` 后：
```bash
docker load -i xxx.tar.gz
# 或
docker load < xxx.tar.gz
```

## 阿里云 ACR 推送

`Push-to-ACRPersonalEdition.yml` 将镜像推送到阿里云 ACR 个人版：
- 目标仓库：`crpi-dsuujqmghq4pfebi.cn-hangzhou.personal.cr.aliyuncs.com/my-dify-prod`
- 需要 Secrets：`ALIYUN_ACCESS_KEY_ID`、`ALIYUN_ACCESS_KEY_SECRET`

## 辅助脚本

`aliyun-acr-push-skill/scripts/generate-links.py` - 根据镜像名生成 Pull 命令或查看历史记录。

## 非代码项目

本仓库不包含传统意义上的可构建代码。所有"开发"工作都是修改 YAML 工作流文件本身。
