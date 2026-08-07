"""Register a task definition revision pointing at a new image digest
(keeping the env vars from the current revision) and update the service.
"""
import json
import os
import subprocess
import sys

REGION = "ap-southeast-2"
FAMILY = "cvx-slip-receipt-task"
CLUSTER = "cvx-slip-receipt-cluster"
SERVICE = "cvx-slip-receipt-service"
IMAGE = (
    "047750375159.dkr.ecr.ap-southeast-2.amazonaws.com/cvx-slip-receipt"
    "@sha256:71e0c1e43e474312f35e1f798ab33e2b614f749912b55e7d57b3ba4b3772be06"
)


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)
    return result.stdout


current = json.loads(run([
    "aws", "ecs", "describe-task-definition",
    "--task-definition", FAMILY,
    "--region", REGION,
    "--query", "taskDefinition",
]))

current["containerDefinitions"][0]["image"] = IMAGE

register_input = {
    key: current[key]
    for key in (
        "family", "taskRoleArn", "executionRoleArn", "networkMode",
        "containerDefinitions", "requiresCompatibilities", "cpu", "memory",
    )
    if key in current
}
if "runtimePlatform" in current:
    register_input["runtimePlatform"] = current["runtimePlatform"]

infile = os.path.join(os.environ["TEMP"], "taskdef_img.json")
with open(infile, "w", encoding="utf-8") as f:
    json.dump(register_input, f)

registered = json.loads(run([
    "aws", "ecs", "register-task-definition",
    "--region", REGION,
    "--cli-input-json", f"file://{infile}",
]))
new_arn = registered["taskDefinition"]["taskDefinitionArn"]
print(f"Registered: {new_arn}")

run([
    "aws", "ecs", "update-service",
    "--region", REGION,
    "--cluster", CLUSTER,
    "--service", SERVICE,
    "--task-definition", new_arn,
])
print("Service update started")
