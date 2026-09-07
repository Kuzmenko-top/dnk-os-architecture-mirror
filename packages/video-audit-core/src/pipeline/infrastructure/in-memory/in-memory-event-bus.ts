/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/in-memory/in-memory-event-bus.ts"
# purpose: "In-Memory Event Bus with Wildcard Subscriptions and Error Isolation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AuditEvent, AuditEventType } from '../../domain/events/events.js';
import { AuditEventBus, AuditEventHandler, Unsubscribe } from '../../ports/event-bus.js';

export class InMemoryAuditEventBus implements AuditEventBus {
  private handlers = new Map<string, Set<AuditEventHandler<any>>>();
  private publishedEvents: AuditEvent[] = [];

  async publish(event: AuditEvent): Promise<void> {
    this.publishedEvents.push(event);

    const specificHandlers = this.handlers.get(event.eventType) || new Set();
    const wildcardHandlers = this.handlers.get('*') || new Set();

    const allHandlers = [...specificHandlers, ...wildcardHandlers];

    for (const handler of allHandlers) {
      try {
        await handler(event);
      } catch (err) {
        // Log / isolate error so one failing subscriber does not halt others
        console.error(`[InMemoryAuditEventBus] Error in handler for event ${event.eventType}:`, err);
      }
    }
  }

  async subscribe<T extends AuditEvent = AuditEvent>(
    eventType: AuditEventType | '*',
    handler: AuditEventHandler<T>
  ): Promise<Unsubscribe> {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }

    const set = this.handlers.get(eventType)!;
    set.add(handler);

    return () => {
      set.delete(handler);
      if (set.size === 0) {
        this.handlers.delete(eventType);
      }
    };
  }

  getPublishedEvents(): AuditEvent[] {
    return [...this.publishedEvents];
  }

  clearPublishedEvents(): void {
    this.publishedEvents = [];
  }
}

export { InMemoryAuditEventBus as InMemoryEventBus };
