Class HealthcareIntegrationLab.HL7.Processor
{
ClassMethod ClassifyMessage(messageType As %String) As %String
{
    If messageType = "ADT^A01^ADT_A01" Quit "ADMISSION"
    If messageType = "ORU^R01^ORU_R01" Quit "LAB_RESULT"
    Quit "UNSUPPORTED"
}

// This demonstrates the routing decision only. In an IRIS production,
// use the built-in HL7 parser, schema validation, business services,
// routing rules, transformations, and message-trace facilities.
}
