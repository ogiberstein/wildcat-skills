# Promise Machine audit

## Step 1, round 1 -- 2026-08-20

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `scripts/promise_machine.py` | `check --only copies` removed a missing-law finding and returned success without comparing a copy to an authored source | fixed in the audit fix commit |
| S1-R1-02 | medium | `scripts/promise_machine.py` | `check --only law` still ran plugin discovery and could fail on an unrelated empty plugin tree | fixed in the audit fix commit |

Leads not pursued: replacement of a plugin directory by another local process
between discovery and atomic rename. The command operates in the caller-owned
checkout under the caller's filesystem permissions, writes fixed destinations
and claims no hostile multi-user synchronisation boundary.
