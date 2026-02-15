# 瓣影寻踪 (Douban Scout)

一个现代化的 Web 应用，用于探索豆瓣电影和电视节目，配备强大的筛选和搜索功能。

## 功能特性

- **卡片网格视图**：精美的海报卡片，展示评分、类型和年份
- **多维筛选**：
  - 类型：全部 / 电影 / 电视节目
  - 评分范围：0-10 分，支持包含未评分作品
  - 年份范围：支持按上映年份区间筛选
  - 评分人数：支持设置最低评分人数阈值
  - 类型标签：支持多选（AND 逻辑）和排除（OR 逻辑）
  - 制片国家/地区：支持按国家或地区进行筛选
- **灵活排序**：支持按评分、评分人数、年份进行升序或降序排列
- **实时搜索**：支持标题实时搜索，内置防抖处理
- **无限滚动**：流畅的加载体验，自动加载下一页
- **深色模式**：支持浅色和深色主题切换
- **响应式设计**：完美适配移动端和桌面端，提供专门的移动端筛选抽屉
- **海报代理**：内置海报代理服务，支持多镜像回退，解决跨域及图片加载失败问题
- **数据导入**：支持从豆瓣备份 SQLite 文件运行时导入数据
- **接口限流**：内置灵活的限流机制，保护服务稳定性

## 快速开始

### 前置条件

- **Node.js**: v18 或更高版本
- **Python**: v3.11 或更高版本
- **uv**: 极速 Python 包管理器 ([安装指南](https://github.com/astral-sh/uv))

### 1. 启动后端

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 3. 访问应用

- **Web 界面**: [http://localhost:3000](http://localhost:3000)
- **API 文档**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 数据导入

本应用支持在运行时从豆瓣备份 SQLite 文件导入数据。

通过 API 提供豆瓣备份 SQLite 文件的绝对路径来触发导入：

```bash
curl -X POST http://localhost:8000/api/import \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"source_path": "/absolute/path/to/your/backup.sqlite3"}'
```

查看进度：

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/import/status
```

*注意：导入在后台运行。数据库中的现有数据将被替换。*

## 配置

后端行为可以通过环境变量进行自定义：

<!-- ENV_VARS_START -->

| 环境变量 | 默认值 | 描述 |
| -------- | ------ | ---- |
| `DATA_DIR` | `data` | 存储所有持久化数据的根目录, 包括 SQLite 数据库文件和海报图片缓存 |
| `POSTER_CACHE_TTL` | `365` | 本地海报图片的缓存有效期(天), 超过此天数后会尝试重新下载 |
| `IMPORT_API_KEY` | *无* | 调用数据导入 API 时必须在请求头中提供的 X-API-Key 密钥; 若未设置, 导入接口将被禁用 |
| `RATE_LIMIT_DEFAULT` | `100/minute` | 全局默认的接口访问速率限制, 适用于未单独配置限流的接口 |
| `RATE_LIMIT_SEARCH` | `30/minute` | 搜索标题、获取电影或电视节目列表等主要查询接口的访问速率限制 |
| `RATE_LIMIT_GENRES` | `20/minute` | 获取影视类型标签列表接口的访问速率限制 |
| `RATE_LIMIT_REGIONS` | `20/minute` | 获取影视地区标签列表接口的访问速率限制 |
| `RATE_LIMIT_STATS` | `10/minute` | 获取数据统计信息(如作品总数、年份分布等)接口的访问速率限制 |
| `RATE_LIMIT_POSTER` | `200/minute` | 海报图片代理服务接口的访问速率限制 |
| `RATE_LIMIT_IMPORT` | `5/minute` | 触发数据导入任务以及查询导入进度接口的访问速率限制 |

<!-- ENV_VARS_END -->

### 限流格式

限流字符串遵循 `[次数]/[时间周期]` 格式。示例：

- `10/minute` (每分钟 10 次)
- `500/hour` (每小时 500 次)
- `1/second` (每秒 1 次)

支持的时间周期：`second`, `minute`, `hour`, `day`, `month`, `year`。

## 许可

本项目采用 [MIT License](LICENSE) 许可。
