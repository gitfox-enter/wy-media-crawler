# 网易文创导入器 维护手册

> 面向维护者的技术文档，涵盖系统架构、工作流配置、故障排查与日常维护。

## 系统架构

### 核心设计原则

- **纯 GitHub Actions 运行**：不依赖任何服务器，所有代码在 GitHub Actions 运行环境中执行
- **配置外置化**：所有可变配置（网易号映射、ima 文件夹 ID）通过 YAML 管理，无需修改代码
- **去重驱动的增量导入**：基于 wy_crawl_results.json 记录已导入文章 ID，每次运行仅导入新文章
- **精确重试**：仅重试失败的批次，不重试已成功的文章

### 数据流

```
sites_to_folders.yaml  -> 读取配置
    |
wy_crawl_ima.py -> urllib 访问 163.com/dy/media/{TID}.html
    |
BeautifulSoup 解析 SSR 页面，提取文章列表
    |
wy_crawl_results.json <-> 比对去重，过滤已导入
    |
ima Open API (import_urls) -> 批量导入（10 条/批）
    |
实时更新 wy_crawl_results.json -> git push 回仓库
```

## 工作流配置

### daily-import.yml

位置: .github/workflows/daily-import.yml

触发方式:
- 定时触发: cron 0 14 * * *（每日 14:00 UTC = 北京时间 22:00）
- 手动触发: GitHub Actions -> Run workflow

手动触发参数:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| dry_run | boolean | false | 为 true 时仅爬取比对，不执行导入 |

运行步骤:
1. 检出代码
2. 设置 Python 3 环境
3. pip install requests beautifulsoup4 lxml
4. 运行 python wy_crawl_ima.py
5. 若非 dry_run 模式：git add wy_crawl_results.json -> git commit -> git push

环境变量:
| 变量 | 来源 | 说明 |
|------|------|------|
| IMA_CLIENT_ID | GitHub Secrets | ima Open API client_id |
| IMA_API_KEY | GitHub Secrets | ima Open API api_key |
| ENABLE_DAILY | GitHub Variables | 控制定时任务是否启用（默认 true） |

## 核心脚本说明

### wy_crawl_ima.py

版本: v3（SHA: 87d6f529fff23a6c2a0712e0678a11e2935a42b8）
大小: 13.8 KB

关键功能:

| 模块 | 说明 |
|------|------|
| 配置加载 | 从 sites_to_folders.yaml 读取 ACCOUNT_TIDS 和 FOLDERS |
| 爬虫引擎 | 纯 urllib 实现，访问 https://www.163.com/dy/media/{TID}.html（SSR 渲染） |
| 文章解析 | BeautifulSoup 解析 HTML，提取文章 URL、标题、发布时间 |
| 去重比对 | 读取 wy_crawl_results.json，过滤已存在的 article_id |
| 批量导入 | 按 10 条/批调用 ima import_urls API |
| 精确重试 | 失败项最多重试 2 次，仅重试失败的文章 |
| 实时去重更新 | 每批导入成功后立即写入 wy_crawl_results.json |
| DRY_RUN 模式 | 环境变量 DRY_RUN=true 时跳过导入和 git push |

## 站点映射配置

### sites_to_folders.yaml

位置: 仓库根目录
大小: 3.3 KB
映射数: 40 个网易号

格式:
```yaml
网易号名称: "folder_id_xxx"
```

注意：多个网易号可以映射到同一个 ima 文件夹。

## 去重文件

### wy_crawl_results.json

位置: 仓库根目录
大小: 约 467 KB（3025+ 篇文章记录）
格式: JSON 数组

维护策略:
- 自动维护：每批导入成功后脚本自动更新
- git push：工作流最后一步自动提交并推送回仓库
- 手动清理：如需重置，可删除文件后重新运行（会从头导入所有文章）

### 数据文件增长策略

> **wy_crawl_results.json 是项目核心数据文件，随每次运行自动增长，无需手动干预。**

- **增长预期**：以 40 个网易号每日约 80-200 篇新文章估算，文件年增量约 10-30 MB
- **Git 提交**：每次运行自动更新并提交，历史 commit 中保留完整记录
- **瘦身建议**：
  - 若不需历史记录，可定期压缩：删除旧文件 → 保留最新版 → 重新提交
  - 若文件过大（>5 MB），建议在 `.github/workflows/daily-import.yml` 中添加 `git filter-branch` 或定期归档
- **注意事项**：删除后重新运行会从头导入所有文章，可能导致 ima 知识库出现重复内容

## 故障排查

| 症状 | 可能原因 | 解决方法 |
|------|----------|----------|
| Actions 运行失败 | Secrets 未配置或配置错误 | 检查 IMA_CLIENT_ID 和 IMA_API_KEY 是否正确 |
| 爬取到 0 篇文章 | 网易号页面结构变更 | 运行 dry_run 检查返回的 HTML 结构 |
| 导入 API 返回 401 | ima API Key 过期 | 重新生成 API Key 并更新 Secrets |
| 大量文章导入失败 | 网易号 URL 格式变更 | 检查 https://www.163.com/dy/media/{TID}.html 是否可访问 |
| 去重文件未更新 | dry_run 模式未关闭 | 重新运行时不勾选 dry_run |
| git push 失败 | 远程仓库有冲突 | 手动拉取最新代码，解决冲突后重新运行 |

## 安全说明

- **纯 GitHub Actions 模式**：不依赖任何外部服务器
- **Secret 保护**：IMA_CLIENT_ID 和 IMA_API_KEY 存储在 GitHub Secrets 中，不可见
- **去重文件安全**：wy_crawl_results.json 仅包含文章 ID 和 URL，不包含敏感信息

## 维护清单

| 频率 | 任务 | 操作 |
|------|------|------|
| 每日 | 检查 Actions 运行状态 | 确认工作流是否正常完成 |
| 每周 | 检查去重文件增长 | 确认新文章持续导入中 |
| 每月 | 检查网易号活跃度 | 确认 40 个网易号是否持续更新 |
| 按需 | 添加/删除网易号 | 编辑 sites_to_folders.yaml |
| 按需 | 更新 Secrets | ima API Key 过期时更新 |
| 按需 | 清理去重文件 | 如需重新全量导入，删除 wy_crawl_results.json |

## 版本历史

### v3（当前）
- 配置外置化：ACCOUNT_TIDS 和 FOLDERS 从 YAML 加载
- 精确重试：仅重试失败项，最多 2 次
- 实时去重更新：每批导入后立即写回 wy_crawl_results.json
- DRY_RUN 模式支持

### v2
- 引入 BeautifulSoup 解析
- 批量导入（10 条/批）

### v1
- 初始版本，基于 requests 和简单 URL 列表

## 相关文档

- [README.md](README.md) — 项目入口文档
- [ONBOARDING.md](ONBOARDING.md) — 上手指南