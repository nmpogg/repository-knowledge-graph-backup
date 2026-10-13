class Queue {
    add(name: string): string { return `local:${name}`; }
}
class Worker {
    constructor(readonly label: string) { }
}
// Expected: local Queue/Worker bindings must not create BullMQ technology or message edges.
export function useShadowedBindings(): string {
    const queue = new Queue();
    const worker = new Worker('local-worker');
    return `${queue.add('local-job')}:${worker.label}`;
}
