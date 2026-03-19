const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy for NVIDIA NIM API
  app.use(
    '/api/nvidia',
    createProxyMiddleware({
      target: 'https://integrate.api.nvidia.com',
      changeOrigin: true,
      pathRewrite: {
        '^/api/nvidia': '',
      },
      onProxyRes: function (proxyRes, req, res) {
        proxyRes.headers['Access-Control-Allow-Origin'] = '*';
      },
    })
  );

  // Proxy for Judge0 Code Execution (Java)
  app.use(
    '/api/judge0',
    createProxyMiddleware({
      target: 'https://ce.judge0.com',
      changeOrigin: true,
      pathRewrite: {
        '^/api/judge0': '', // This will map /api/judge0/XXX to ce.judge0.com/XXX
      },
      onProxyRes: function (proxyRes, req, res) {
        proxyRes.headers['Access-Control-Allow-Origin'] = '*';
      },
    })
  );
};
