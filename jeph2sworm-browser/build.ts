/**
 * Build configuration for the Jeph2Sworm Chrome extension.
 * Uses esbuild for fast bundling of TypeScript entry points.
 */

import { build, BuildOptions } from 'esbuild';

const isWatch = process.argv.includes('--watch');

const commonOptions: BuildOptions = {
  bundle: true,
  format: 'esm',
  target: 'chrome120',
  sourcemap: true,
  minify: !isWatch,
  outdir: 'dist',
  logLevel: 'info',
};

const entryPoints: Record<string, string> = {
  background: 'src/background.ts',
  content: 'src/content.ts',
  sidepanel: 'src/sidepanel.ts',
  'popup/popup': 'src/popup/popup.ts',
  'devtools/devtools': 'src/devtools/devtools.ts',
  'devtools/panel': 'src/devtools/panel.ts',
};

async function main(): Promise<void> {
  try {
    if (isWatch) {
      const ctx = await import('esbuild').then((e) =>
        e.context({ ...commonOptions, entryPoints })
      );
      await ctx.watch();
      console.log('Watching for changes...');
    } else {
      await build({ ...commonOptions, entryPoints });
      console.log('Build complete.');
    }
  } catch (err) {
    console.error('Build failed:', err);
    process.exit(1);
  }
}

main();
