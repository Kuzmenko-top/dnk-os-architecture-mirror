# --- DNK-MRH-HEADER ---
# mrh_id: "event-inventory.md"
# purpose: "Реєстр схем подій та контрактів агентів (Event Schemas)."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# Event Inventory: Agent & Canvas Event Schemas

Для інтеграції живих агентів (Гєрич, Yuriy, dnk-dev-01) описані наступні типи та структури подій.

## 1. Схема подій запуску Агента (Agent Run Events)

### `agent.run.created`
Виникає, коли користувач відправив промпт, і для нього створено унікальну сесію запуску.
```typescript
interface AgentRunCreatedEvent {
  type: 'agent.run.created';
  payload: {
    runId: string;       // UUID4
    agentId: string;     // e.g. "gerych_librarian"
    prompt: string;      // Текст запиту користувача
  };
  timestamp: number;
}
```

### `agent.run.started`
Агент прийняв завдання в роботу у контейнері Docker.
```typescript
interface AgentRunStartedEvent {
  type: 'agent.run.started';
  payload: {
    runId: string;
    timestamp: number;
  };
  timestamp: number;
}
```

### `agent.run.progress`
Трансляція проміжного прогресу та думок агента.
```typescript
interface AgentRunProgressEvent {
  type: 'agent.run.progress';
  payload: {
    runId: string;
    percentage: number;  // 0 to 100
    step: string;        // e.g. "Parsing AST graph..."
    log?: string;        // Рядок логу консолі
  };
  timestamp: number;
}
```

### `agent.run.waiting_approval`
Агент вимагає підтвердження на деструктивні чи фінансові дії (MRH, Token limits).
```typescript
interface AgentRunWaitingApprovalEvent {
  type: 'agent.run.waiting_approval';
  payload: {
    runId: string;
    approvalId: string;
    requestedAction: string; // Опис дії для підтвердження користувачем
  };
  timestamp: number;
}
```

### `agent.run.completed`
Успішне завершення генерації та створення артефакту.
```typescript
interface AgentRunCompletedEvent {
  type: 'agent.run.completed';
  payload: {
    runId: string;
    artifactId?: string;   // ID створеного файлу
    resultSummary: string; // Короткий опис результату
  };
  timestamp: number;
}
```

### `agent.run.failed`
Агент зупинився через помилку чи ліміт токенів.
```typescript
interface AgentRunFailedEvent {
  type: 'agent.run.failed';
  payload: {
    runId: string;
    errorCode: string;     // напр. "TOKEN_LIMIT_EXCEEDED"
    errorMessage: string;  // Текст помилки
  };
  timestamp: number;
}
```

---

## 2. Схеми подій Артефактів та Полотна (Artifact & Canvas Events)

### `artifact.created` / `artifact.updated`
```typescript
interface ArtifactCreatedEvent {
  type: 'artifact.created';
  payload: {
    artifactId: string;
    name: string;        // liquid_banner.liquid
    type: string;        // "shopify_liquid"
    rawContent: string;  // Сирий код файлу
  };
  timestamp: number;
}
```

### `canvas.saved`
```typescript
interface CanvasSavedEvent {
  type: 'canvas.saved';
  payload: {
    canvasId: string;
    timestamp: number;
  };
  timestamp: number;
}
```
