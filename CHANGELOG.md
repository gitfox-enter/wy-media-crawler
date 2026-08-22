# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v3] - 当前版本

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
