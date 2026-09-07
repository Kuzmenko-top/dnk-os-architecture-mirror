# Multi-Region Routing & Replication Reference Details

## 🌐 Cloudflare Workers Geo-Routing Example

```javascript
export default {
  async fetch(request, env, ctx) {
    const country = request.headers.get("cf-ipcountry") || "US";
    const url = new URL(request.url);

    // Route EU/UK traffic to Europe
    if (["EU", "GB", "DE", "FR"].includes(country)) {
      url.hostname = "eu-west-1.api.dnk-os.com";
    } else if (["JP", "SG", "AU", "KR"].includes(country)) {
      url.hostname = "ap-southeast-1.api.dnk-os.com";
    } else {
      url.hostname = "us-east-1.api.dnk-os.com";
    }

    return fetch(url.toString(), request);
  }
};
```

## 📊 PostgreSQL Cross-Region Replication Lag Query

To inspect logical replication delay in PostgreSQL primary:

```sql
SELECT
    subname AS subscription_name,
    pg_wal_lsn_diff(pg_current_wal_lsn(), latest_end_lsn) AS lag_bytes,
    EXTRACT(EPOCH FROM (now() - last_msg_receipt_time)) AS lag_seconds
FROM pg_stat_subscription;
```

## 🛡️ Circuit-Breaker Integration

When replication `lag_seconds > 30`, mark the replica target as `unhealthy` in the GSLB registry to prevent stale reads and unsafe failover promotions.
