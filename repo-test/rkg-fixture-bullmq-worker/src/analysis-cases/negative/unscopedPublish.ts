interface LocalPublisher { publish(topic: string, value: unknown): Promise<void> }

// Expected: no BullMQ publish edge; this receiver is an unrelated application abstraction.
export async function publishLocally(publisher: LocalPublisher, topic: string): Promise<void> {
  await publisher.publish(topic, { fixture: true });
}
