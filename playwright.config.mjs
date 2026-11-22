import { defineConfig } from '@playwright/test';

const port = 8051;
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: './qa',
  testMatch: '*.spec.mjs',
  reporter: 'list',
  use: {
    baseURL,
    browserName: 'chromium',
    reducedMotion: 'reduce',
    launchOptions: { executablePath: process.env.CHROMIUM_BINARY }
  },
  webServer: {
    command: `python3 -m http.server ${port} --bind 127.0.0.1 --directory dist`,
    stderr: 'ignore',
    url: baseURL
  }
});
