Class HealthcareIntegrationLab.HL7.Message Extends %Persistent
{
Property SourceSystem As %String(MAXLEN = 128) [ Required ];
Property MessageControlID As %String(MAXLEN = 128) [ Required ];
Property MessageType As %String(MAXLEN = 64) [ Required ];
Property ProcessingStatus As %String(MAXLEN = 32) [ InitialExpression = "RECEIVED" ];
Property AttemptCount As %Integer [ InitialExpression = 0 ];
Property LastErrorCode As %String(MAXLEN = 64);
Property ReceivedAt As %TimeStamp;

Index MessageIdentity On (SourceSystem, MessageControlID) [ Unique ];

// Illustrative persistent ledger model. Compile and validate in IRIS before use.
}
