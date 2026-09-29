# Deploying the reference AWS architecture

`infra/agrichain-stack.yaml` (CloudFormation) builds the architecture diagram in `assets/cloud_archetec_lastversion.png`.
`infra/deploy.py` packages the code and deploys the stack. Nothing has to be created by hand in the console.

## Diagram vs. what gets deployed

| Diagram | Deployed | Note |
|---|---|---|
| VPC, Region, 2 AZs | Custom VPC `10.0.0.0/16`, 2 public + 2 private subnets | Replaces the Default VPC |
| Internet Gateway | Yes | Public route table |
| Application Load Balancer | Yes, HTTP :80 -> target group :3000 | Sticky sessions on, health check `/healthz` |
| Auto Scaling group, EC2 in 2 public subnets | Yes, 2 instances (min 1, max 4, CPU target 60%) | Each instance runs the Express web server **and** the FastAPI AI agent |
| Amazon Redshift + subnet group in private subnets | **Amazon RDS PostgreSQL** in private subnets, DB subnet group over both AZs | Redshift is not usable in Learner Lab; RDS was already the chosen substitute. Second private subnet is the failover reserve (`DBMultiAZ=true` if your account allows it) |
| DynamoDB (user login & session) | Yes: `*_user_login`, `*_user_session` (TTL), `*_chat_history` | Passwords hashed with scrypt; the API verifies the session on every call |
| S3 (CSV file) | Yes, private bucket, prefix `csv-uploads/` | |
| Event Trigger -> Step Functions | S3 -> EventBridge rule -> Step Functions state machine | S3 cannot start a state machine directly; EventBridge is the supported bridge |
| AWS Lambda -> Load data | Lambda **inside the private subnets** | Reaches S3 and DynamoDB through free gateway endpoints, so no NAT gateway is needed |

Skipped because of Learner Lab limits or cost: NAT gateway, Redshift, HTTPS/ACM certificate (ALB is HTTP only),
Multi-AZ RDS by default, and any IAM role creation (`LabRole` / `LabInstanceProfile` are reused).

## Deploy

Prerequisites: Python 3 with `pip install boto3`, and the credentials from the Learner Lab **AWS Details** panel
(`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) exported in your shell.

```bash
python infra/deploy.py --groq-key gsk_xxxxxxxx --admin-password "ChooseALoginPass1"
```

Optional flags: `--admin-username`, `--key-name vockey` (SSH), `--ssh-cidr x.x.x.x/32`, `--capacity 1`.

The script stores the Groq key and a generated DB password in SSM Parameter Store, uploads the app and the
Lambda package to an artifacts bucket, and creates the stack (about 15 minutes, mostly RDS). It prints
`WebsiteUrl`; wait ~5 more minutes for the instances to install and pass the ALB health check.

On the first deploy a CloudFormation custom resource runs inside the VPC to create the `data_warehouse` schema,
all tables, `dim_date` (2015-2035 plus the 9999-12-31 sentinel) and the first login user.

Re-run the same command after a code change: a new zip name makes CloudFormation update the launch template.
Existing instances are not replaced automatically; terminate them (ASG starts fresh ones) or run
`aws autoscaling start-instance-refresh --auto-scaling-group-name agrichain-asg`.

## Use it

1. Open `WebsiteUrl`, log in with the admin user.
2. Upload the CSVs in this order (dimension files first): Crop, Farmer, Warehouse, Customer, then Harvest,
   Sales, Shipment, Inventory. File names must contain those words.
3. Each upload starts a Step Functions execution. Watch it in the console under Step Functions -> `agrichain-etl`
   (a fact file that references a dimension that has not been loaded fails with a clear message in the execution).
4. Ask the AI assistant questions; it queries RDS through the SQL guardrails.

## Operations

* **Query the private RDS**: it has no public address. Use SSM Session Manager or SSH to an instance, then
  `psql "host=<RdsEndpoint> user=admin_agri dbname=postgres sslmode=require"` (password: SSM `/agrichain/db_password`).
* **Web/AI logs**: `journalctl -u agrichain-web -u agrichain-ai`; bootstrap log `/var/log/agrichain-bootstrap.log`.
* **ETL logs**: CloudWatch log group `/aws/lambda/agrichain-etl`.
* **Tear down**: empty the CSV bucket and the artifacts bucket, then delete the stack `agrichain`.

## Known Learner Lab risks

* The rule that starts Step Functions and the state machine both use `LabRole`. If a lab's `LabRole` trust policy
  rejects `events.amazonaws.com`, stack creation fails on `CsvUploadRule`; the fallback is an S3 notification to a
  tiny Lambda that calls `StartExecution`.
* Lab sessions end and the account can be recycled. Everything is reproducible by re-running `deploy.py`, but the
  data is not: the RDS instance is deleted with the stack.
* Groq (the LLM) is reached over the internet from the public subnets; that is why the EC2 instances keep public IPs.
