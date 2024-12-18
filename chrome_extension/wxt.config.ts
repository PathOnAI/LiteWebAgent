import { defineConfig } from 'wxt';

// See https://wxt.dev/api/config.html
export default defineConfig({
  extensionApi: 'chrome',
  manifest: {
    name: 'LiteWebAgent Controller',
    permissions: [
      'activeTab',
      'sidePanel',
      'tabs',
    ],
    host_permissions: [
      'http://localhost:5001/*',
      'http://127.0.0.1:5001/*',
    ],
    action: {
      default_title: 'Open LiteAgent chat interface',
    },
    side_panel: {
      default_path: "sidepanel.html",
    },
    web_accessible_resources: [
      {
        resources: ['permission.html'],
        matches: ['*://*/*'],
      },
    ],
    content_scripts: [
      {
        js: ['/content-scripts/content.js'],
        matches: ['*://*/*'],
        run_at: 'document_idle',
      },
    ],
  },
  modules: ['@wxt-dev/module-react'],
  runner: {
    disabled: true,
  },
  build: {
    minify: false,
    },
});