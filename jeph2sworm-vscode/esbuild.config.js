/**
 * esbuild configuration for the Jeph2Sworm VS Code extension.
 *
 * Bundles the extension host TypeScript into a single CJS file
 * compatible with the VS Code extension runtime.
 */

const esbuild = require("esbuild");

const isWatch = process.argv.includes("--watch");
const isProduction = process.argv.includes("--production");

/** @type {import('esbuild').BuildOptions} */
const buildOptions = {
  entryPoints: ["./src/extension.ts"],
  bundle: true,
  outfile: "dist/extension.js",
  external: ["vscode"],
  format: "cjs",
  platform: "node",
  target: "node18",
  sourcemap: !isProduction,
  minify: isProduction,
  treeShaking: true,
  logLevel: "info",
  // Mark all dependencies as external except ws (bundled)
  // vscode is always external
};

async function main() {
  try {
    if (isWatch) {
      const ctx = await esbuild.context(buildOptions);
      await ctx.watch();
      console.log("[esbuild] Watching for changes...");
    } else {
      await esbuild.build(buildOptions);
      console.log("[esbuild] Extension build complete.");
    }
  } catch (err) {
    console.error("[esbuild] Build failed:", err);
    process.exit(1);
  }
}

main();
