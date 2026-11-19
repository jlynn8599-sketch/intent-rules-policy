# Intent Rules v1.0.0 — Pre-Execution Authorization & Governance Policy Pack

**Author:** Jessica Lynn Moss, Founder & Chief Software Architect — **JLM AI Agent LLC** (`jlmai.org`)  
**Repository:** [`jlynn8599-sketch/intent-rules-policy`](https://github.com/jlynn8599-sketch/intent-rules-policy)  
**Upstream Reference:** NVIDIA OpenShell Community Discussions `#4247` & `#4238`  

---

## Overview

**Intent Rules v1.0.0** is a declarative, deny-by-default pre-execution authorization and governance policy pack designed for autonomous AI agents, runtime sandboxes (such as NVIDIA OpenShell), and multi-chain Web3 execution pipelines.

Rather than relying on prompt-level guardrails or post-action logging, Intent Rules v1.0.0 places a mandatory cryptographic policy gate directly in front of every tool boundary—verifying signed work orders, evaluating runtime verifier questions, issuing ephemeral capability tokens, and recording every decision to an immutable verification ledger.

---

## Core Architectural Pillars

* **Tool-Boundary Enforcement (Deny-by-Default):** Every tool call fails closed unless explicitly permitted by active policy.
* **Signed, Versioned Work Orders:** Agents cannot self-authorize privileged operations; state-changing and financial actions require a cryptographically signed, versioned work order declaring the exact authorized intent.
* **17 Intents Across 4 Risk Tiers:**
  1. **Tier 1 — Read-Only:** Non-mutating telemetry, chain state queries, and read operations.
  2. **Tier 2 — State-Changing:** Configuration updates, file mutations, and infrastructure modifications.
  3. **Tier 3 — Financial:** On-chain signing, liquidity provisioning, token transfers, and billing operations (EVM & Solana Token-2022 intent pipelines).
  4. **Tier 4 — Founder-Only Admin:** Restricted administrative and governance controls locked behind explicit founder-level cryptographic authorization.
* **Five Verifier Questions:** Extends static policy proving (*"never grants more than intended"*) into dynamic, per-action runtime verification checks before capability issuance.
* **Ephemeral Capability Tokens & Immutable Ledger:** Issues short-lived, single-scope capability tokens aligned with zero-trust credential brokering and logs every `ALLOW` / `DENY` evaluation to a tamper-evident verification ledger.

---

## Security & Compliance Matrix

| Threat Vector | Legacy Guardrail Approach | Intent Rules v1.0.0 Mitigation |
| :--- | :--- | :--- |
| **Prompt Injection / Jailbreaks** | System prompts and LLM refusal training. | **Bypass-proof:** Compromised LLM context still lacks a valid signed work order and capability token at the tool gate. |
| **Unauthorized Treasury / Contract Calls** | Broad private key access or coarse multi-sig thresholds. | **Tier-Isolated:** Isolates financial operations into Tier 3 with intent-specific work orders and short-lived capability tokens. |
| **Privilege Escalation** | Monolithic agent permissions across tools and APIs. | **Bounded Roles:** Enforces strict authority boundaries across 4 roles and 4 risk tiers; Tier 4 admin tools are locked out of autonomous execution. |
| **Compliance & Incident Forensics** | Unstructured application logs or post-hoc monitoring. | **Tamper-Evident Audit:** Generates a deterministic verification ledger capturing pre-execution policy evaluations and provenance metadata. |

---

## Try it in 5 minutes

No framework install needed — the policy is a plain YAML file, and the
`examples/try-it/` folder has a minimal reference evaluator that runs the
deny-by-default gate against it:

```bash
git clone https://github.com/jlynn8599-sketch/intent-rules-policy.git
cd intent-rules-policy
pip install pyyaml
python3 examples/try-it/intent_gate.py --demo
```

Expected output: one `ALLOW` (an observer reading chain state) and four
`DENY`s — a role trying to move treasury funds, an orchestrator reaching
for founder-only key rotation, an expired work order, and a replayed nonce.
Every decision is appended to `examples/try-it/verification_ledger.jsonl`.

The evaluator is a teaching demo, not the JLMAI framework and not
production code: it does not verify Ed25519 signatures (VQ5 is stubbed),
and it has no network or key management. The framework itself — async
dispatchers, ZK attestation pipelines, runtime sandboxes — lives in
[`jlmai-agent-framework`](https://github.com/jlynn8599-sketch/jlmai-agent-framework).

* **Policy Specification:** [`policies/intent_rules_v1.0.0.yaml`](./policies/intent_rules_v1.0.0.yaml)
* **Reference evaluator:** [`examples/try-it/intent_gate.py`](./examples/try-it/intent_gate.py)

---

## Contact & Provenance

* **Organization:** JLM AI Agent LLC (`jlmai.org`)
* **Email:** `jlmaiagent@astermail.org`
* **GitHub:** [`@jlynn8599-sketch`](https://github.com/jlynn8599-sketch)
