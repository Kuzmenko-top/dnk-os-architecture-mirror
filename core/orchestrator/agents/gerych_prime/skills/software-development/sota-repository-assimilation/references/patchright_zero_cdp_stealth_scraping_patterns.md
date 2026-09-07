# Patchright Zero-CDP & Anti-Detect Browser Automation Patterns

## Overview
Patchright (`Kaliiiiiiiiii-Vinyzu/patchright`) is an undetectable fork of Playwright (Node.js & Python) designed to bypass anti-bot and WAF systems (Cloudflare Turnstile, DataDome, Kasada, Akamai, PerimeterX/HUMAN, AWS WAF). It operates on an Apache 2.0 permissive license.

## Core Architectural Invariants

### 1. Zero-CDP Execution (Kasada / DataDome Bypass)
- **Problem**: Standard automation frameworks (Playwright, Puppeteer) issue `Runtime.enable` and `Console.enable` CDP commands on launch. Sophisticated anti-bot engines detect these via V8 console listener hooks, stack trace mutations, and CDP event leaks.
- **Pattern**: Completely suppress `Runtime.enable` and `Console.enable`. To resolve execution context IDs, evaluate a reference to `globalThis` with `{ serialization: "idOnly" }` and parse the context ID directly from `objectId.split('.')[1]`.

### 2. AST Transformation Layer (`ts-morph`)
- **Pattern**: Avoid maintaining a diverging upstream browser fork. Instead, maintain a suite of AST transformation scripts (using `ts-morph`) that patch `playwright-core` at build or post-install time. This decouples stealth enhancements from Microsoft's release cadence.

### 3. Chromium Command-Line Argument Hygiene
- **Strip**: `--enable-automation` (immediately exposes automated control).
- **Inject**: `--disable-blink-features=AutomationControlled` (resets `navigator.webdriver` to `false` at the Blink engine level).
- **Preserve**: Standard user arguments (e.g. realistic user-data-dir, default profile switches).

### 4. Network-Level InitScript Injection
- **Problem**: Standard `Page.addScriptToEvaluateOnNewDocument` leaves detectable artifacts in the DOM and prototype chains.
- **Pattern**: Intercept initial document network requests at the transport layer (`_networkManager.setRequestInterception`) and inject initialization scripts wrapped with cryptographically random 20-byte hash tags (`initScriptTag`).

### 5. Closed Shadow DOM Traversal
- **Problem**: Cloudflare Turnstile and similar challenges render interactive checkboxes inside closed shadow roots, blocking standard CSS/XPath selectors.
- **Pattern**: Modify the internal `XPathSelectorEngine` to pierce closed shadow DOM trees, allowing programmatic inspection and click dispatch.

## Hexagonal Adapter Architecture in DNK OS
```
[DNK Swarm Worker (e.g. dnk_shopify / gerych_researcher)]
                     │
                     ▼
          [PatchrightBrowserPort]  <--- Typed Contract (Pydantic / ABC)
                     │
                     ▼
           [DNKPatchrightAdapter]  <--- core/adapters/dnk_patchright_adapter.py
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
 [Zero-CDP Chromium]     [Residential Proxy + TLS JA4]
```
