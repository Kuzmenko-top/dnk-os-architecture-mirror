/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/event-bus.test.ts"
# purpose: "Unit Tests for In-Memory Event Bus Subscriptions and Dispatch."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach } from 'vitest';
import { InMemoryAuditEventBus } from '../../src/pipeline/infrastructure/in-memory/in-memory-event-bus.js';
import { AuditJobCreatedEvent, AuditEvent } from '../../src/pipeline/domain/events/events.js';

describe('InMemoryEventBus', () => {
  let eventBus: InMemoryAuditEventBus;

  beforeEach(() => {
    eventBus = new InMemoryAuditEventBus();
  });

  it('publishes and delivers versioned events to subscribers', async () => {
    const received: AuditJobCreatedEvent[] = [];

    const unsubscribe = await eventBus.subscribe<AuditJobCreatedEvent>(
      'AuditJobCreated.v1',
      async (event) => {
        received.push(event);
      }
    );

    const sampleEvent: AuditJobCreatedEvent = {
      eventId: 'evt-1',
      eventType: 'AuditJobCreated.v1',
      correlationId: 'corr-1',
      actorId: 'test-runner',
      timestamp: new Date().toISOString(),
      payload: {
        jobId: 'job-1',
        referenceAssetId: 'ref-1',
        jobType: 'transcription',
        idempotencyKey: 'idem-1',
        attempt: 1,
        maxAttempts: 5,
        availableAt: new Date().toISOString()
      }
    };

    await eventBus.publish(sampleEvent);
    expect(received.length).toBe(1);
    expect(received[0].eventId).toBe('evt-1');

    unsubscribe();

    await eventBus.publish({
      ...sampleEvent,
      eventId: 'evt-2'
    });
    expect(received.length).toBe(1);
  });

  it('supports wildcard subscriptions', async () => {
    const allEvents: AuditEvent[] = [];

    await eventBus.subscribe('*', async (evt) => {
      allEvents.push(evt);
    });

    const sampleEvent: AuditJobCreatedEvent = {
      eventId: 'evt-wildcard',
      eventType: 'AuditJobCreated.v1',
      correlationId: 'corr-w',
      actorId: 'test-runner',
      timestamp: new Date().toISOString(),
      payload: {
        jobId: 'job-w',
        referenceAssetId: 'ref-w',
        jobType: 'ocr',
        idempotencyKey: 'idem-w',
        attempt: 1,
        maxAttempts: 3,
        availableAt: new Date().toISOString()
      }
    };

    await eventBus.publish(sampleEvent);
    expect(allEvents.length).toBe(1);
    expect(allEvents[0].eventId).toBe('evt-wildcard');
  });
});
