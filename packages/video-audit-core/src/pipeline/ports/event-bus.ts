/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/event-bus.ts"
# purpose: "Port Interface for Asynchronous Versioned Event Bus."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AuditEvent, AuditEventType } from '../domain/events/events.js';

export type AuditEventHandler<T extends AuditEvent = AuditEvent> = (event: T) => Promise<void> | void;
export type Unsubscribe = () => void;

export interface AuditEventBus {
  publish(event: AuditEvent): Promise<void>;
  subscribe<T extends AuditEvent = AuditEvent>(
    eventType: AuditEventType | '*',
    handler: AuditEventHandler<T>
  ): Promise<Unsubscribe>;
}
