const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api/nvidia',
    createProxyMiddleware({
      target: 'https://integrate.api.nvidia.com',
      changeOrigin: true,
      pathRewrite: {
        '^/api/nvidia': '', // remove /api/nvidia from the beginning of the path
      },
      onProxyRes: function (proxyRes, req, res) {
        proxyRes.headers['Access-Control-Allow-Origin'] = '*';
      },
    })
  );
};
