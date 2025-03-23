import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';

/** @type {import('vite').Plugin} */
const corsPlugin = {
  name: 'cors-plugin',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      // Allow requests from any origin in development mode
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      
      // Note: When using wildcard '*' for origins, credentials cannot be true
      // If you need credentials, you'll need to specify exact origins
      
      // Handle preflight OPTIONS requests
      if (req.method === 'OPTIONS') {
        res.statusCode = 204;
        res.end();
        return;
      }
      
      next();
    });
  }
};

export default defineConfig({
  plugins: [
    sveltekit(),
    corsPlugin, // Add the CORS plugin
    viteStaticCopy({
      targets: [
        {
          src: 'node_modules/onnxruntime-web/dist/*.jsep.*',
          dest: 'wasm'
        }
      ]
    })
  ],
  define: {
    APP_VERSION: JSON.stringify(process.env.npm_package_version),
    APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build')
  },
  build: {
    sourcemap: true
  },
  worker: {
    format: 'es'
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: 'localhost',
        ws: true,
        xfwd: true,
        // Most important for credentials
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Proxying request:', req.method, req.url, '→', proxyReq.path);
          });
          // This is crucial for cookies/credentials
          proxy.options.cookieDomainRewrite = 'localhost';
          proxy.options.preserveHeaderKeyCase = true;
          proxy.options.selfHandleResponse = false;
        }
      },
      // Add a proxy for the specific mcp.run endpoint
      '/mcp-api': {
        target: 'https://www.mcp.run',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/mcp-api/, '/api'),
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('MCP Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Proxying MCP request:', req.method, req.url, '→', proxyReq.path);
          });
        }
      },
      '/smithery-api/registry': {
        target: 'https://registry.smithery.ai',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/smithery-api\/registry/, ''),
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Proxy error:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Proxying request:', req.method, req.url, '→', proxyReq.path);
          });
        }
      }
    }
  }
});