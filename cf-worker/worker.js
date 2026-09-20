/**
 * Cloudflare Worker: Jev System One CORS 反向代理
 * 部署说明:
 * 1. 登录 Cloudflare Dashboard -> Workers & Pages -> Create Worker
 * 2. 粘贴本文件全部代码并点击 Deploy
 * 3. 将生成的 Worker 域名 (如 https://jev-proxy.xxx.workers.dev) 填入 Jev Playground 前端设置中的 Base URL 即可
 */
export default {
  async fetch(request, env, ctx) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "*",
      "Access-Control-Max-Age": "86400"
    };

    // 处理跨域预检请求
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      const url = new URL(request.url);
      const targetUrl = `https://api.typesafe.ai${url.pathname}${url.search}`;

      const headers = new Headers(request.headers);
      headers.set("Host", "api.typesafe.ai");

      const init = {
        method: request.method,
        headers: headers,
        redirect: "follow"
      };
      if (request.method !== "GET" && request.method !== "HEAD") {
        init.body = request.body;
      }

      const proxyReq = new Request(targetUrl, init);

      const response = await fetch(proxyReq);
      const responseHeaders = new Headers(response.headers);
      
      // 附加跨域放行头
      for (const [k, v] of Object.entries(corsHeaders)) {
        responseHeaders.set(k, v);
      }

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 502,
        headers: {
          ...corsHeaders,
          "Content-Type": "application/json"
        }
      });
    }
  }
};
