# 🔬 WebAssembly & WebGL Reverse Engineering Patterns

## 📌 Overview
High-velocity protocol for extracting, decompiling, and analyzing client-side WebAssembly (`.wasm`) binaries, WebGL/WebGL2 shader pipelines, and offscreen canvas acceleration buffers during web application reverse engineering.

---

## 🧬 1. WebAssembly Binary Interception & Acquisition

### 1.1 Discovery & Retrieval
1. **Performance & Network Scanning**:
   ```javascript
   // Scan performance resource buffer for .wasm assets
   const wasmEntries = performance.getEntriesByType('resource')
       .filter(r => r.name.includes('.wasm'))
       .map(r => r.name);
   ```
2. **Worker & Dynamic Import Traversal**:
   Search bundle and web worker scripts for dynamic import patterns:
   - `fetch('*.wasm')` / `WebAssembly.instantiateStreaming`
   - Hardcoded CDN static resource paths (`/sdk/.../*.wasm`).

3. **In-Browser Binary Fetch & Serialization**:
   ```javascript
   const res = await fetch(wasmUrl);
   const buffer = await res.arrayBuffer();
   const bytes = new Uint8Array(buffer);
   let binary = '';
   for (let i = 0; i < bytes.byteLength; i++) {
       binary += String.fromCharCode(bytes[i]);
   }
   const base64Wasm = btoa(binary);
   ```

---

## ⚙️ 2. Static Parsing & Decompilation Toolchain

### 2.1 Native macOS/Linux Toolchain
- `wasm-decompile`: High-level C-like pseudocode representation with control flow.
- `wasm2wat`: WebAssembly text format (S-expressions) for opcode-level validation.
- `wasm-objdump --details`: Export/Import table and section size breakdown.
- `wasm2c`: Compiles WASM into pure ANSI C source and headers.

### 2.2 CLI Execution Pipeline
```bash
# Decompile WASM to high-level readable C-like code
wasm-decompile module.wasm -o module.c

# Inspect exported/imported symbols
wasm-objdump --details -x module.wasm

# Extract data segments and debug string references
wasm-decompile module.wasm | grep -E "(d_|export|import)"
```

### 2.3 Identifying Toolchain & Provenance
- Look at data strings (`data d_...`) in the decompiled output to recover internal build paths (e.g., `client/api_client/src/definitions.rs`).
- `__wbindgen_*` exports signify Rust + `wasm-bindgen`.
- `_emscripten_*` or `_malloc` exports signify C/C++ + Emscripten.

---

## 🎨 3. WebGL Shader Pipeline Extraction

### 3.1 Intercepting Shaders via Runtime Hooking
```javascript
const originalShaderSource = WebGLRenderingContext.prototype.shaderSource;
WebGLRenderingContext.prototype.shaderSource = function(shader, source) {
    window.__captured_shaders = window.__captured_shaders || [];
    window.__captured_shaders.push({
        type: shader.type,
        source: source,
        timestamp: performance.now()
    });
    return originalShaderSource.apply(this, arguments);
};
```

### 3.2 Key WebGL Shader Architectures in Web Canvas
1. **Quad Vertex Shader**: Renders full-screen clip-space quad `[-1, 1]` with normalized UVs `[0, 1]` for post-processing filters.
2. **Color Clamping & Exposure Fragment Shader**: Implements `min(max(color, minVal), maxVal)` for dynamic range thresholding and alpha clipping previews.
3. **Dual Blend Composite Fragment Shader**: Mixes base and overlay textures (`mix(base, overlay, alpha)` or `base * overlay`) on the GPU.
4. **Tensor Dimension Remapping Fragment Shader**: Packs/unpacks multidimensional tensor textures for client-side ML/inference models.

---

## 📐 4. Offscreen Canvas Buffer Reverse Engineering

### 4.1 Categorizing Canvas Elements
1. **Typography & Text Metric Buffer (e.g. `750x81 px`)**:
   - Dedicated offscreen canvas used by rich-text engines (Tiptap / ProseMirror / Skia).
   - Computes glyph advances, multiline word wrapping, ascenders/descenders, and kerning without causing DOM reflows.
2. **Interactive Tooling Buffers (e.g. `300x150 px`)**:
   - Isolated canvas elements for brush stroke dynamics, chromatic wheel pickers, and live color sampling.
3. **Main Scene Graph Stage (e.g. `3360x1924 px` physical / DPR 2.0)**:
   - Layer 1 (z: 20): Interactive transformer handles, rotation anchors, and magnetic snap guides.
   - Layer 2 (z: 0): Active Konva/Fabric scene graph (shapes, groups, images).
   - Layer 3 (z: -1): Static backdrop, canvas boundaries, artboards, grid lines.
