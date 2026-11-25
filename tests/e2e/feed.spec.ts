import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Email").fill("demo@pulso.local");
  await page.getByLabel("Senha", { exact: true }).fill("pulso-demo-local-2026");
  await page.getByRole("button", { name: "Entrar no workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Vídeos em alta", exact: true }),
  ).toBeVisible();
});

test("entra no workspace e filtra somente os vídeos carregados", async ({
  page,
}) => {
  await expect(
    page.getByRole("heading", { name: "Vídeos em alta", exact: true }),
  ).toBeVisible();
  await expect(page.locator("[data-video-card]")).toHaveCount(20);
  await page.getByLabel("Hashtag", { exact: true }).selectOption("receitas");
  await expect(page.locator("[data-video-card]")).toHaveCount(5);
  await expect(page.getByText("5 de 20 vídeos carregados")).toBeVisible();
  await expect(
    page.getByLabel("País", { exact: true }).locator("option"),
  ).toHaveCount(249);
});

test("preserva o rascunho da marca ao navegar e permite descartar", async ({
  page,
}) => {
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Regras da marca" })
    .click();
  await page.getByLabel("Categoria (opcional)").fill("Cerâmica autoral");
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Vídeos em alta" })
    .click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Regras da marca" })
    .click();
  await expect(page.getByLabel("Categoria (opcional)")).toHaveValue(
    "Cerâmica autoral",
  );
  await expect(
    page.getByText("Alterações não salvas", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Descartar alterações" }).click();
  await expect(page.getByLabel("Categoria (opcional)")).toHaveValue("");
});

test("remove e desfaz uma referência pendente sem exigir nova busca", async ({
  page,
}) => {
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Criadores", exact: true })
    .click();
  const handle = `teste_${Date.now().toString(36)}`;
  await page.getByLabel("Usuário ou URL do TikTok").fill(`@${handle}`);
  await page
    .getByRole("button", { name: "Adicionar perfil", exact: true })
    .click();
  const profile = page
    .locator("[data-creator]")
    .filter({ hasText: `@${handle}` });
  await expect(profile).toBeVisible();
  await profile.getByRole("button", { name: "Remover" }).click();
  await expect(profile).toHaveCount(0);
  await page.getByRole("button", { name: "Desfazer", exact: true }).click();
  await expect(profile).toBeVisible();
});

test("inicia análise com recorte congelado e permite cancelar", async ({
  page,
}) => {
  await page
    .getByRole("button", { name: "Analisar recorte", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Configuração da análise" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Iniciar análise", exact: true })
    .click();
  await expect(
    page.getByText("Recorte congelado", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancelar execução" }).click();
  await expect(
    page.getByText("Execução cancelada", { exact: true }),
  ).toBeVisible();
});

test("janela individual tem duas abas, fecha com Escape e devolve foco", async ({
  page,
}) => {
  const open = page
    .locator("[data-video-card]")
    .first()
    .getByRole("button", { name: "Ideias e roteiros" });
  await open.click();
  await expect(
    page.getByRole("tab", { name: "Roteiro", exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Análise visual" }).click();
  await expect(
    page.getByText("Mídia autorizada não disponível", { exact: false }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(open).toBeFocused();
});
