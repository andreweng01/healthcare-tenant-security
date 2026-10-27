import pytest
from reference_impl.hl7_lab import MessageLedger, parse_minimal, retry_decision

ADT = "MSH|^~\\&|REGISTRATION|HOSPITAL_A|INTEGRATION|HOSPITAL_A|20261027120000||ADT^A01^ADT_A01|MSG000001|P|2.5\rEVN|A01|20261027120000\rPID|1||PAT-10001^^^HOSPITAL_A^MR||DOE^JANE||19840212|F\rPV1|1|I|WARD^101^1^HOSPITAL_A\r"
ORU = "MSH|^~\\&|LAB|HOSPITAL_A|INTEGRATION|HOSPITAL_A|20261027121000||ORU^R01^ORU_R01|MSG000002|P|2.5\rPID|1||PAT-10001^^^HOSPITAL_A^MR||DOE^JANE||19840212|F\rOBR|1|ORD-9001|LAB-9001|CBC^Complete Blood Count\rOBX|1|NM|718-7^Hemoglobin^LN||13.4|g/dL|12.0-16.0|N|||F\r"

def test_adt_parses():
    m = parse_minimal(ADT)
    assert (m.source_system, m.control_id) == ("REGISTRATION", "MSG000001")

def test_oru_parses():
    assert parse_minimal(ORU).message_type == "ORU^R01^ORU_R01"

def test_missing_msh_rejected():
    with pytest.raises(ValueError, match="Missing MSH"):
        parse_minimal("PID|1||123\r")

def test_missing_required_segment_rejected():
    with pytest.raises(ValueError, match="PV1"):
        parse_minimal(ADT.replace("PV1|1|I|WARD^101^1^HOSPITAL_A\r", ""))

def test_unsupported_type_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        parse_minimal(ADT.replace("ADT^A01^ADT_A01", "XYZ^Z99^XYZ_Z99"))

def test_duplicate_identity_detected():
    m, ledger = parse_minimal(ADT), MessageLedger()
    assert ledger.begin(m) == "ACCEPTED"
    assert ledger.begin(m) == "DUPLICATE"

def test_same_id_from_different_source_is_distinct():
    m1 = parse_minimal(ADT)
    m2 = parse_minimal(ADT.replace("REGISTRATION", "REGISTRATION_2"))
    ledger = MessageLedger()
    assert ledger.begin(m1) == "ACCEPTED"
    assert ledger.begin(m2) == "ACCEPTED"

def test_success_state_recorded():
    m, ledger = parse_minimal(ADT), MessageLedger()
    ledger.begin(m)
    ledger.mark_success(m)
    assert ledger.get(m.source_system, m.control_id).status == "PROCESSED"

def test_retry_is_bounded():
    assert retry_decision("TRANSIENT", 1, 3) == "RETRY"
    assert retry_decision("TRANSIENT", 2, 3) == "RETRY"
    assert retry_decision("TRANSIENT", 3, 3) == "DEAD_LETTER"

def test_permanent_errors_not_retried():
    assert retry_decision("MALFORMED", 1) == "REJECT"
    assert retry_decision("UNSUPPORTED", 1) == "REJECT"
    assert retry_decision("BUSINESS_VALIDATION", 1) == "REJECT"
