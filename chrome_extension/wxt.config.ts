import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
  extensionApi: 'chrome',
  manifest: {
    name: 'LiteWebAgent Controller',
    permissions: [
      'activeTab',
      'tabs',
    ],
    host_permissions: [
      "http://localhost:5001/*",
      "http://127.0.0.1:5001/*"
    ],
  },
  modules: ['@wxt-dev/module-react'],
  runner: {
    disabled: true,
  },
});