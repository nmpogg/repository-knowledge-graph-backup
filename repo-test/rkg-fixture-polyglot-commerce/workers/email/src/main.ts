import { pathToFileURL } from 'node:url';
import { bootstrap } from './index.js';
export async function main(): Promise<void> {
    const runtime = await bootstrap();
    const stop = () => { void runtime.close().catch(() => { process.exitCode = 1; }); };
    process.once('SIGINT', stop);
    process.once('SIGTERM', stop);
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    void main().catch(() => { console.error('email worker startup failed'); process.exitCode = 1; });
}
