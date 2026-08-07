"""Register a new ECS task definition revision with production env vars,
then update the service.

Set secrets via environment before running (do not commit credentials):

  set DATABASE_URL=postgresql://...
  set NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
  set NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=...
  python scripts/fix_ecs_env.py
"""
import json
import os
import subprocess
import sys
import tempfile

REGION = os.getenv("AWS_REGION", "ap-southeast-2")
FAMILY = os.getenv("ECS_TASK_DEFINITION", "cvx-slip-receipt-task")
CLUSTER = os.getenv("ECS_CLUSTER", "cvx-slip-receipt-cluster")
SERVICE = os.getenv("ECS_SERVICE", "cvx-slip-receipt-service")

REQUIRED = ("DATABASE_URL",)
OPTIONAL_DEFAULTS = {
    "PORT": "3001",
    "RELOAD": "0",
    "AWS_REGION": REGION,
    "S3_BUCKET": "classify-docs-047750375159-ap-southeast-2-an",
    "AI_PROVIDER": "bedrock",
    "AI_MODEL": "amazon.nova-lite-v1:0",
    "BEDROCK_REGION": REGION,
    "AI_TIMEOUT": "30",
}


def run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def env_value(name: str) -> str | None:
    aliases = {
        "NEXT_PUBLIC_SUPABASE_URL": ("NEXT_PUBLIC_SUPABASE_URL", "VITE_SUPABASE_URL", "SUPABASE_URL"),
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY": (
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
            "VITE_SUPABASE_ANON_KEY",
            "SUPABASE_ANON_KEY",
        ),
    }
    for key in aliases.get(name, (name,)):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return None


def build_environment() -> list[dict[str, str]]:
    missing = [name for name in REQUIRED if not env_value(name)]
    if missing:
        print(f"Missing required env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    variables: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(name: str, value: str) -> None:
        if name not in seen and value:
            variables.append({"name": name, "value": value})
            seen.add(name)

    for name in REQUIRED:
        add(name, env_value(name) or "")

    for name, default in OPTIONAL_DEFAULTS.items():
        add(name, os.getenv(name, default).strip())

    for name in (
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        "AI_API_KEY",
        "AI_BASE_URL",
    ):
        value = env_value(name)
        if value:
            add(name, value)

    return variables


current = json.loads(run([
    "aws", "ecs", "describe-task-definition",
    "--task-definition", FAMILY,
    "--region", REGION,
    "--query", "taskDefinition",
]))

container = current["containerDefinitions"][0]
container["environment"] = build_environment()

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

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
    json.dump(register_input, f)
    infile = f.name

registered = json.loads(run([
    "aws", "ecs", "register-task-definition",
    "--region", REGION,
    "--cli-input-json", f"file://{infile}",
]))
new_arn = registered["taskDefinition"]["taskDefinitionArn"]
print(f"Registered: {new_arn}")
print("Environment:")
for item in container["environment"]:
    masked = item["value"]
    if any(s in item["name"] for s in ("URL", "KEY", "PASSWORD", "SECRET")):
        masked = "***"
    print(f"  {item['name']}={masked}")

run([
    "aws", "ecs", "update-service",
    "--region", REGION,
    "--cluster", CLUSTER,
    "--service", SERVICE,
    "--task-definition", new_arn,
])
print("Service update started")
