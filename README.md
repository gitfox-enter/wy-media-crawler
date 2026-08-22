# 网易文创资源矩阵 → ima 知识库 自动导入

自动抓取网易文创资源矩阵（necc）40 个网易号的最新文章，通过 ima Open API 导入到 ima 知识库对应文件夹中。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Actions (daily-import.yml)          │
│                                                             │
│  1. 读取 sites_to_folders.yaml 配置                          │
│  2. 遍历 40 个网易号，爬取最新文章列表                        │
│  3. 与 wy_crawl_results.json 去重比对                        │
│  4. 通过 ima Open API 批量导入（10 条/批）                   │
│  5. 实时更新去重文件，git push 回仓库                         │
└─────────────────────────────────────────────────────────────┘
```

## 配置

### GitHub Secrets

| Secret | 说明 |
|--------|------|
| `IMA_CLIENT_ID` | ima openapi client_id |
| `IMA_API_KEY` | ima openapi api_key |

### GitHub Variables

| Variable | 说明 | 默认值 |
|----------|------|--------|
| `ENABLE_DAILY` | 是否启用定时任务 | `true` |

### 站点映射配置

编辑 `sites_to_folders.yaml`，配置网易号 TID 到 ima 知识库文件夹的映射：

```yaml
account_name: "folder_id_xxx"
```

当前共 40 个网易号映射，详见 `sites_to_folders.yaml`。

## 快速开始

1. **Fork** 本仓库
2. 在 GitHub Secrets 中设置 `IMA_CLIENT_ID` 和 `IMA_API_KEY`
3. （可选）在 GitHub Variables 中设置 `ENABLE_DAILY=false` 禁用自动运行
4. 手动触发工作流测试：
   - Actions → 每日网易文创导入 → Run workflow → 勾选 `dry_run` 模式
5. 确认 dry_run 输出无误后，启用定时任务

## 手动触发

Go to Actions → 每日网易文创导入 → Run workflow

可选参数：
- `dry_run`：仅爬取和比对，不执行导入，用于验证

## 文件说明

| 文件 | 说明 |
|------|------|
| `wy_crawl_ima.py` | 主抓取导入脚本 |
| `sites_to_folders.yaml` | 40 个网易号 → ima 文件夹映射配置 |
| `wy_crawl_results.json` | 去重基准文件（已导入 3025 篇） |
| `.github/workflows/daily-import.yml` | GitHub Actions 工作流配置 |
| `README.md` | 项目入口文档 |
| `ONBOARDING.md` | 上手指南 |
| `MAINTENANCE.md` | 维护手册 |

## 定时任务

- 每日 14:00 UTC（北京时间 22:00）自动运行
- 可通过 `ENABLE_DAILY=false` 禁用
- 手动触发时支持 `dry_run` 参数

## 技术栈

- **语言**: Python 3
- **爬虫**: urllib（纯标准库，无外部 HTTP 依赖）
- **解析**: BeautifulSoup（HTML 解析）
- **API**: ima Open API（import_urls 端点）
- **自动化**: GitHub Actions
- **配置**: YAML 文件

## 相关项目

- [bzuu-ima-importer](https://github.com/gitfox-enter/bzuu-ima-importer) — 亳州学院官网 → ima 知识库 自动导入（同技术栈，更复杂的工作流体系）
- [RSSForge](https://github.com/gitfox-enter/RSSForge) — RSS 聚合器，支持 ima 知识库集成