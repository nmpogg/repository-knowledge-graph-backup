import { describe, expect, it, vi } from 'vitest';
import { dispatchOrderEvent } from '../src/application/orderEvents.js';
import { processEmailJob } from '../src/workers/emailWorker.js';
import { EmailService } from '../src/services/emailService.js';
const event = { type: 'order.updated' as const, order_id: 'order-1', status: 'CREATED', occurred_at: '2026-10-05T10:00:00Z' };
describe('event to email flow without Redis or SMTP', () => {
    it('enqueues the order and delegates the job to the email service', async () => {
        const add = vi.fn().mockResolvedValue(undefined);
        await dispatchOrderEvent('orders.events', event, { add });
        expect(add).toHaveBeenCalledWith('send-order-email', { orderId: 'order-1', template: 'order-updated' }, expect.any(Object));
        const sendOrderEmail = vi.fn().mockResolvedValue(undefined);
        const call = add.mock.calls[0];
        if (!call)
            throw new Error('Queue was not invoked');
        await processEmailJob({ data: call[1] }, { sendOrderEmail });
        expect(sendOrderEmail).toHaveBeenCalledWith({ orderId: 'order-1', template: 'order-updated' });
    });
    it('does not enqueue unknown topics or malformed events', async () => {
        const add = vi.fn();
        await expect(dispatchOrderEvent('dynamic.events', event, { add })).rejects.toThrow('Unsupported');
        await expect(dispatchOrderEvent('orders.events', { ...event, order_id: '' }, { add })).rejects.toThrow('Invalid');
        expect(add).not.toHaveBeenCalled();
    });
    it('does not swallow queue or service failures', async () => {
        await expect(dispatchOrderEvent('orders.events', event, { add: vi.fn().mockRejectedValue(new Error('enqueue failed')) })).rejects.toThrow('enqueue failed');
        await expect(processEmailJob({ data: { orderId: 'order-1', template: 'order-updated' } }, { sendOrderEmail: vi.fn().mockRejectedValue(new Error('send failed')) })).rejects.toThrow('send failed');
    });
    it('has an in-memory service with no SMTP startup side effect', async () => {
        await expect(new EmailService('fixture@example.test').sendOrderEmail({ orderId: 'order-1', template: 'order-updated' })).resolves.toBeUndefined();
    });
});
