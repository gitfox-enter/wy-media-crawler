# 网易文创导入器 Onboarding Guide

> 面向新手的快速上手指南，无需阅读代码即可理解项目如何工作。

---

## TL;DR

这是一个自动化的机器人，每天定时爬取 40 个网易号的最新文章，自动导入到 ima 知识库中，无需手动操作。

## 项目做什么？

想象你关注了 40 个网易号（如"网易文创"、"网易数读"、"网易科技"等），每天手动打开每个号看更新是件麻烦事。这个项目就是帮你做这件事的机器人：

1. 每天 14:00 UTC（北京时间 22:00）自动访问 40 个网易号
2. 检查是否有新文章发布
3. 将新文章批量导入到 ima 知识库的对应文件夹中
4. 自动跳过已导入过的文章（基于去重文件）

## 核心概念（仅需掌握 4 个）

| 概念 | 是什么 | 涉及文件 | 何时需要关心 |
|------|--------|----------|-------------|
| 站点映射 | 哪个网易号导入到哪个 ima 文件夹 | sites_to_folders.yaml | 增加/删除网易号时 |
| 爬虫脚本 | 核心程序：爬取+去重+导入 | wy_crawl_ima.py | 几乎不碰，除非需要改逻辑 |
| 去重基准 | 记录已导入文章的 ID，避免重复导入 | wy_crawl_results.json | 自动维护，无需手动干预 |
| 定时任务 | 每天自动运行一次 | .github/workflows/daily-import.yml | 修改运行时间或禁用时 |

## 文件结构

```
wy-media-crawler/
├── wy_crawl_ima.py               ← 核心：爬取+去重+导入一体脚本
├── sites_to_folders.yaml         ← 最重要的配置文件：40个网易号→ima文件夹映射
├── wy_crawl_results.json         ← 去重基准文件（自动维护，已导入 3025 篇）
├── .github/workflows/
│   └── daily-import.yml          ← 每日定时任务配置
├── README.md                     ← 项目入口文档
├── ONBOARDING.md                 ← 本文件：上手指南
└── MAINTENANCE.md                ← 维护手册
```

## 自动导入流程

```
定时触发（每日 14:00 UTC）
    ↓
读取 sites_to_folders.yaml，获取 40 个网易号的 TID 和 folder_id
    ↓
遍历每个网易号：
    ├─ 访问 https://www.163.com/dy/media/{TID}.html
    ├─ 解析 SSR 文章列表（无需 JS 渲染）
    ├─ 与 wy_crawl_results.json 比对，过滤已导入文章
    └─ 新文章 → 调用 ima import_urls API 导入（10 条/批）
    ↓
每批导入成功后，实时更新 wy_crawl_results.json
    ↓
git push 去重文件回仓库
```

## 日常操作

### 1. 手动触发一次导入（验证配置）

GitHub 仓库 → Actions → 每日网易文创导入 → Run workflow → 勾选 dry_run（仅爬取不导入）

### 2. 添加/删除网易号

编辑 sites_to_folders.yaml：

```yaml
# 格式：网易号名称: ima 文件夹 ID
新增网易号: "folder_xxx"
```

### 3. 查看运行状态

- GitHub 仓库 → Actions → 查看最近一次运行日志
- 检查 wy_crawl_results.json 大小变化，确认是否持续有新文章导入

### 4. 禁用自动运行

在 GitHub Variables 中设置 ENABLE_DAILY=false，或直接删除 .github/workflows/daily-import.yml

## 常见问题

**Q: 为什么有些文章没有导入？**
A: 可能原因：1) 文章已被去重文件记录（历史已导入）；2) 网易号 SSR 页面解析失败（检查 Actions 日志）；3) ima API 返回错误（检查 Secrets 配置是否正确）。

**Q: 如何判断导入是否成功？**
A: 检查 Actions 运行日志末尾是否有 "导入完成" 字样，以及 wy_crawl_results.json 中的文章数量是否增加。

**Q: 导入失败的文章会重试吗？**
A: 会。脚本对失败的批次进行精确重试（最多 2 次），仅重试失败的文章，不重试已成功的。

**Q: 如何查看当前已导入多少篇文章？**
A: 查看 wy_crawl_results.json 文件长度，或检查 Actions 日志中报告的导入数量。

**Q: 代码修改后如何生效？**
A: 推送到 main 分支后，下一次 Actions 运行会自动使用新代码。

## 技术栈

- 语言: Python 3
- 爬虫: urllib（纯标准库实现）
- 解析: BeautifulSoup
- API: ima Open API（import_urls 端点）
- 自动化: GitHub Actions
- 配置: YAML
- 去重: 基于文章 ID 的 JSON 文件

## 当前状态

- 监控网易号数: 40
- 已导入文章数: 3025+
- 自动运行频率: 每日 14:00 UTC（北京时间 22:00）
- 支持模式: dry_run（仅验证）/ 正常导入 双模式