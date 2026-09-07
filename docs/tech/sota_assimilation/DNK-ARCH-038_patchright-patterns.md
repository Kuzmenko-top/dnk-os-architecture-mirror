# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-ARCH-038_patchright-patterns.md"
# purpose: "Architecture: CDP bypass, AST mutations, anti-detect mechanics, and DAG topology for Patchright."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🏛️ DNK-ARCH-038: Patchright Architecture & Anti-Detect Mechanics

## 1. High-Level Architecture Topology
Patchright does not maintain a fragile manual fork of Playwright. Instead, it deploys a programmatic AST mutation pipeline using `ts-morph` targeting upstream `microsoft/playwright`:

```
+-------------------------------------------------------------+
|                 Upstream Playwright Core                   |
+-------------------------------------------------------------+
                              |
                              v
             +---------------------------------+
             |   Patchright AST Engine         |
             |   (ts-morph AST Mutators)       |
             +---------------------------------+
               |              |              |
               v              v              v
       [crPagePatch] [crExecContext] [chromiumSwitches]
               |              |              |
               +--------------+--------------+
                              |
                              v
             +---------------------------------+
             |   Patched Stealth Driver        |
             |  (Node.js / Python Runtime)     |
             +---------------------------------+
                              |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
[Zero-CDP Session]   [Crypto-Init Intercept]   [Shadow DOM Engine]
```

## 2. Core Architectural Patterns

### Pattern A: Zero-Noisy CDP Execution (Silent Engine)
- **Problem**: Antifraud engines register listeners on `console`, `Error`, and examine stack traces triggered by CDP `Runtime.enable` and `Console.enable`.
- **Patchright Solution**:
  1. Complete removal of `Runtime.enable` and `Console.enable` during target attachment in `CRPage` and `FrameSession`.
  2. Resolution of Execution Context ID by evaluating `globalThis` with `{ serialization: "idOnly" }` and parsing the returned `objectId`:
     ```ts
     const globalThis = await session._sendMayFail('Runtime.evaluate', {
         expression: "globalThis",
         serializationOptions: { serialization: "idOnly" }
     });
     const executionContextId = parseInt(globalThis.result.objectId.split('.')[1], 10);
     ```
  3. Preservation of all context isolation without notifying the target page JavaScript runtime.

### Pattern B: Network-Layer InitScript Ingestion (Stealth Injection)
- **Problem**: Script tags injected via standard DOM methods or standard CDP APIs leave observable traces in `PerformanceObserver`, DOM mutations, and script resource timings.
- **Patchright Solution**:
  1. A unique cryptographically secure 40-character hex tag (`crypto.randomBytes(20).toString('hex')`) is generated per page instance.
  2. Scripts are intercepted and injected at the network layer (`_networkManager.setRequestInterception(true)`).
  3. On frame navigation, cleanup is coordinated so that no lingering DOM markers or debug classes can be matched by bot detection scanners.

### Pattern C: Chromium Automation Flag Neutralization
- **Problem**: Launching Chromium with automation switches sets internal C++ flags in V8/Blink (`navigator.webdriver = true`, disabled WebGL features, degraded audio/video codecs).
- **Patchright Solution**:
  1. Removes `--enable-automation` from default Chromium args.
  2. Injects `--disable-blink-features=AutomationControlled`.
  3. Modifies `packages/protocol/spec/protocol.yml` and context options to enable fine-grained `focusControl` and touch simulation.

### Pattern D: Closed Shadow Root Piercing
- **Problem**: Cloudflare Turnstile and modern login/captcha widgets place verification tokens and interactive checkboxes inside Closed Shadow DOM roots, making standard selectors fail.
- **Patchright Solution**:
  1. Patches `XPathSelectorEngine` to query closed shadow roots by accessing underlying V8 node references directly through patched execution contexts.
  2. Enables robust headless interaction without triggering accessibility tree inspection flags.
