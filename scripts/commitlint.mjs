import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

// Use the project's Node runtime, including when Git is launched from an IDE.
const localNode = resolve(
  `node_modules/node/bin/node${process.platform === "win32" ? ".exe" : ""}`,
);
const child = spawn(
  existsSync(localNode) ? localNode : process.execPath,
  [resolve("node_modules/@commitlint/cli/cli.js"), ...process.argv.slice(2)],
  { stdio: "inherit" },
);
child.on("error", (error) => {
  console.error(error.message);
  process.exitCode = 1;
});
child.on("exit", (code) => {
  process.exitCode = code ?? 1;
});
