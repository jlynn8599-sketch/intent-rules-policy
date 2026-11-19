#!/usr/bin/env python3
"""Intent Rules v1.0.0 - minimal reference evaluator (EXAMPLE ONLY).

Reads policies/intent_rules_v1.0.0.yaml and decides ALLOW / DENY for a
signed work order, using the policy's five verifier questions (VQ1-VQ5).

This is a teaching demo, NOT the JLMAI framework and NOT production code:
  - VQ5 (signature / attestation validity) is STUBBED: it only checks that
    a signature field is present. A real deployment must verify the
    Ed25519 signature and the ZK provenance attestation.
  - There is no network, no key management, and no real ledger service.
    Decisions are appended to a local verification_ledger.jsonl file.
  - The default decision is DENY. Any failed check denies, and the gate
    fails closed on malformed input.

Usage:
  pip install pyyaml
  python3 intent_gate.py ../../policies/intent_rules_v1.0.0.yaml work_order_allow.json
  python3 intent_gate.py --demo   # runs the five bundled cases
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required for this example: pip install pyyaml")

LEDGER = Path(__file__).resolve().parent / "verification_ledger.jsonl"


def load_policy(path):
    with open(path) as f:
        return yaml.safe_load(f)


def policy_version(policy):
    # metadata.name is "intent-rules-v1.0.0" -> version "v1.0.0"
    return policy["metadata"]["name"].rsplit("-", 1)[-1]


def tier_of_intent(policy, intent):
    for tier_name, tier in policy["riskTiers"].items():
        if intent in tier["intents"]:
            return tier_name, tier
    return None, None


def evaluate(policy, order, used_nonces):
    """Return (decision, failed_check, detail). Decision is ALLOW or DENY."""
    checks = []

    def fail(check, detail):
        checks.append((check, "FAIL", detail))
        return "DENY", check, detail

    # VQ1 - intent match: the requested intent must exist and must be the
    # exact intent declared in the signed work order.
    tier_name, tier = tier_of_intent(policy, order.get("intent"))
    if tier is None:
        return fail("VQ1_INTENT_MATCH",
                    f"unknown intent: {order.get('intent')!r}")
    checks.append(("VQ1_INTENT_MATCH", "PASS",
                   f"intent {order['intent']!r} found in {tier_name}"))

    # VQ2 - role boundary: the role's max tier must cover the intent's tier.
    role = order.get("role")
    roles = policy.get("agentRoles", {})
    if role not in roles:
        return fail("VQ2_ROLE_BOUNDARY", f"unknown role: {role!r}")
    max_tier = roles[role]["maxTier"]
    if tier["level"] > max_tier:
        return fail("VQ2_ROLE_BOUNDARY",
                    f"role {role!r} (max tier {max_tier}) cannot run "
                    f"tier {tier['level']} intent {order['intent']!r}")
    if tier.get("requiresFounderSignoff") and not order.get("founder_signoff"):
        return fail("VQ2_ROLE_BOUNDARY",
                    f"tier {tier['level']} requires founder sign-off")
    if tier.get("autonomousExecutionAllowed") is False and order.get("autonomous"):
        return fail("VQ2_ROLE_BOUNDARY",
                    f"tier {tier['level']} does not allow autonomous execution")
    checks.append(("VQ2_ROLE_BOUNDARY", "PASS",
                   f"role {role!r} authorized for tier {tier['level']}"))

    # VQ3 - parameter bounds: target and value must stay inside the
    # constraints declared in the work order.
    request = order.get("request", {})
    constraints = order.get("constraints", {})
    allowed_targets = constraints.get("allowed_targets")
    if allowed_targets is not None and request.get("target") not in allowed_targets:
        return fail("VQ3_PARAMETER_BOUNDS",
                    f"target {request.get('target')!r} not in allowed targets")
    max_value = constraints.get("max_value")
    if max_value is not None and request.get("value", 0) > max_value:
        return fail("VQ3_PARAMETER_BOUNDS",
                    f"value {request.get('value')} exceeds max {max_value}")
    checks.append(("VQ3_PARAMETER_BOUNDS", "PASS", "target and value in bounds"))

    # VQ4 - freshness / nonce: the work order must be for the current policy
    # version, unexpired, and its nonce must not have been used before.
    if order.get("policy_version") != policy_version(policy):
        return fail("VQ4_FRESHNESS_NONCE",
                    f"work order is for policy {order.get('policy_version')!r}, "
                    f"current is {policy_version(policy)!r}")
    try:
        expires = datetime.fromisoformat(
            order["expires_at"].replace("Z", "+00:00"))
    except (KeyError, ValueError):
        return fail("VQ4_FRESHNESS_NONCE", "missing or invalid expires_at")
    if expires <= datetime.now(timezone.utc):
        return fail("VQ4_FRESHNESS_NONCE",
                    f"work order expired at {order['expires_at']}")
    nonce = order.get("nonce")
    if not nonce:
        return fail("VQ4_FRESHNESS_NONCE", "missing nonce")
    if nonce in used_nonces:
        return fail("VQ4_FRESHNESS_NONCE", f"nonce {nonce!r} already used (replay)")
    used_nonces.add(nonce)
    checks.append(("VQ4_FRESHNESS_NONCE", "PASS", "current, unexpired, fresh nonce"))

    # VQ5 - attestation validity. STUB in this example: presence only.
    # A real deployment verifies the Ed25519 signature here.
    if not order.get("signature"):
        return fail("VQ5_ATTESTATION_VALID", "missing signature")
    checks.append(("VQ5_ATTESTATION_VALID", "PASS",
                   "signature present (STUB - not cryptographically verified)"))

    return "ALLOW", None, "all five verifier questions passed"


def record_ledger(order, decision, failed_check):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "work_order_id": order.get("work_order_id"),
        "intent": order.get("intent"),
        "role": order.get("role"),
        "decision": decision,
        "failed_check": failed_check,
    }
    with open(LEDGER, "a") as f:
        f.write(json.dumps(entry) + "\n")


def run_case(policy, order_path, used_nonces):
    with open(order_path) as f:
        order = json.load(f)
    decision, failed, detail = evaluate(policy, order, used_nonces)
    record_ledger(order, decision, failed)
    status = f"{decision} ({failed}: {detail})" if failed else f"{decision} - {detail}"
    print(f"{Path(order_path).name:32} {order['intent']:28} {order['role']:26} {status}")
    return decision


def main(argv):
    here = Path(__file__).resolve().parent
    if "--demo" in argv:
        policy = load_policy(here / "../../policies/intent_rules_v1.0.0.yaml")
        used_nonces = set()
        print(f"Policy: {policy['metadata']['name']} "
              f"(default: {policy['metadata']['defaultDecision']}, "
              f"fail-closed: {policy['enforcement']['failClosed']})")
        print(f"{'work order':32} {'intent':28} {'role':26} decision")
        run_case(policy, here / "work_order_allow.json", used_nonces)
        run_case(policy, here / "work_order_deny_role.json", used_nonces)
        run_case(policy, here / "work_order_deny_tier4.json", used_nonces)
        run_case(policy, here / "work_order_deny_expired.json", used_nonces)
        # Replay: same work order (same nonce) as the first case.
        run_case(policy, here / "work_order_allow.json", used_nonces)
        print(f"\nDecisions appended to {LEDGER.name}")
        return 0
    if len(argv) != 3:
        print(__doc__)
        return 2
    policy = load_policy(argv[1])
    return 0 if run_case(policy, argv[2], set()) == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
