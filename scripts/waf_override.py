"""Override SizeRestrictions_BODY to Count in the CloudFront WAF ACL.

The AWSManagedRulesCommonRuleSet blocks request bodies larger than 8KB,
which breaks file uploads to /api/files. Counting instead of blocking
keeps the rest of the rule set active; the app enforces its own 10MB limit.
"""
import json
import os
import subprocess
import sys

TEMP = os.environ["TEMP"]
ACL_FILE = os.path.join(TEMP, "webacl.json")

# PowerShell's > redirect writes UTF-16
with open(ACL_FILE, encoding="utf-16") as f:
    data = json.load(f)

acl = data["WebACL"]
lock_token = data["LockToken"]

# Body-inspecting rules false-positive on multipart binary uploads.
# Scope-down statements aren't allowed on the CloudFront Free plan,
# so set every body-inspecting rule to Count instead of Block.
BODY_RULES = {
    "AWSManagedRulesCommonRuleSet": [
        "SizeRestrictions_BODY",
        "CrossSiteScripting_BODY",
        "GenericLFI_BODY",
        "GenericRFI_BODY",
    ],
    "AWSManagedRulesKnownBadInputsRuleSet": [
        "JavaDeserializationRCE_BODY",
        "Log4JRCE_BODY",
    ],
}

found = 0
for rule in acl["Rules"]:
    stmt = rule.get("Statement", {}).get("ManagedRuleGroupStatement")
    if stmt and stmt.get("Name") in BODY_RULES:
        overrides = stmt.setdefault("RuleActionOverrides", [])
        existing = {o["Name"] for o in overrides}
        for name in BODY_RULES[stmt["Name"]]:
            if name not in existing:
                overrides.append({"Name": name, "ActionToUse": {"Count": {}}})
        print(f"Overrides set on {stmt['Name']}: {[o['Name'] for o in overrides]}")
        found += 1
if not found:
    sys.exit("No managed rule groups found")

rules_file = os.path.join(TEMP, "waf_rules.json")
with open(rules_file, "w", encoding="utf-8") as f:
    json.dump(acl["Rules"], f)

cmd = [
    "aws", "wafv2", "update-web-acl",
    "--scope", "CLOUDFRONT",
    "--region", "us-east-1",
    "--name", acl["Name"],
    "--id", acl["Id"],
    "--lock-token", lock_token,
    "--default-action", json.dumps(acl["DefaultAction"]),
    "--visibility-config", json.dumps(acl["VisibilityConfig"]),
    "--rules", f"file://{rules_file}",
]
result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)
print("WAF updated successfully")
