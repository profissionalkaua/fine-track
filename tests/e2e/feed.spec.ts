import { test, expect } from '@playwright/test';

test('entra no workspace e filtra somente os vídeos carregados', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Email').fill('demo@pulso.local');
  await page.getByLabel('Senha', { exact: true }).fill('pulso-demo-local-2026');
  await page.getByRole('button', { name: 'Entrar no workspace' }).click();
  await expect(page.getByRole('heading', { name: 'Vídeos em alta', exact: true })).toBeVisible();
  await expect(page.locator('[data-video-card]')).toHaveCount(20);
  await page.getByLabel('Hashtag', { exact: true }).selectOption('receitas');
  await expect(page.locator('[data-video-card]')).toHaveCount(5);
  await expect(page.getByText('5 de 20 vídeos carregados')).toBeVisible();
  await expect(page.getByLabel('País', { exact: true }).locator('option')).toHaveCount(249);
});
