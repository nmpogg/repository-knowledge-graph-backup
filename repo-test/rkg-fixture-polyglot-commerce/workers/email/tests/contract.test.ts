import { readFileSync } from 'node:fs';
import { expect, it, vi } from 'vitest';
import { dispatchOrderEvent } from '../src/application/orderEvents.js';
it('accepts the shared Spring event envelope without a broker', async () => {
    const event = JSON.parse(readFileSync(new URL('../../../contracts/examples/order-event.json', import.meta.url), 'utf8'));
    const add = vi.fn().mockResolvedValue(undefined);
    await dispatchOrderEvent('orders.events', event, { add });
    expect(add).toHaveBeenCalledWith('send-order-email', { orderId: 'order-1', template: 'order-updated' }, expect.any(Object));
});
