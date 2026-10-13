import type { Queue } from 'bullmq';
import { ORDERS_TOPIC, validateOrderEvent, type OrderEvent } from '../domain/events.js';
import type { SendOrderEmailJobData } from '../domain/jobs.js';
import { enqueueOrderEmail } from '../producers/emailProducer.js';
// RKG_EXPECT: event-to-email-queue
export async function dispatchOrderEvent(topic: string, event: OrderEvent, queue: Pick<Queue<SendOrderEmailJobData>, 'add'>): Promise<void> {
    if (topic !== ORDERS_TOPIC)
        throw new Error('Unsupported event topic');
    validateOrderEvent(event);
    await enqueueOrderEmail(queue, { orderId: event.order_id, template: 'order-updated' });
}
