"""Fix the task role S3 policy: it referenced a bucket name with a
duplicated account-id suffix that doesn't exist. Point it at the real
upload bucket.
"""
import json
import os
import subprocess
import sys

POLICY_ARN = (
    "arn:aws:iam::047750375159:policy/"
    "cvx-slip-receipt-role-for-task-definitionPolicy"
)
BUCKET = "cvx-slip-receipt-bucket-047750375159-ap-southeast-2-an"

document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
            ],
            "Resource": [
                f"arn:aws:s3:::{BUCKET}",
                f"arn:aws:s3:::{BUCKET}/*",
            ],
        }
    ],
}

infile = os.path.join(os.environ["TEMP"], "task_policy.json")
with open(infile, "w", encoding="utf-8") as f:
    json.dump(document, f)

result = subprocess.run(
    [
        "aws", "iam", "create-policy-version",
        "--policy-arn", POLICY_ARN,
        "--policy-document", f"file://{infile}",
        "--set-as-default",
    ],
    capture_output=True, text=True, shell=True,
)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)
print("IAM policy updated")
