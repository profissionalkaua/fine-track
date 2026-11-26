import { existsSync } from "node:fs";

// Production images and CI do not need Git hooks or development dependencies.
if (
  process.env.NODE_ENV !== "production" &&
  process.env.CI !== "true" &&
  process.env.HUSKY !== "0" &&
  existsSync(".git")
) {
  const husky = (await import("husky")).default;
  const error = husky();
  if (error) {
    console.error(error);
    process.exitCode = 1;
  }
}
