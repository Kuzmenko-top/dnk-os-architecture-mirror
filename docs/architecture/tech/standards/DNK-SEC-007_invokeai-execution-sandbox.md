# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/standards/DNK-SEC-007_invokeai-execution-sandbox.md"
# purpose: "Security Standards, Model Weight Deserialization & GPU Guardrails for InvokeAI Invocations"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

# 🛡️ Security Standards: InvokeAI Execution Sandbox & Weights Firewall (DNK-SEC-007)

This specification defines the security invariants, model deserialization guardrails, and hardware protection policies for running InvokeAI invocations inside **DNK OS**.

---

## 1. Model Weights Deserialization Guard

To eliminate Remote Code Execution (RCE) vectors through malicious model weights:
- **Safetensors Exclusivity**: Production nodes MUST prioritize and enforce `.safetensors` model formats.
- **Pickle Deserialization Block**: Direct loading of legacy PyTorch `.ckpt` or `.bin` files via unrestricted `torch.load` is strictly prohibited. If legacy checkpoints are imported, they must be converted in an isolated ephemeral container via `pickle_safety_scanner`.
- **Cryptographic Hash Verification**: Model downloads must match SHA-256 / Blake3 hashes registered in the DNK Model Manifest.

---

## 2. Dynamic Invocations & Node Sandbox

Custom user-defined and community invocations run with strict isolation:
- **No Unrestricted Filesystem Access**: Invocations can only read and write to designated tenant asset buffers (`/outputs/tenant_id/...`).
- **Network Egress Filtering**: Generative nodes have zero outbound network access during execution. Remote ControlNet or LoRA assets must be pre-fetched by the Model Manager before graph execution starts.
- **AST / Import Whitelist**: Custom nodes are audited for prohibited primitives (`os.system`, `subprocess`, raw network sockets).

---

## 3. GPU Hardware & Memory Protection

To avoid Out-of-Memory (OOM) crashes and system instability:
- **Sequential VRAM Offloading**: Models (Text Encoder, UNet/DiT, VAE) are dynamically loaded into VRAM only during their active execution step and evicted when inactive.
- **Tiled VAE & Attention Slicing**: Mandatory for images exceeding $1024 \times 1024$ resolution to maintain stable memory ceilings.
- **Execution Timeout**: Any single node invocation exceeding `120s` on local GPU or `300s` on cloud workers is terminated with a `GenerativeTimeoutException`.
