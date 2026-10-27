# Test matrix

| Scenario | Expected behavior | Python reference test | IRIS run still required |
|---|---|---:|---:|
| Valid ADT A01 with PID/PV1 | Accept | Yes | Yes |
| Valid ORU R01 with PID/OBR/OBX | Accept | Yes | Yes |
| Missing MSH | Reject | Yes | Yes |
| Missing required segment | Reject | Yes | Yes |
| Unsupported message type | Reject/quarantine | Yes | Yes |
| Duplicate sender + control ID | Detect duplicate | In-memory only | Durable ledger |
| Same control ID from another sender | Distinct identity | Yes | Yes |
| Transient failure | Retry within limit | Policy only | Yes |
| Retry exhausted | Quarantine/dead-letter | Policy only | Yes |
| Malformed/permanent failure | No retry loop | Policy only | Yes |
| Engine restart during processing | Recover safely | No | Yes |
| ACK at agreed persistence boundary | Correct ACK/NACK | No | Yes |
| Replay | Authorized and audited | No | Yes |

This is a test plan. Mark a scenario passed only after actually running it.
