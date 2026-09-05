# AgriBridge — Testing Guide & Verification Suite
**Smart Horizon 2026 | Test Suite Pass Rate: 270/270 (100% Green)**

---

## 1. Quick Command Reference

```bash
# Run entire test suite across unit and integration
python -m pytest tests/unit/ tests/integration/

# Run specific domain suites
python -m pytest tests/unit/test_saathi_step*.py
python -m pytest tests/integration/test_orchestration.py
python -m pytest tests/integration/test_borderline_escalation.py
```

## 2. Test Architecture & Coverage

- **Unit Tests (156 Tests)**: Steps 1 to 20 Saathi Companion, script detection, zero-hallucination guardrails, 4-state lifecycle status tests.
- **Integration Tests (114 Tests)**: End-to-end multi-signal pipelines, crop monitoring handoffs, borderline escalations, live weather rescheduling, and role isolation audits.
