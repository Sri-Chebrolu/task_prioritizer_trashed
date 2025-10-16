const path = require('path');
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: path.join(__dirname, 'specs'),
  fullyParallel: false,
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  use: {
    baseURL: 'http://localhost:4173/frontend',
    headless: true,
  },
  webServer: {
    command: 'python -m http.server 4173',
    url: 'http://localhost:4173/frontend/index.html',
    reuseExistingServer: !process.env.CI,
    cwd: path.join(__dirname, '..', '..'),
    timeout: 60_000,
  },
});
