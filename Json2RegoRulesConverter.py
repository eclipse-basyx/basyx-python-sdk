import json
from typing import Dict, Any

def convert_idta_rule_to_rego(rule: Dict[str, Any], rule_index: int = 0) -> str:
    formula = rule.get("FORMULA", {})
    acl = rule.get("ACL", {})
    rights = acl.get("RIGHTS", [])
    access = acl.get("ACCESS", "DENY").upper()

    if access != "ALLOW":
        return ""

    rego_conditions = []

    def parse_expression(expr: Dict[str, Any]) -> str:
        if "$eq" in expr:
            left = parse_operand(expr["$eq"][0])
            right = parse_operand(expr["$eq"][1])
            return f"{left} == {right}"
        elif "$regex" in expr:
            left = parse_operand(expr["$regex"][0])
            pattern = expr["$regex"][1].get("$strVal", "")
            return f're_match("{pattern}", {left})'
        elif "$ge" in expr:
            left = parse_operand(expr["$ge"][0])
            right = parse_operand(expr["$ge"][1])
            return f"{left} >= {right}"
        elif "$le" in expr:
            left = parse_operand(expr["$le"][0])
            right = parse_operand(expr["$le"][1])
            return f"{left} <= {right}"
        elif "$and" in expr:
            return " and ".join([f"({parse_expression(sub)})" for sub in expr["$and"]])
        elif "$or" in expr:
            return " or ".join([f"({parse_expression(sub)})" for sub in expr["$or"]])
        else:
            return "# unsupported expression"

    def parse_operand(operand: Dict[str, Any]) -> str:
        if "$attribute" in operand:
            attr = operand["$attribute"]
            if "CLAIM" in attr:
                return f'input.subject.{attr["CLAIM"]}'
            if "REFERENCE" in attr:
                return f'input.resource.{attr["REFERENCE"].replace("(Submodel)*#", "")}'
            if "GLOBAL" in attr:
                return f'input.context.{attr["GLOBAL"]}'
        elif "$field" in operand:
            return f'input.resource.{operand["$field"].replace("$sm#", "")}'
        elif "$strVal" in operand:
            return f'"{operand["$strVal"]}"'
        elif "$timeVal" in operand:
            return f'"{operand["$timeVal"]}"'
        else:
            return "# unsupported operand"

    if formula:
        rego_conditions.append(parse_expression(formula))

    if rights:
        right_exprs = [f'input.action == "{right}"' for right in rights]
        rego_conditions.append(f"({' or '.join(right_exprs)})")

    if not rego_conditions:
        return ""

    conditions_block = "\n    ".join(rego_conditions)
    rule_block = f"""
allow_rule_{rule_index} {{
    {conditions_block}
}}"""
    return rule_block


def generate_rego_policy_from_idta(json_data: Dict[str, Any]) -> str:
    """
    Generate a complete Rego policy from an IDTA-01004 rule set.
    """
    rules = json_data.get("AllAccessPermissionRules", {}).get("rules", [])
    rule_blocks = [convert_idta_rule_to_rego(rule, idx) for idx, rule in enumerate(rules)]
    rule_blocks = [rb for rb in rule_blocks if rb.strip()]

    allow_conditions = " or ".join([f"allow_rule_{i}" for i in range(len(rule_blocks))])
    rego_policy = "package accesscontrol\n\ndefault allow = false\n\n"
    rego_policy += f"allow {{\n    {allow_conditions}\n}}\n"
    rego_policy += "\n".join(rule_blocks)
    return rego_policy

def save_rego_policy_to_file(rego_policy: str, file_path: str) -> None:
    with open(file_path, "w") as f:
        f.write(rego_policy)


if __name__ == "__main__":
    with open("policies/rules.json") as f:
        json_data = json.load(f)
        rego_policy = generate_rego_policy_from_idta(json_data)
        save_rego_policy_to_file(rego_policy, "policies/access_policy.rego")
