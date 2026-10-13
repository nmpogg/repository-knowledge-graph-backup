import type { SendOrderEmailJobData } from '../domain/jobs.js';
// RKG_EXPECT: email-service
export class EmailService {
    constructor(private readonly fromAddress: string) { }
    async sendOrderEmail(message: SendOrderEmailJobData): Promise<void> {
        void this.fromAddress;
        void message.orderId;
        await Promise.resolve();
    }
}
