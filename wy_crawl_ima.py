#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""网易文创资源矩阵 -> ima 知识库 增量爬虫 + 自动导入 (v3)

数据源: https://www.163.com/dy/media/{TID}.html (SSR 渲染文章列表)
知识库: WY 文创资源矩阵内容收录

v3 优化:
  1. 配置外置化: ACCOUNT_TIDS / FOLDERS 从 YAML 加载
  2. 精确重试: 仅失败项重试，而非整批重试
  3. 去重文件实时更新: 每批导入后立即写回
"""
import json, os, sys, time, re
import urllib.request, urllib.error

KB_ID = "ma1M4_yaAsSCqjoGYInjPvDI-vviZ9tbzJpVGu0wgn0="
BASE = "https://ima.qq.com/openapi/wiki/v1"
CLIENT_ID = os.environ.get("IMA_CLIENT_ID") or (open(os.path.expanduser("~/.config/ima/client_id")).read().strip() if os.path.exists(os.path.expanduser("~/.config/ima/client_id")) else "")
API_KEY = os.environ.get("IMA_API_KEY") or (open(os.path.expanduser("~/.config/ima/api_key")).read().strip() if os.path.exists(os.path.expanduser("~/.config/ima/api_key")) else "")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

RESULTS_FILE = os.environ.get("RESULTS_FILE", "wy_crawl_results.json")
LOG_FILE = os.environ.get("LOG_FILE", "wy_crawl.log")
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("true", "1", "yes")
YAML_PATH = os.environ.get("FOLDERS_YAML", "sites_to_folders.yaml")

# === 配置外置化：从 YAML 加载 ===
ACCOUNT_TIDS = {}
FOLDERS = {}


def load_config():
    global ACCOUNT_TIDS, FOLDERS
    if os.path.exists(YAML_PATH):
        try:
            import yaml
            with open(YAML_PATH, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            ACCOUNT_TIDS = data.get("accounts", {})
            FOLDERS = data.get("folders", {})
            log("已加载 %d 个账号TID, %d 个文件夹映射 (来自 %s)" % (len(ACCOUNT_TIDS), len(FOLDERS), YAML_PATH))
        except Exception as e:
            log("加载YAML失败: %s" % e)
    if not ACCOUNT_TIDS:
        # 兜底
        ACCOUNT_TIDS = {
            "网易哒哒": "T1417494430169", "网易王三三": "T1478229630669",
            "网易公开课": "T1477998124260", "城市漫游计划": "T1558002289275",
            "硬核看板": "T1557205557340", "网易数读": "T1558001296379",
            "网易健康": "T1420006426286", "网易设计": "T1374481988457",
            "网易财经": "T1428648190649", "网易时尚": "T1436757113402",
            "了不起的中国制造": "T1490002277117", "惊奇科技": "T1527579866938",
            "网易智能": "T1432538178516", "网易游戏频道": "T1501486360559",
            "网易艺术": "T1487692790259", "稿事编辑部": "T1504787811030",
            "态℃": "T1554807287299", "身体密码破译局": "T1520840296223",
            "北京买房人": "T1511169428677", "易眼看房": "T1502173973874",
            "娱乐FOCUS": "T1506586554886", "知否": "T1551963709658",
            "关爱买房公会": "T1491903303413", "后厂村7号": "T1554807366914",
            "网易海南房产": "T1446620866473", "严肃买房报告": "T1488966276089",
            "网易房产广州站": "T1460086635862", "科学大师": "T1554807186592",
            "网易声音图书馆": "T1487128297941", "地产申度": "T1487657364131",
            "网易谈心社": "T1500525259859", "网易浪潮工作室": "T1348654756909",
            "网易人间": "T1438840302520", "网易上流": "T1487769826746",
            "潮向Sense": "T1606112595383", "网易槽值": "T1438157774789",
            "看客": "T1387970173334", "网易娱乐": "T1571741465820",
            "网易号官方平台": "T1438163433635", "西北望看台": "T1555591682718",
        }
        log("使用内置默认账号TID (%d 个)" % len(ACCOUNT_TIDS))
    if not FOLDERS:
        FOLDERS = {
            "网易哒哒": "folder_7489865226676282", "网易王三三": "folder_7489865247645732",
            "网易公开课": "folder_7489865247649310", "城市漫游计划": "folder_7489865297980114",
            "硬核看板": "folder_7489865289590892", "网易数读": "folder_7489865293772471",
            "网易健康": "folder_7489865230869360", "网易设计": "folder_7493900432320702",
            "网易财经": "folder_7489865230869889", "网易时尚": "folder_7489865235066323",
            "了不起的中国制造": "folder_7489865260231470", "惊奇科技": "folder_7489865281189336",
            "网易智能": "folder_7489865235065254", "网易游戏频道": "folder_7489865268606597",
            "网易艺术": "folder_7489865256036205", "稿事编辑部": "folder_7489865272814420",
            "态℃": "folder_7489865285382444", "身体密码破译局": "folder_7489865281188178",
            "北京买房人": "folder_7493900449116164", "易眼看房": "folder_7489865268608786",
            "娱乐FOCUS": "folder_7489865272812579", "知否": "folder_7489865281187980",
            "关爱买房公会": "folder_7493900449117772", "后厂村7号": "folder_7489865289579339",
            "网易海南房产": "folder_7489865243441651", "严肃买房报告": "folder_7493900461678945",
            "网易房产广州站": "folder_7493900461700646", "科学大师": "folder_7489865285395596",
            "网易声音图书馆": "folder_7489865251830114", "地产申度": "folder_7489865251841925",
            "网易谈心社": "folder_7493903087335794", "网易浪潮工作室": "folder_7493903213143852",
            "网易人间": "folder_7493903221532833", "网易上流": "folder_7493903078924573",
            "潮向Sense": "folder_7493903229940584", "网易槽值": "folder_7493903070557593",
            "看客": "folder_7493903242526334", "网易娱乐": "folder_7493903594845174",
            "网易号官方平台": "folder_7493903653545107", "西北望看台": "folder_7493903674517328",
        }
        log("使用内置默认文件夹映射 (%d 个)" % len(FOLDERS))


# 通用正则 — 匹配所有频道域
ARTICLE_RE = re.compile(r'https?://www\.163\.com/([a-z0-9]+)/article/([A-Za-z0-9]+)\.html')


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def fetch_page(url, timeout=20, retries=3):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace"), r.status
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
            else:
                log("  fetch失败 %s: %s" % (url, e))
                return None, 0
    return None, 0


def extract_articles_from_media_page(html):
    """从 dy/media 页面 SSR HTML 提取文章链接列表 (去重)"""
    docs = {}
    for m in ARTICLE_RE.finditer(html or ""):
        channel, docid = m.group(1), m.group(2)
        if docid and docid not in docs:
            docs[docid] = "https://www.163.com/%s/article/%s.html" % (channel, docid)
    return [docs[d] for d in sorted(docs)]


def call_api(path, payload, timeout=120):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "ima-openapi-clientid": CLIENT_ID,
            "ima-openapi-apikey": API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:500]
        return {"code": e.code, "error": body}
    except Exception as e:
        return {"error": str(e)}


def import_urls_batch(folder_id, urls):
    """导入一批URL，返回 (成功列表, 失败列表, 是否API级失败)"""
    res = call_api("/import_urls", {
        "knowledge_base_id": KB_ID,
        "folder_id": folder_id,
        "urls": urls,
    }, timeout=120)
    ok_list = []
    fail_list = []
    if res.get("code") == 0:
        results = res.get("data", {}).get("results", {})
        for u in urls:
            r = results.get(u, {})
            if r.get("ret_code") == 0:
                ok_list.append(u)
            else:
                fail_list.append(u)
                log("  FAIL: %s -> %s" % (u, str(r)[:200]))
        return ok_list, fail_list, False
    else:
        log("  API失败: %s" % str(res)[:300])
        return [], urls, True


def load_existing_docs(results_file):
    """加载已有去重记录，返回 (docid_set, articles_list)"""
    docids = set()
    articles = []
    if os.path.exists(results_file):
        try:
            with open(results_file, encoding="utf-8") as f:
                data = json.load(f)
            for art in data.get("articles", []):
                url = art.get("url", "")
                m = re.search(r'/article/([A-Za-z0-9]+)\.html', url)
                if m:
                    docids.add(m.group(1))
                    articles.append(art)
            log("已加载 %d 个已有 docid (来自 %s)" % (len(docids), results_file))
        except Exception as e:
            log("加载已有结果失败: %s" % e)
    else:
        log("未找到 %s，将进行全量抓取" % results_file)
    return docids, articles


def save_results(results_file, articles):
    """保存/更新去重文件"""
    out = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(articles),
        "articles": articles,
    }
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def main():
    log("=" * 60)
    log("网易文创 -> ima 知识库 增量爬取 v3")
    label = " [DRY-RUN, 仅统计]" if DRY_RUN else ""
    log(label)
    log("知识库: %s" % KB_ID)
    log("去重文件: %s" % RESULTS_FILE)

    load_config()

    # 加载已有去重记录
    existing_docs, existing_articles = load_existing_docs(RESULTS_FILE)

    total_new = 0
    total_imported = 0
    total_failed = 0
    accounts_with_articles = 0
    accounts_failed = 0
    all_new_articles = []

    for account, tid in ACCOUNT_TIDS.items():
        folder_id = FOLDERS.get(account)
        if not folder_id:
            log("跳过 %s: 无 folder_id" % account)
            continue
        page_url = "https://www.163.com/dy/media/%s.html" % tid
        log("\n[%s] 抓取 %s" % (account, page_url))
        html, status = fetch_page(page_url)
        if not html:
            log("  抓取失败 (HTTP %s)" % status)
            accounts_failed += 1
            continue
        urls = extract_articles_from_media_page(html)
        # 去重过滤
        new_urls = []
        for u in urls:
            m = re.search(r'/article/([A-Za-z0-9]+)\.html', u)
            if not m:
                continue
            docid = m.group(1)
            if docid in existing_docs:
                continue
            new_urls.append(u)
            existing_docs.add(docid)
        log("  页面文章: %d, 新增: %d" % (len(urls), len(new_urls)))
        if new_urls:
            accounts_with_articles += 1
        total_new += len(new_urls)
        if not new_urls or DRY_RUN:
            if DRY_RUN and new_urls:
                log("  [DRY] 跳过导入，%d 篇待导入" % len(new_urls))
            continue
        # 分批导入 (10条/批) + 精确重试失败项
        batch_new_articles = []
        for i in range(0, len(new_urls), 10):
            batch = new_urls[i:i+10]
            ok_list, fail_list, api_failed = import_urls_batch(folder_id, batch)
            total_imported += len(ok_list)
            total_failed += len(fail_list)

            # 精确重试：仅失败项重试，最多重试2次
            if api_failed or fail_list:
                retry_urls = batch if api_failed else fail_list
                time.sleep(3)
                ok2, fail2, _ = import_urls_batch(folder_id, retry_urls)
                total_imported += len(ok2)
                total_failed += len(fail2)

            # 记录本次导入的 URL
            for u in batch:
                batch_new_articles.append({"url": u, "account": account, "source": "imported_%s" % time.strftime("%Y%m%d")})
            time.sleep(1.0)

        # 每账号处理完即更新去重文件
        if batch_new_articles:
            all_new_articles.extend(batch_new_articles)
            combined = existing_articles + all_new_articles
            seen_urls = set()
            dedup_combined = []
            for a in combined:
                if a["url"] in seen_urls:
                    continue
                seen_urls.add(a["url"])
                dedup_combined.append(a)
            save_results(RESULTS_FILE, dedup_combined)
            log("  去重文件已更新: %d 条" % len(dedup_combined))

    log("\n" + "=" * 60)
    if DRY_RUN:
        log("DRY-RUN 汇总: 账号 %d 个, 有新增 %d 个, 失败 %d 个" % (len(ACCOUNT_TIDS) - accounts_failed, accounts_with_articles, accounts_failed))
        log("待导入文章: %d 篇" % total_new)
    else:
        log("导入汇总: 账号 %d 个成功(%d 个有新增), 失败 %d 个" % (len(ACCOUNT_TIDS) - accounts_failed, accounts_with_articles, accounts_failed))
        log("新增文章: %d, 导入成功: %d, 失败: %d" % (total_new, total_imported, total_failed))
        log("去重文件: %s (%d 条)" % (RESULTS_FILE, len(existing_articles) + len(all_new_articles)))
    log("=" * 60)


if __name__ == "__main__":
    main()