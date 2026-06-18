# Daily Product Monitoring

亚马逊产品日常监控系统，包含**评论评分追踪**和**竞品多维监控**两大模块，支持浏览器指纹伪装、SQLite 持久化存储、HTML 邮件报告和 Excel 数据导出。

## 功能概览

### 评论评分追踪 (`review_tracker`)

每日自动抓取指定产品的评分和评论数，对比历史数据，生成 HTML 报告并通过邮件发送。

- 自动提取 ASIN、标题、星级评分、评论总数
- SQLite 存储每日快照，支持历史趋势对比
- 全内联样式 HTML 报告（兼容 QQ 邮箱 / Gmail）
- 反爬伪装：curl_cffi 浏览器指纹 + 随机间隔 + 指数退避

### 竞品多维监控 (`competitor_monitor`)

批量抓取多个 ASIN 的 10 项关键指标，输出符合运营习惯的 Excel 报表。

| 指标 | 说明 |
|------|------|
| 划线价 | List Price / Strike Price |
| 页面价 | 当前售价 |
| 活动 | 专享折扣 / 优惠券 / LD / BD |
| 评分 | 星级评分 |
| 评论数 | 总评论数量 |
| 排名 | 大类 / 小类 BSR |
| 变体数量 | 颜色/尺寸等变体 |
| 库存 | 库存状态 |
| 购物车卖家 | Buy Box 卖家信息 |
| 其他 | AC 标等附加信息 |

### 共用请求层 (`shared`)

基于 `curl_cffi` 的统一抓取层，支持多种浏览器 TLS 指纹伪装，自动检测验证码页面并触发冷却退避。

## 项目结构

```
Daily-Product-Monitoring/
├── shared/                          # 共用请求层
│   ├── __init__.py
│   └── fetcher.py                   # curl_cffi 浏览器指纹伪装 + 重试/退避
│
├── review_tracker/                  # 评论评分追踪模块
│   ├── config.yaml.example          # 配置文件模板
│   ├── tracker.py                   # 主入口：每日追踪
│   ├── scraper.py                   # 亚马逊页面抓取与解析
│   ├── storage.py                   # SQLite 存储
│   ├── reporter.py                  # HTML 报告生成
│   └── mailer.py                    # SMTP 邮件发送
│
├── competitor_monitor/              # 竞品监控模块
│   ├── config.yaml.example          # 配置文件模板
│   ├── __init__.py
│   ├── monitor.py                   # 主入口：批量监控
│   ├── scraper.py                   # 批量 ASIN 抓取
│   ├── excel_writer.py              # Excel（openpyxl）报表输出
│   └── extractors/                  # 各指标提取器
│       ├── __init__.py
│       ├── prices.py                # 划线价 / 页面价
│       ├── rank.py                  # BSR 排名
│       ├── rating.py                # 评分 & 评论数
│       ├── seller.py                # Buy Box 卖家
│       ├── inventory.py             # 库存状态
│       ├── category.py              # 类目路径
│       ├── bsr.py                   # Best Sellers Rank
│       ├── coupons.py               # 优惠券
│       ├── promotions.py            # 促销活动
│       ├── variations.py            # 变体
│       └── ac_and_tier.py           # Amazon's Choice & 价格带
│
├── debug_ac_rank.py                 # 调试脚本：测试 AC 标和 BSR 提取
├── requirements.txt                 # Python 依赖
├── .gitignore
└── README.md
```

## 快速开始

### 环境要求

- Python 3.10+
- Windows / macOS / Linux

### 安装

```bash
git clone https://github.com/383766159/Daily-Product-Monitoring.git
cd Daily-Product-Monitoring
pip install -r requirements.txt
```

### 配置

```bash
# 评论追踪配置
cp review_tracker/config.yaml.example review_tracker/config.yaml
# 编辑 config.yaml，填入邮箱 SMTP 信息和要追踪的产品链接

# 竞品监控配置
cp competitor_monitor/config.yaml.example competitor_monitor/config.yaml
# 编辑 config.yaml，填入要监控的 ASIN 列表
```

### 运行

```bash
# 评论评分追踪（每日抓取 + 报告 + 邮件）
python -m review_tracker.tracker

# 仅抓取和显示报告，不发送邮件
python -m review_tracker.tracker --dry-run

# 测试邮件发送
python -m review_tracker.tracker --test

# 竞品监控（生成 Excel）
python -m competitor_monitor.monitor

# 竞品监控 + 发送邮件
python -m competitor_monitor.monitor --email
```

## 依赖

| 库 | 用途 |
|----|------|
| `requests` | HTTP 基础请求 |
| `beautifulsoup4` | HTML 解析 |
| `lxml` | XML / HTML 快速解析器 |
| `curl_cffi` | TLS 浏览器指纹伪装 |
| `pyyaml` | 配置文件解析 |
| `openpyxl` | Excel 读写 |

## 注意事项

- **配置文件**: `config.yaml` 包含敏感信息（邮箱密码等），已被 `.gitignore` 排除。请从 `.example` 模板复制后自行填写。
- **请求频率**: 默认请求间隔 3-10 秒，避免触发亚马逊反爬机制。
- **反爬策略**: 当检测到验证码页面时，自动进入 10-20 秒冷却退避。
- **数据存储**: 评论追踪数据存储在 SQLite 数据库中（`review_tracker/data/tracker.db`），竞品监控输出为 Excel 文件（`competitor_monitor/outputs/`）。

## License

MIT
