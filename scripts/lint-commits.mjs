import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

function git(args) {
  const result = spawnSync("git", args, { encoding: "utf8" });
  if (result.status !== 0)
    throw new Error(result.stderr || "Falha ao consultar o histórico Git.");
  return result.stdout.trim();
}

function lint(args, input) {
  const result = spawnSync(
    process.execPath,
    [resolve("scripts/commitlint.mjs"), ...args],
    {
      input,
      stdio: [input === undefined ? "inherit" : "pipe", "inherit", "inherit"],
    },
  );
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}

const to = process.env.COMMIT_TO || "HEAD";
const from = process.env.COMMIT_FROM;
const baselinePath = resolve(".commitlint-baseline");
const baseline = existsSync(baselinePath)
  ? readFileSync(baselinePath, "utf8").trim()
  : "";
if (
  from &&
  /^[a-f0-9]{40,64}$/i.test(from) &&
  !/^0+$/.test(from) &&
  spawnSync("git", ["cat-file", "-e", `${from}^{commit}`]).status === 0
) {
  lint(["--from", from, "--to", to, "--verbose"]);
} else if (
  /^[a-f0-9]{40,64}$/i.test(baseline) &&
  spawnSync("git", ["merge-base", "--is-ancestor", baseline, to]).status === 0
) {
  // Preserve the pre-existing GitHub license commit; all project commits after it are validated.
  lint(["--from", baseline, "--to", to, "--verbose"]);
} else {
  // First push/new branch: include root commits as well as the remaining range.
  const roots = git(["rev-list", "--max-parents=0", to])
    .split("\n")
    .filter(Boolean);
  for (const root of roots)
    lint(["--verbose"], git(["show", "-s", "--format=%B", root]) + "\n");
  if (roots[0]) lint(["--from", roots[0], "--to", to, "--verbose"]);
}
