import { test, expect, type BrowserContext } from "@playwright/test";
let sessionCookies: Awaited<ReturnType<BrowserContext["cookies"]>> | null =
  null;

test.beforeEach(async ({ page, context }) => {
  if (sessionCookies) {
    await context.addCookies(sessionCookies);
    await page.goto("/");
  } else {
    await page.goto("/");
    await page.getByLabel("Email").fill("demo@pulso.local");
    await page
      .getByLabel("Senha", { exact: true })
      .fill("pulso-demo-local-2026");
    await page.getByRole("button", { name: "Entrar no workspace" }).click();
  }
  await expect(
    page.getByRole("heading", { name: "Vídeos em alta", exact: true }),
  ).toBeVisible();
  if (!sessionCookies) sessionCookies = await context.cookies();
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
    page.getByRole("tabpanel", { name: "Análise visual", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(open).toBeFocused();
});

test("reabrir vídeo recupera a execução disponível sem iniciar outra", async ({
  page,
}) => {
  await page.getByLabel("País", { exact: true }).selectOption("BR");
  const open = page
    .locator("[data-video-card]")
    .first()
    .getByRole("button", { name: "Ideias e roteiros" });
  const lookup = page.waitForResponse(
    (response) =>
      response.url().includes("/runs/available?") && response.status() === 200,
  );
  const opened = page
    .waitForResponse(
      (response) =>
        response.url().endsWith("/runs/video/open") &&
        response.status() === 202,
    )
    .catch(() => null);
  await open.click();
  const available = (await (await lookup).json()).run;
  if (!available) {
    expect(await opened).not.toBeNull();
  }
  await page.keyboard.press("Escape");
  let creations = 0;
  page.on("request", (request) => {
    if (
      request.method() === "POST" &&
      /\/v1\/runs(?:\/video\/open)?$/.test(request.url())
    )
      creations++;
  });
  const recovered = page.waitForResponse(
    (response) =>
      response.url().includes("/runs/available?") && response.status() === 200,
  );
  await open.click();
  expect((await (await recovered).json()).run).not.toBeNull();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(creations).toBe(0);
});

test("trocar workspace reinicia perfis e bloqueia rascunhos antigos durante a carga", async ({
  page,
}) => {
  const options = await page
    .getByRole("combobox", { name: "Workspace ativo", exact: true })
    .locator("option")
    .evaluateAll((nodes) =>
      nodes.map((n) => ({ id: (n as HTMLOptionElement).value })),
    );
  const current = await page
    .getByRole("combobox", { name: "Workspace ativo", exact: true })
    .inputValue();
  const target = options.find((option) => option.id !== current)!.id;
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Criadores", exact: true })
    .click();
  const handle = `isolado_${Date.now().toString(36)}`;
  await page.getByLabel("Usuário ou URL do TikTok").fill(`@${handle}`);
  await page
    .getByRole("button", { name: "Adicionar perfil", exact: true })
    .click();
  await expect(
    page.locator("[data-creator]").filter({ hasText: handle }),
  ).toBeVisible();
  const refreshed = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/creators") &&
      r.request().method() === "GET" &&
      r.request().headers()["x-workspace-id"] === target,
    { timeout: 2000 },
  );
  await page
    .getByRole("combobox", { name: "Workspace ativo", exact: true })
    .selectOption(target);
  await refreshed;
  await expect(
    page.locator("[data-creator]").filter({ hasText: handle }),
  ).toHaveCount(0);
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "Regras da marca" })
    .click();
  await page
    .getByLabel("Categoria (opcional)")
    .fill("Rascunho do outro workspace");
  let release!: () => void;
  const barrier = new Promise<void>((resolve) => (release = resolve));
  let entered!: () => void;
  const requested = new Promise<void>((resolve) => (entered = resolve));
  await page.route("**/api/v1/brand-rules", async (route) => {
    if (route.request().method() === "GET") {
      entered();
      await barrier;
    }
    await route.continue();
  });
  await page
    .getByRole("combobox", { name: "Workspace ativo", exact: true })
    .selectOption(current);
  await requested;
  try {
    await expect(page.getByLabel("Categoria (opcional)")).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Salvar regras" }),
    ).toHaveCount(0);
  } finally {
    release();
  }
  await expect(page.getByLabel("Categoria (opcional)")).not.toHaveValue(
    "Rascunho do outro workspace",
  );
});

test("resposta de paginação antiga não retorna após trocar o país", async ({
  page,
}) => {
  let release!: () => void;
  const barrier = new Promise<void>((resolve) => (release = resolve));
  let entered!: () => void;
  const held = new Promise<void>((resolve) => (entered = resolve));
  await page.route("**/api/v1/top-videos?**", async (route) => {
    if (new URL(route.request().url()).searchParams.has("cursor")) {
      const response = await route.fetch();
      entered();
      await barrier;
      await route.fulfill({ response }).catch(() => {});
    } else await route.continue();
  });
  await page.getByRole("button", { name: "Carregar mais vídeos" }).click();
  await held;
  await page.getByLabel("País", { exact: true }).selectOption("PT");
  await expect(
    page.getByRole("heading", { name: "A fonte ainda está indisponível" }),
  ).toBeVisible();
  release();
  await page.waitForLoadState("networkidle");
  await expect(page.getByLabel("País", { exact: true })).toHaveValue("PT");
  await expect(page.locator("[data-video-card]")).toHaveCount(0);
  await page.getByRole("button", { name: "Limpar filtros" }).click();
  await expect(page.locator("[data-video-card]")).toHaveCount(20);
});
