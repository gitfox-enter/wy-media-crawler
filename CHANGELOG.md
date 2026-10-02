# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v4] - 当前版本

### Fixed

- 修复 网易艺术、潮向Sense 长期 0 导入：原正则只匹配新式图文 URL

### Changed

- ARTICLE_RE 扩展为三种 URL 格式：新式图文、老式图文（`{channel}.163.com/{yy}/{mmdd}/{hh}/{docid}.html`）、视频（`www.163.com/v/video/{vid}.html`）
- 去重提取统一改用 DOCID_RE，跨格式按 docid 去重

## [v3]

### Added

- 配置外置化：ACCOUNT_TIDS 和 FOLDERS 从 `sites_to_folders.yaml` 加载
- 精确重试：仅重试失败项，最多 2 次
- 实时去重更新：每批导入后立即写回 `wy_crawl_results.json`
- DRY_RUN 模式支持

## [v2]

### Added

- 引入 BeautifulSoup 解析
- 批量导入（10 条/批）

## [v1]

### Added

- 初始版本，基于 requests 和简单 URL 列表
