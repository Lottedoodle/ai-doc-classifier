"""Tear down the temporary Adminer POC resources."""
from __future__ import annotations

import json
import os
import subprocess
import sys

REGION = "ap-southeast-2"
CLUSTER = "cvx-slip-receipt-cluster"
LISTENER_ARN = "arn:aws:elasticloadbalancing:ap-southeast-2:047750375159:listener/app/cvx-alb/0ff71d0ca84a1895/a5a6375302f060b6"
CF_ID = "E2ILLRM0QYLHMI"


def run(args: list[str], check: bool = True) -> str:
    result = subprocess.run(args, capture_output=True, text=True, shell=True)
    if check and result.returncode != 0:
        print(result.stderr or result.stdout)
        if check:
            sys.exit(1)
    return result.stdout


def main() -> None:
    # Scale down / delete service
    run([
        "aws", "ecs", "update-service",
        "--region", REGION,
        "--cluster", CLUSTER,
        "--service", "cvx-adminer-service",
        "--desired-count", "0",
    ], check=False)
    run([
        "aws", "ecs", "delete-service",
        "--region", REGION,
        "--cluster", CLUSTER,
        "--service", "cvx-adminer-service",
        "--force",
    ], check=False)
    print("Deleted ECS service cvx-adminer-service")

    # Delete ALB rules matching /adminer
    rules = json.loads(run([
        "aws", "elbv2", "describe-rules",
        "--region", REGION,
        "--listener-arn", LISTENER_ARN,
    ]))
    for rule in rules["Rules"]:
        for cond in rule.get("Conditions", []):
            if cond.get("Field") == "path-pattern":
                values = cond.get("PathPatternConfig", {}).get("Values") or cond.get("Values", [])
                if any(v.startswith("/adminer") for v in values):
                    run([
                        "aws", "elbv2", "delete-rule",
                        "--region", REGION,
                        "--rule-arn", rule["RuleArn"],
                    ])
                    print(f"Deleted ALB rule {rule['RuleArn']}")

    # Delete target group
    tg = run([
        "aws", "elbv2", "describe-target-groups",
        "--region", REGION,
        "--names", "cvx-adminer-tg",
        "--query", "TargetGroups[0].TargetGroupArn",
        "--output", "text",
    ], check=False).strip()
    if tg and tg != "None":
        run([
            "aws", "elbv2", "delete-target-group",
            "--region", REGION,
            "--target-group-arn", tg,
        ], check=False)
        print("Deleted target group cvx-adminer-tg")

    # Remove CloudFront behavior
    raw = run(["aws", "cloudfront", "get-distribution-config", "--id", CF_ID])
    data = json.loads(raw)
    etag = data["ETag"]
    cfg = data["DistributionConfig"]
    behaviors = cfg.get("CacheBehaviors") or {"Quantity": 0, "Items": []}
    items = [b for b in (behaviors.get("Items") or []) if b.get("PathPattern") != "/adminer*"]
    if len(items) != len(behaviors.get("Items") or []):
        cfg["CacheBehaviors"] = {"Quantity": len(items), "Items": items} if items else {"Quantity": 0}
        infile = os.path.join(os.environ["TEMP"], "cf_adminer_teardown.json")
        with open(infile, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        run([
            "aws", "cloudfront", "update-distribution",
            "--id", CF_ID,
            "--if-match", etag,
            "--distribution-config", f"file://{infile}",
        ])
        print("Removed CloudFront behavior /adminer*")
    else:
        print("CloudFront behavior /adminer* not found")

    print("Adminer POC teardown complete")


if __name__ == "__main__":
    main()
