"""Temporary POC: Adminer DB UI behind /adminer with HTTP Basic Auth.

Creates:
  - Target group cvx-adminer-tg
  - Task definition cvx-adminer-task (nginx + adminer)
  - ECS service cvx-adminer-service
  - ALB listener rule for /adminer*
  - CloudFront behavior /adminer*

Login (Basic Auth): admin / CvxDbAdmin2026
DB (inside Adminer): System=PostgreSQL, Server=RDS hostname,
  Username=slipapp, Password=Admincvx, Database=slipreceipt
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

REGION = "ap-southeast-2"
CLUSTER = "cvx-slip-receipt-cluster"
VPC = "vpc-0153fe51ea1fcb543"
SUBNETS = [
    "subnet-0dd9917a5eeb4e4ac",
    "subnet-0820478263b5becbc",
    "subnet-01476b86ca2f0c474",
]
SG = "sg-00cf0e57c763bc875"
ALB_ARN = "arn:aws:elasticloadbalancing:ap-southeast-2:047750375159:loadbalancer/app/cvx-alb/0ff71d0ca84a1895"
LISTENER_ARN = "arn:aws:elasticloadbalancing:ap-southeast-2:047750375159:listener/app/cvx-alb/0ff71d0ca84a1895/a5a6375302f060b6"
EXEC_ROLE = "arn:aws:iam::047750375159:role/ecsTaskExecutionRole"
CF_ID = "E2ILLRM0QYLHMI"
RDS_HOST = "database-1.c3ymo6sec310.ap-southeast-2.rds.amazonaws.com"
ALB_ORIGIN_ID = "cvx-alb-1705740726.ap-southeast-2.elb.amazonaws.com"

# admin / CvxDbAdmin2026
HTPASSWD = "admin:$apr1$BF761nGO$Dk2fwLDcUtMKWqZ2sVn2t1"

NGINX_CONF = r"""
server {
  listen 80;
  server_name _;

  location = /adminer {
    return 301 /adminer/;
  }

  location /adminer/ {
    auth_basic "CVX DB Admin (POC)";
    auth_basic_user_file /etc/nginx/htpasswd;
    proxy_pass http://127.0.0.1:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
  }

  location = /health {
    access_log off;
    return 200 'ok';
    add_header Content-Type text/plain;
  }
}
""".strip()


def run(args: list[str], check: bool = True) -> str:
    result = subprocess.run(args, capture_output=True, text=True, shell=True)
    if check and result.returncode != 0:
        print(result.stderr or result.stdout)
        sys.exit(1)
    return result.stdout


def ensure_target_group() -> str:
    out = run(
        [
            "aws", "elbv2", "describe-target-groups",
            "--region", REGION,
            "--names", "cvx-adminer-tg",
            "--query", "TargetGroups[0].TargetGroupArn",
            "--output", "text",
        ],
        check=False,
    ).strip()
    if out and out != "None" and "error" not in out.lower():
        print(f"Target group exists: {out}")
        return out

    out = run([
        "aws", "elbv2", "create-target-group",
        "--region", REGION,
        "--name", "cvx-adminer-tg",
        "--protocol", "HTTP",
        "--port", "80",
        "--vpc-id", VPC,
        "--target-type", "ip",
        "--health-check-path", "/health",
        "--health-check-interval-seconds", "15",
        "--healthy-threshold-count", "2",
        "--unhealthy-threshold-count", "3",
        "--query", "TargetGroups[0].TargetGroupArn",
        "--output", "text",
    ]).strip()
    print(f"Created target group: {out}")
    return out


def register_task_definition() -> str:
    import base64

    # Decode at container start — avoids fragile shell escaping of nginx conf
    conf_b64 = base64.b64encode(NGINX_CONF.encode()).decode()
    ht_b64 = base64.b64encode((HTPASSWD + "\n").encode()).decode()
    nginx_cmd = (
        f"echo {conf_b64} | base64 -d > /etc/nginx/conf.d/default.conf && "
        f"echo {ht_b64} | base64 -d > /etc/nginx/htpasswd && "
        "nginx -g 'daemon off;'"
    )

    task = {
        "family": "cvx-adminer-task",
        "networkMode": "awsvpc",
        "requiresCompatibilities": ["FARGATE"],
        "cpu": "256",
        "memory": "512",
        "executionRoleArn": EXEC_ROLE,
        "containerDefinitions": [
            {
                "name": "nginx",
                "image": "public.ecr.aws/nginx/nginx:1.27-alpine",
                "essential": True,
                "portMappings": [
                    {"containerPort": 80, "protocol": "tcp"}
                ],
                "entryPoint": ["/bin/sh", "-c"],
                "command": [nginx_cmd],
                "dependsOn": [
                    {"containerName": "adminer", "condition": "START"}
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/cvx-adminer-task",
                        "awslogs-region": REGION,
                        "awslogs-stream-prefix": "nginx",
                        "awslogs-create-group": "true",
                    },
                },
            },
            {
                "name": "adminer",
                "image": "adminer:4.8.1",
                "essential": True,
                "portMappings": [
                    {"containerPort": 8080, "protocol": "tcp"}
                ],
                "environment": [
                    {"name": "ADMINER_DEFAULT_SERVER", "value": RDS_HOST},
                    {"name": "ADMINER_DESIGN", "value": "pepa-linha"},
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/cvx-adminer-task",
                        "awslogs-region": REGION,
                        "awslogs-stream-prefix": "adminer",
                        "awslogs-create-group": "true",
                    },
                },
            },
        ],
    }

    infile = os.path.join(os.environ["TEMP"], "adminer_task.json")
    with open(infile, "w", encoding="utf-8") as f:
        json.dump(task, f)

    out = json.loads(run([
        "aws", "ecs", "register-task-definition",
        "--region", REGION,
        "--cli-input-json", f"file://{infile}",
    ]))
    arn = out["taskDefinition"]["taskDefinitionArn"]
    print(f"Registered task: {arn}")
    return arn


def ensure_service(task_arn: str, tg_arn: str) -> None:
    services = json.loads(run([
        "aws", "ecs", "describe-services",
        "--region", REGION,
        "--cluster", CLUSTER,
        "--services", "cvx-adminer-service",
    ]))
    existing = services["services"]
    alive = existing and existing[0]["status"] != "INACTIVE"

    net = {
        "awsvpcConfiguration": {
            "subnets": SUBNETS,
            "securityGroups": [SG],
            "assignPublicIp": "ENABLED",
        }
    }
    load_balancers = [
        {
            "targetGroupArn": tg_arn,
            "containerName": "nginx",
            "containerPort": 80,
        }
    ]

    if alive:
        run([
            "aws", "ecs", "update-service",
            "--region", REGION,
            "--cluster", CLUSTER,
            "--service", "cvx-adminer-service",
            "--task-definition", task_arn,
            "--desired-count", "1",
            "--force-new-deployment",
        ])
        print("Updated existing Adminer service")
        return

    run([
        "aws", "ecs", "create-service",
        "--region", REGION,
        "--cluster", CLUSTER,
        "--service-name", "cvx-adminer-service",
        "--task-definition", task_arn,
        "--desired-count", "1",
        "--launch-type", "FARGATE",
        "--network-configuration", json.dumps(net),
        "--load-balancers", json.dumps(load_balancers),
        "--health-check-grace-period-seconds", "60",
    ])
    print("Created Adminer service")


def ensure_alb_rule(tg_arn: str) -> None:
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
                    print(f"ALB rule already exists: {rule['RuleArn']}")
                    return

    run([
        "aws", "elbv2", "create-rule",
        "--region", REGION,
        "--listener-arn", LISTENER_ARN,
        "--priority", "10",
        "--conditions", json.dumps([
            {"Field": "path-pattern", "Values": ["/adminer", "/adminer/*"]}
        ]),
        "--actions", json.dumps([
            {
                "Type": "forward",
                "TargetGroupArn": tg_arn,
            }
        ]),
    ])
    print("Created ALB listener rule for /adminer*")


def ensure_cloudfront_behavior() -> None:
    raw = run([
        "aws", "cloudfront", "get-distribution-config",
        "--id", CF_ID,
    ])
    data = json.loads(raw)
    etag = data["ETag"]
    cfg = data["DistributionConfig"]

    behaviors = cfg.get("CacheBehaviors") or {"Quantity": 0, "Items": []}
    items = behaviors.get("Items") or []
    if any(b.get("PathPattern") == "/adminer*" for b in items):
        print("CloudFront behavior /adminer* already exists")
        return

    items.append({
        "PathPattern": "/adminer*",
        "TargetOriginId": ALB_ORIGIN_ID,
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 7,
            "Items": ["HEAD", "GET", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
            "CachedMethods": {"Quantity": 2, "Items": ["HEAD", "GET"]},
        },
        "Compress": True,
        "SmoothStreaming": False,
        "FieldLevelEncryptionId": "",
        "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",  # CachingDisabled
        "OriginRequestPolicyId": "b689b0a8-53d0-40ab-baf2-68738e2966ac",  # AllViewerExceptHostHeader
        "LambdaFunctionAssociations": {"Quantity": 0},
        "FunctionAssociations": {"Quantity": 0},
        "GrpcConfig": {"Enabled": False},
    })
    # Keep API / uploads ahead of default; order among custom behaviors: api, uploads, adminer
    order = {"/api/*": 0, "/uploads/*": 1, "/adminer*": 2}
    items.sort(key=lambda b: order.get(b.get("PathPattern"), 99))
    cfg["CacheBehaviors"] = {"Quantity": len(items), "Items": items}

    infile = os.path.join(os.environ["TEMP"], "cf_adminer.json")
    with open(infile, "w", encoding="utf-8") as f:
        json.dump(cfg, f)

    run([
        "aws", "cloudfront", "update-distribution",
        "--id", CF_ID,
        "--if-match", etag,
        "--distribution-config", f"file://{infile}",
    ])
    print("Added CloudFront behavior /adminer*")


def wait_healthy(tg_arn: str, timeout: int = 300) -> None:
    print("Waiting for Adminer target to become healthy...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        out = json.loads(run([
            "aws", "elbv2", "describe-target-health",
            "--region", REGION,
            "--target-group-arn", tg_arn,
        ]))
        states = [
            t["TargetHealth"]["State"]
            for t in out.get("TargetHealthDescriptions", [])
        ]
        print(f"  target health: {states or ['(none yet)']}")
        if states and all(s == "healthy" for s in states):
            print("Adminer target healthy")
            return
        time.sleep(15)
    print("WARNING: timed out waiting for healthy target — check ECS/ALB console")


def ensure_log_group() -> None:
    run([
        "aws", "logs", "create-log-group",
        "--region", REGION,
        "--log-group-name", "/ecs/cvx-adminer-task",
    ], check=False)


def main() -> None:
    ensure_log_group()
    tg = ensure_target_group()
    ensure_alb_rule(tg)  # associate TG with ALB before creating the service
    task = register_task_definition()
    ensure_service(task, tg)
    ensure_cloudfront_behavior()
    wait_healthy(tg)
    print()
    print("=== Adminer POC ready (after CloudFront finishes deploying) ===")
    print("URL:  https://d15k4r0om4alun.cloudfront.net/adminer/")
    print("Basic Auth:  admin / CvxDbAdmin2026")
    print("In Adminer form:")
    print(f"  System:   PostgreSQL")
    print(f"  Server:   {RDS_HOST}")
    print(f"  Username: slipapp")
    print(f"  Password: Admincvx")
    print(f"  Database: slipreceipt")
    print()
    print("Tear down later: python scripts/teardown_adminer_poc.py")


if __name__ == "__main__":
    main()
