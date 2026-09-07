# Next.js 14 Web UI Dashboard & Local Media Processing Architecture (DNK-STD-0092)

## Overview
This reference specifies the full-stack integration pattern connecting a modern Next.js 14 App Router frontend to a FastAPI/Celery video processing backend, supporting both interactive web uploads and high-throughput local media volume mounts (1000+ GB archives).

---

## 1. Next.js 14 Reverse Proxy Handler Pattern (`app/api/proxy/[...path]/route.ts`)

To avoid Cross-Origin Resource Sharing (CORS) complexity and streamline authentication/streaming, use an App Router catch-all route handler that dynamically forwards HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`) to the backend service.

```typescript
// app/api/proxy/[...path]/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleProxy(request, params.path)
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleProxy(request, params.path)
}

async function handleProxy(request: NextRequest, pathSegments: string[]) {
  const backendBase = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const targetPath = pathSegments.join('/')
  const searchParams = request.nextUrl.searchParams.toString()
  const targetUrl = `${backendBase}/api/${targetPath}${searchParams ? `?${searchParams}` : ''}`

  try {
    const headers = new Headers(request.headers)
    headers.delete('host')

    const body = request.method !== 'GET' && request.method !== 'HEAD' ? await request.blob() : undefined

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: headers,
      body: body,
      // @ts-ignore - Required for Node.js fetch streaming in Node 18+
      duplex: 'half',
    })

    const responseBody = await response.blob()
    return new NextResponse(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    })
  } catch (err: any) {
    return NextResponse.json(
      { error: 'Failed to proxy request to backend', details: err.message },
      { status: 502 }
    )
  }
}
```

---

## 2. Multi-Stage Pipeline Execution with Progress Tracking

The client-side upload component coordinates the end-to-end media pipeline across discrete HTTP stages:
1. **Ingest (`POST /api/proxy/video/ingest`)**: Uploads video multipart payload, performs SHA-256 deduplication and FFmpeg 16kHz audio extraction.
2. **Transcribe (`POST /api/proxy/video/transcribe/{footage_id}`)**: Invokes Gemini 3.5 STT with word-level timestamps.
3. **AutoCut (`POST /api/proxy/video/cut/{footage_id}`)**: Evaluates filler words, pause thresholds, and generates clean keep-ranges.
4. **Index (`POST /api/proxy/library/search`)**: Embeds transcript into 1024-dim pgvector space for instant semantic search.

---

## 3. Local Archive Volume Mount & Batch Ingest (1000+ GB)

For processing high-volume raw video footage without web browser upload bottlenecks:
- Mount host raw archive folder into Docker services:
  ```yaml
  volumes:
    - ./data/video_archive:/data/video_archive
  ```
- Trigger headless pipeline execution via CLI inside the worker:
  ```bash
  docker-compose exec worker python scripts/media/run_pipeline.py --video /data/video_archive/video.mp4
  ```
