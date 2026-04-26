import { chromium } from '../../../frontend/node_modules/playwright/index.mjs';
import { writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const artifactDir = process.argv[2];
const appUrl = 'http://127.0.0.1:4173/dist-react/index.html?apiBase=http://127.0.0.1:8100#/login';
const unique = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);
const username = `smoke_user_${unique}`;
const password = 'SmokePass123!';
const adminPassword = 'admin-secret';

await mkdir(artifactDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
const page = await context.newPage();

const result = {
  appUrl,
  username,
  created: false,
  reloadedLookupPassed: false,
  screenshots: {
    modal: 'create-modal.png',
    success: 'create-success.png',
    reloaded: 'create-reloaded-search.png',
  },
  timestamps: {
    startedAt: new Date().toISOString(),
  },
};

try {
  await page.goto(appUrl, { waitUntil: 'networkidle' });
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill(adminPassword);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL(/#\/dashboard$/);

  await page.goto('http://127.0.0.1:4173/dist-react/index.html?apiBase=http://127.0.0.1:8100#/users', { waitUntil: 'networkidle' });
  await page.locator('h2.ant-typography').filter({ hasText: 'Users' }).waitFor();

  await page.getByRole('button', { name: 'Create user' }).first().click();
  const createDialog = page.getByRole('dialog', { name: 'Create user' });
  await createDialog.getByLabel('Username').fill(username);
  await createDialog.getByLabel('Initial password').fill(password);
  await createDialog.getByLabel('Display name').fill('Smoke User');
  await createDialog.getByLabel('Email').fill(`${username}@example.com`);
  await createDialog.getByLabel('Tenant ID').fill('tenant_smoke');
  await createDialog.getByLabel('Entitlements (comma or newline separated)').fill('dashboard:view, publish:run');
  await page.screenshot({ path: join(artifactDir, 'create-modal.png'), fullPage: true });

  await createDialog.getByRole('button', { name: 'Create user' }).click();
  await page.getByText('Confirm password: Create user').waitFor();
  await page.getByPlaceholder('Enter your password').fill(adminPassword);
  await page.getByRole('button', { name: 'Confirm and continue' }).click();

  await page.getByText('User created. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  await page.getByText(username).first().waitFor({ timeout: 20000 });
  await page.getByText('Smoke User').first().waitFor({ timeout: 20000 });
  result.created = true;
  await page.screenshot({ path: join(artifactDir, 'create-success.png'), fullPage: true });

  await page.reload({ waitUntil: 'networkidle' });
  await page.locator('h2.ant-typography').filter({ hasText: 'Users' }).waitFor();
  const searchInput = page.getByPlaceholder('alice / alice@example.com / u_1');
  await searchInput.fill(username);
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await page.getByText(username).first().waitFor({ timeout: 20000 });
  result.reloadedLookupPassed = true;
  await page.screenshot({ path: join(artifactDir, 'create-reloaded-search.png'), fullPage: true });

  result.timestamps.finishedAt = new Date().toISOString();
  await writeFile(join(artifactDir, 'result.json'), JSON.stringify(result, null, 2), 'utf8');
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  result.timestamps.failedAt = new Date().toISOString();
  result.error = {
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : null,
  };
  await writeFile(join(artifactDir, 'result.json'), JSON.stringify(result, null, 2), 'utf8');
  console.error(JSON.stringify(result, null, 2));
  process.exitCode = 1;
} finally {
  await context.close();
  await browser.close();
}


