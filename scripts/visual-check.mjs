import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir, writeFile } from "node:fs/promises";

await mkdir(".runtime/screenshots", { recursive: true });
const browser = await chromium.launch();
const reports = [];
for (const [name, width, height] of [
  ["desktop", 1440, 1000],
  ["mobile", 390, 844],
]) {
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3000");
  await page.getByLabel("Email").fill("demo@pulso.local");
  await page.getByLabel("Senha", { exact: true }).fill("pulso-demo-local-2026");
  await page.getByRole("button", { name: "Entrar no workspace" }).click();
  await page.locator("[data-video-card]").first().waitFor();
  for (const [area, label] of [
    ["feed", "VÃ­deos em alta"],
    ["creators", "Criadores"],
    ["brand", "Regras da marca"],
    ["analysis", "Gerar ideias"],
  ]) {
    if (area !== "feed")
      await page
        .getByRole("navigation")
        .getByRole("button", { name: label, exact: true })
        .click();
    await page.waitForTimeout(300);
    await page.screenshot({ path: `.runtime/screenshots/${name}-${area}.png` });
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    );
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    reports.push({
      viewport: name,
      area,
      overflow,
      violations: result.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        count: v.nodes.length,
        examples: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
        })),
      })),
    });
  }
  await context.close();
}
await browser.close();
await writeFile(
  ".runtime/accessibility.json",
  JSON.stringify(reports, null, 2),
);
for (const report of reports) console.log(JSON.stringify(report));
if (
  reports.some(
    (r) =>
      r.overflow ||
      r.violations.some((v) => ["serious", "critical"].includes(v.impact)),
  )
)
  process.exitCode = 1;
