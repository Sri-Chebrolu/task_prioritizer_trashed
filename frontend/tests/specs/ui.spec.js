const { test, expect } = require('@playwright/test');

test.describe('PriorityOS UI', () => {
  test('captures a task via quick capture and schedules it', async ({ page }) => {
    await page.goto('/index.html');

    await expect(page.getByRole('heading', { level: 1, name: 'Today' })).toBeVisible();

    const taskStack = page.locator('[data-component="task-stack"] .task-card');
    const initialCount = await taskStack.count();

    await page.getByRole('button', { name: '+ Capture' }).click();

    const captureInput = page.locator('[data-capture="input"]');
    await expect(captureInput).toBeVisible();
    await captureInput.fill('Draft press release !8 #work @today');

    await page.getByRole('button', { name: 'Capture & schedule' }).click();

    const status = page.locator('[data-capture="status"]');
    await expect(status).toContainText('Task captured');

    await page.waitForTimeout(800);
    await expect(page.locator('.capture-modal')).toHaveAttribute('aria-hidden', 'true');

    await expect(taskStack).toHaveCount(initialCount + 1);
    await expect(taskStack.first().locator('.status-tag')).toBeVisible();
  });

  test('auto-schedules needs-scheduling tasks from the sidebar', async ({ page }) => {
    await page.goto('/index.html');

    const needsScheduling = page.locator('[data-component="needs-scheduling"] .unscheduled-task');
    const firstRow = needsScheduling.first();

    await expect(firstRow).toBeVisible();
    const taskName = await firstRow.locator('span').textContent();

    await firstRow.getByRole('button', { name: 'Auto-schedule' }).click();

    await expect(page.locator('[data-component="task-stack"] .task-card', { hasText: taskName.trim() })).toContainText('Scheduled');
  });
});
