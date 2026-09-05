# AgriBridge Field Agent Workflow & Lifecycle

## 1. Complete Task Lifecycle
```
PENDING
   ↓  (Agent chooses Accept or Reject)
ASSIGNED / ACCEPTED  (or REJECTED with mandatory reason)
   ↓
IN_PROGRESS
   ↓
FIELD_VISIT (On-site inspection)
   ↓
REPORT_SUBMITTED (Observation + Photos + Findings)
   ↓
VERIFICATION RESULT (VERIFIED_DISEASE / NOT_VERIFIED / INCONCLUSIVE)
   ↓
CLOSED
```

---

## 2. Notification Delivery Lifecycle
```
CREATED (AI/Engine creates event)
   ↓
QUEUED (Buffered in message broker/database)
   ↓
SENT (Dispatched via delivery channel)
   ↓
DELIVERED (Device acknowledgement received)
   ↓
READ (Farmer views notification on dashboard)

* Failure Path:
FAILED (Network or token error) → RETRYING (Exponential backoff) → DELIVERED (or Fallback SMS)
```

---

## 3. Human Verification Policy
1. **Never Bypass Gates**: Field agents verify biological facts (pathogen presence, sensor wiring, damage percentage).
2. **Standardized Knowledge-Base Execution**: Once a pathogen is verified (`VERIFIED_DISEASE`), the application unlocks verified recommendations from the ICAR/Agricultural knowledge base rather than unstructured free-form advice.
3. **Full Audit Trace**: Every transition records `timestamp`, `agent_id`, `status`, and `notes`.

