# Web Pixel API & GDPR-Compliant Event Ingestion Pipeline

This reference details the implementation standards for Shopify App Bridge 2.0 Web Pixel extensions, HMAC validation, GDPR/CCPA PII anonymization, and real-time event analytics.

## 1. Web Pixel Extension Architecture

Shopify Web Pixels run in an isolated sandbox environment and subscribe to customer events without impacting checkout performance.

### Extension Target & Manifest (`shopify.extension.toml`)
```toml
name = "dnk-pixel"
type = "web_pixel_extension"

[settings]
api_endpoint = "https://api.dnk.os/web-pixel/events"
runtime_context = "sandbox"

[[targeting]]
target = "web_pixel"
module = "./DNKPixel.tsx"
```

### Event Subscription Lifecycle (`DNKPixel.tsx`)
```typescript
import { useEffect } from 'react';

export function DNKPixel() {
  const publishEvent = async (eventType: string, payload: Record<string, unknown>) => {
    await fetch('/web-pixel/events', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Shopify-Topic': `web_pixel/${eventType}`,
      },
      body: JSON.stringify({
        event_type: eventType,
        timestamp: Date.now(),
        url: window.location.href,
        referrer: document.referrer,
        ...payload,
      }),
    });
  };

  useEffect(() => {
    publishEvent('page_view', { shop_id: 'dnk-store', currency: 'USD' });
  }, []);

  return null;
}
```

---

## 2. PII Anonymization & GDPR Compliance (`pii_anonymizer.py`)

All telemetry ingested from Web Pixels must be sanitized before persistence:

1. **Customer ID Hashing**:
   - Apply SHA-256 to raw `customer_id` strings (`hashlib.sha256(cid.encode()).hexdigest()`).
2. **Email Masking**:
   - `john.doe@example.com` ➔ `j******e@example.com`
   - Short usernames (<= 2 chars) masked as `a*@domain.com`.
3. **IP Truncation / Anonymization**:
   - IPv4: Zero the last octet (`192.168.1.45` ➔ `192.168.1.0`).
   - IPv6: Zero the trailing segment (`2001:db8::1` ➔ `2001:db8::0000`).

---

## 3. Web Pixel Ingestion & Security Engine (`web_pixel_ingestion.py`)

### HMAC-SHA256 Signature Verification
```python
def verify_hmac(body_bytes: bytes, received_hmac: str, secret: str) -> bool:
    expected = hmac.new(secret.encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received_hmac)
```

### Real-Time Anomaly Detection
- Negative prices on `add_to_cart` or `purchase`.
- Zero-amount completed orders.
- Abnormal item quantities (`quantity <= 0` or `quantity > 10,000`).
