// Expected: emit a diagnostic; do not infer an internal import edge for a runtime-computed target.
export async function loadOptionalModule(moduleName: string): Promise<unknown> {
  return import(/* @vite-ignore */ moduleName);
}
