# Cloudflare Worker CORS 反向代理

## 为什么需要此 Worker

Jev 官方接口服务器 (`https://api.typesafe.ai`) 默认未向跨域前端开放 CORS 允许标头（`Access-Control-Allow-Origin: *`）。
当本项目部署在 GitHub Pages（或其他独立静态前端域名）时，浏览器同源策略（SOP）会拦截前端发往官方接口的直接请求。

通过在 Cloudflare 免费部署一个轻量级 Worker 作为透明转发网关，在响应头中附加跨域放行标头，即可让纯前端页面直接与 Jev 接口通信，无需维护任何后端服务器。

Cloudflare 免费计划每日提供 100,000 次请求额度，对个人使用或开源体验完全免费且绰绰有余。

## 部署步骤（约 1 分钟）

1. 登录 [Cloudflare 控制台](https://dash.cloudflare.com/)。
2. 在左侧导航栏点击 **Compute (Workers) -> Workers & Pages**。
3. 点击 **Create application** -> **Create Worker**。
4. 给 Worker 命名（例如 `jev-proxy`），点击 **Deploy**。
5. 部署完成后，点击 **Edit code**。
6. 将 `worker.js` 中的全部代码复制并粘贴覆盖到编辑区中。
7. 点击右上角的 **Deploy**（保存并部署）。
8. 返回 Worker 详情页，复制 Worker 提供的分配域名（例如 `https://jev-proxy.your-name.workers.dev`）。
9. 打开 Jev Playground 前端网页，在右上角「设置 API Key」弹窗中，将该 Worker 完整 URL 粘贴到 **API 端点 (Base URL)** 输入框并保存即可。
