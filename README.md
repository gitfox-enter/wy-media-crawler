# 网易文创资源矩阵 → ima 知识库 自动导入

自动抓取网易文创资源矩阵（necc）30 个网易号的最新文章，导入 ima 知识库。

## 配置

在 GitHub Actions Secrets 中设置：

| Secret | 说明 |
|--------|------|
| `IMA_CLIENT_ID` | ima openapi client_id |
| `IMA_API_KEY` | ima openapi api_key |

## 变量

在 GitHub Actions Variables 中设置：

| Variable | 说明 | 默认值 |
|----------|------|--------|
| `ENABLE_DAILY` | 是否启用定时任务 | `true` |

## 手动触发

Go to Actions → 每日网易文创导入 → Run workflow → 可选 dry_run 模式。

## 文件说明

- `wy_crawl_ima.py` — 主抓取导入脚本
- `wy_crawl_results.json` — 去重基准文件（已导入 1986 篇）