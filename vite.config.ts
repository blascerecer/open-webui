import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';

/** @type {import('vite').Plugin} */
const corsPlugin = {
  name: 'cors-plugin',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      // Instead of wildcard, specify the exact origin
      res.setHeader('Access-Control-Allow-Origin', 'http://localhost:5173');
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      res.setHeader('Access-Control-Allow-Credentials', 'true');
      res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
      res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
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