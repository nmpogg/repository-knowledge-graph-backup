import { describe, expect, it, vi } from 'vitest';

const constructors = vi.hoisted(() => ({ Queue: vi.fn(), Worker: vi.fn() }));

vi.mock('bullmq', async (importOriginal) => {
  const actual = await importOriginal<typeof import('bullmq')>();
  return { ...actual, Queue: constructors.Queue, Worker: constructors.Worker };
});

describe('module import', () => {
  it('does not construct a queue, worker, or Redis connection', async () => {
    await import('../src/index.js');
    expect(constructors.Queue).not.toHaveBeenCalled();
    expect(constructors.Worker).not.toHaveBeenCalled();
  });
});
