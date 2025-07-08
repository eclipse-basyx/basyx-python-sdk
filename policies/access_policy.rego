package accesscontrol

default allow = false

allow {
    allow_rule_0
}

allow_rule_0 {
    ((input.resource.semanticId == "SemanticID-Nameplate") or (input.resource.semanticId == "SemanticID-TechnicalData")) and (input.subject.Role == "admin") and (re_match("^https://company1.com/.*$", input.resource.Id)) and (input.context.UTCNOW >= "09:00") and (input.context.UTCNOW <= "17:00")
    (input.action == "READ" or input.action == "WRITE")
}