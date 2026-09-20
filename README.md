# Jev Playground

TypeSafe AI Jev System One 决策模型能力评测与工作流演练台。

- 在线演示：[https://garonix.github.io/jev-playground/](https://garonix.github.io/jev-playground/)
- 测试用 Worker：`https://jev-proxy.zege.workers.dev/`（支持浏览器跨域）
- 官方原始端点：`https://api.typesafe.ai`
- 社区讨论：本项目首发并分享于 [LINUX DO 社区](https://linux.do) — 欢迎前往社区交流讨论与提出改进建议！

---

## 案例矩阵

| 案例 | 官方参考 | 架构模式 | 原语组合 | 核心验证能力 |
| :--- | :--- | :--- | :--- | :--- |
| **智能家居助手** | [Smart Home](https://docs.typesafe.ai/demos/smart-home) | 推测性展开与级联路由 | Choice, Noul | ~100ms 内并行完成分类与设备动作，非控制指令平滑转接大模型 |
| **LLM 实时安全护栏** | [LLM Guardrails](https://docs.typesafe.ai/cookbooks/llm_guardrails) | 危害检测与严重度门控 | Noul (4 项), Score | 替代高延迟串行防护，依据置信度实现放行、人工审核与立即阻断 |
| **工单智能分流** | [Building with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one) | 复合对象解析与多维打分 | Choice, Noul, Score | 跨字段比对防钓鱼仿冒，结合客户等级与怒气指数触发升级 |
| **金融量化函数调用** | [Function Calling](https://docs.typesafe.ai/cookbooks/function_calling) | 强类型参数绑定 | Choice, Noul | 避免大模型 JSON Schema 解析幻觉，100% 映射闭集枚举参数 |
| **RAG 引用真实性核查** | [Citation Check](https://docs.typesafe.ai/cookbooks/citation_check) | 语义级事实比对 | Choice, Score | 检测检索文档与生成回答之间的语义冲突、无源生成与幻觉 |
| **自由实验台** | - | 自由探索模式 | 自由组合原语 | 任意定义输入状态与分类/评分规则，探索模型能力边界 |

---

## 核心特性

- **双模架构兼容**：
  - **纯静态运行**：基于 Vue 3、Tailwind CSS 与原生 ES Modules 构建，零打包步骤，100% 静态部署到 GitHub Pages。
  - **本地极简后端**：基于 FastAPI 与 httpx 提供本地代理服务，免去跨域配置，一键直连官方接口。
- **白绿极简设计系统**：采用 Emerald 翡翠绿与纯白微阴影，适配 16:9 桌面视口一屏展示（三大区块等高吸顶吸底，无页面级外层滚动条）。
- **逐级展开双模编辑器 (State & Questions)**：
  - **State 块视图**：支持深层嵌套复合对象与多维数组的逐级展开、层级发丝导轨线、动态子项增删、类型自由切换与任意层级折叠收起。
  - **Questions 块视图**：可视化定义 Choice 选项、Score 档位及 Noul 判定条件。
  - **JSON 代码视图**：支持格式化与实时语法校验，双模数据 100% 双向无损互通。
  - **状态防护**：支持多步撤销 (Undo)、修改状态重置及输入字符上限约束。
- **决策归因引擎 (Decision Attribution)**：基于浏览器原生 `Intl.Segmenter` API 实现微秒级中英文分词与反事实消融计算，提供显著性热力流、置信度浮动与 Top 贡献排行。
- **离线模拟模式 (Mock Mode)**：内置离线模拟响应引擎。在 API 设置中输入 `mock` 即可无凭据完整体验全部案例流转与归因分析。

---

## 运行方式

### 方式一：在线体验 (GitHub Pages)

无需安装任何环境，直接访问在线演示地址：

- 访问地址：[https://garonix.github.io/jev-playground/](https://garonix.github.io/jev-playground/)
- API 端点：填入测试用 Worker 地址 `https://jev-proxy.zege.workers.dev/` 或自建 Cloudflare Worker。
- API Key：填入您的 TypeSafe API Key（或填入 `mock` 体验离线模拟）。

### 方式二：本地简易后端运行（推荐，免配置官方直连）

如果不想配置 Cloudflare Worker，直接在本地启动简易后端。服务内置透明反向代理，自动附加 CORS 标头并转发至官方接口 `https://api.typesafe.ai`，彻底解决浏览器跨域问题。

本项目使用 `uv` 管理依赖与环境：

```bash
# 1. 启动服务（uv 自动解析依赖并运行）
uv run python main.py

# 或使用 uvicorn 直接启动
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后在浏览器打开 `http://localhost:8000`。点击右上角设置，在 API 端点点击「本地后端」（`http://127.0.0.1:8000`），填入 API Key 即可直连官方。

### 方式三：本地纯静态服务器运行

```bash
# 使用 Python 标准库
python3 -m http.server 8000

# 或使用 Node.js
npx serve .
```

访问 `http://localhost:8000`。此模式下连接官方接口需配置 CORS 代理或填入 `mock` 进行离线模拟。

---

## 部署与云端代理

### GitHub Pages 自建部署

1. Fork 或推送本项目代码至您的 GitHub 仓库。
2. 在仓库进入 **Settings -> Pages**。
3. **Build and deployment -> Source** 选择 **Deploy from a branch**。
4. Branch 选择 `main`，目录选择 `/ (root)` 并保存，即可获得专属在线工作台。

### Cloudflare Worker CORS 代理（可选）

Jev 官方接口 (`https://api.typesafe.ai`) 默认未向跨域前端开放 CORS 标头。若通过第三方静态网站直接调用，可参考 [Cloudflare Worker 代理指南](cf-worker/README.md) 部署免费代理（每日 100,000 次免费额度）。

---

## 项目结构

```text
├── index.html              # 主界面入口 (GitHub Pages / 本地前端)
├── static/                 # 前端核心资源
│   ├── app.js              # Vue 3 控制器与状态机
│   ├── cases.js            # 5 大核心案例定义与中英工作流
│   ├── i18n.js             # 响应式国际化字典与翻译引擎
│   ├── jev-client.js       # Jev API 客户端与离线模拟引擎
│   └── attribution.js      # 基于 Intl.Segmenter 的纯前端决策归因引擎
├── app/                    # 本地 Python 后端与透明代理
│   ├── main.py             # FastAPI 服务入口与透明反向代理 (/v1, /api/proxy)
│   ├── cases/              # 案例定义
│   ├── jev_client.py       # TypeSafe SDK 调用封装
│   └── attribution.py      # 后端归因算法
├── cf-worker/              # Cloudflare Worker 代理配置
│   ├── worker.js           # 极简 CORS 代理脚本
│   └── README.md           # 部署说明
├── main.py                 # 本地一键启动入口
├── pyproject.toml          # 项目配置与依赖管理 (uv)
└── run.sh                  # 启动脚本
```

---

## 社区与交流

本项目首发并分享于 [LINUX DO 社区](https://linux.do) — 欢迎前往社区交流讨论与提出改进建议！

