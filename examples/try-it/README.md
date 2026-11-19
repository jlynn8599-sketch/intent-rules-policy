# Try it in 5 minutes — Intent Rules reference evaluator

A minimal, runnable demo of the deny-by-default gate in
`policies/intent_rules_v1.0.0.yaml`. No framework install, no keys, no
network — just Python and the policy file.

## Run it

```bash
pip install pyyaml
python3 examples/try-it/intent_gate.py --demo
```

## What you should see

One `ALLOW` and four `DENY`s:

| Work order | Intent | Role | Result |
|---|---|---|---|
| `work_order_allow.json` | `read_chain_state` | observer | **ALLOW** — read-only, in role, fresh |
| `work_order_deny_role.json` | `execute_treasury_transfer` | observer | **DENY (VQ2)** — Tier 3 intent, role capped at Tier 1 |
| `work_order_deny_tier4.json` | `rotate_signing_keys` | orchestrator | **DENY (VQ2)** — Tier 4 is founder-only, no autonomous execution |
| `work_order_deny_expired.json` | `execute_treasury_transfer` | treasury | **DENY (VQ4)** — work order expired |
| `work_order_allow.json` again | `read_chain_state` | observer | **DENY (VQ4)** — same nonce reused (replay) |

Every decision is appended to `verification_ledger.jsonl` in this folder,
so you can see the audit trail the gate produces.

## Try your own work order

Copy one of the JSON files, change the intent, role, target, value, or
expiry, and run it directly:

```bash
python3 examples/try-it/intent_gate.py ../../policies/intent_rules_v1.0.0.yaml your_order.json
```

Exit code 0 means ALLOW, 1 means DENY.

## What this is not

- **Not the JLMAI framework.** The framework (async dispatchers, ZK
  attestation pipelines, runtime sandboxes) lives in
  [jlmai-agent-framework](https://github.com/jlynn8599-sketch/jlmai-agent-framework).
- **Not production code.** VQ5 (signature / attestation validity) is
  stubbed — it only checks that a signature field is present. A real
  deployment must verify the Ed25519 signature and the ZK provenance
  attestation before issuing a capability token.
- **Not a security audit.** It is a teaching demo of the policy model:
  default DENY, fail closed, five verifier questions, 60-second tokens.
