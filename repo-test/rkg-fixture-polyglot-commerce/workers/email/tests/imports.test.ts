import { expect, it, vi } from 'vitest';
const connections = vi.hoisted(() => ({ queue: vi.fn(), worker: vi.fn() }));
vi.mock('bullmq', () => ({ Queue: connections.queue, Worker: connections.worker }));
it('importing bootstrap and entrypoint creates no connection or long-running loop', async () => {
    await import('../src/index.js');
    await import('../src/main.js');
    expect(connections.queue).not.toHaveBeenCalled();
    expect(connections.worker).not.toHaveBeenCalled();
});
