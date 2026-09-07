# 🛡️ Secure Media Ingestion, Probe Validation & SSRF Isolation Protocol (VIDEO-AUDIT-PIPELINE-001B)

## Overview
The Ingestion Layer of `@dnk/video-audit-core` provides protected entry points for media files (`DirectUploadInput`, `TelegramFileInput`, `UrlInput`) before job scheduling.

---

## 1. Core Ingestion Security Rules

### A. Path Traversal & Filename Sanitization
- **Rule**: Never trust client-provided file names or paths.
- **Implementation (`sanitizeFilename`)**:
  - Replaces null bytes (`\0`) and control characters (`\x00-\x1f`).
  - Removes directory traversal sequences (`../`, `..\`, `./`).
  - Strips illegal OS path characters (`<>:"/\|?*`).
  - Limits output filename length to 255 characters.
  - Storage path inside `ArtifactStore` uses SHA-256 binary hash digest, NOT the user filename (`artifacts/{jobType}/{referenceAssetId}/{sha256}.bin`).

### B. MIME Spoofing & Magic Bytes Sniffing
- **Rule**: Never trust `Content-Type` header from HTTP clients or file extension.
- **Sniffing Table (`sniffMediaHeader`)**:
  - `MP4`: `ftyp` box at byte 4 (`0x66 0x74 0x79 0x70`).
  - `MOV`: `ftyp` box (`qt  `, `mp42`, `isom`) or `moov` / `mdat` atom headers.
  - `WEBM` / `MKV`: Matroska EBML ID (`0x1A 0x45 0xDF 0xA3`).
  - `GIF` / `PNG` / `JPEG` / `PDF` / `ELF` / `PE` / `HTML`: Explicitly detected and blocked if non-media.

### C. SSRF (Server-Side Request Forgery) URL Protection
- **Rule**: Validate all target URLs before issuing HTTP requests.
- **Forbidden Ranges (`validateUrlForSsrf`)**:
  - Protocol: `https:` only (`http:`, `ftp:`, `file:`, `gopher:` rejected).
  - Private IP Ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8` (Loopback).
  - Cloud Metadata Endpoints: `169.254.169.254` (AWS IMDS, GCP, Azure).
  - Special Hosts: `localhost`, `*.local`, `*.internal`.
  - Credentials: URLs containing user/password (`https://user:pass@domain.com`) rejected.

---

## 2. Ingestion Idempotency & SHA-256 Deduplication

1. **Content Hash Deduplication**:
   - Calculate SHA-256 digest of incoming media payload.
   - Query `ReferenceAssetRepository.findByContentHash(sha256)`.
   - If match found: Return existing `ReferenceAsset`, avoiding duplicate binary storage and re-processing.

2. **Telegram Update Tracker**:
   - Tracks processed `telegram_update_id` and `file_unique_id`.
   - Idempotent re-tries return existing asset and job status without duplicate task creation.

---

## 3. Degraded Capability Mode (Audio-less Video)

- When media probe detects video container without audio stream (`probe.hasAudio === false`):
  - Mark `ReferenceAsset` metadata with `hasAudio: false`.
  - Exclude `transcription` and `prosody_analysis` from derived `MediaCapability`.
  - Append warning to `degradationWarnings: ['NO_AUDIO_STREAM_DETECTED']`.
  - Allow downstream visual-only audit jobs (`visual_analysis`, `shot_detection`) to proceed normally.
