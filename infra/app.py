#!/usr/bin/env python3
"""AWS CDK app for Yggdrasil — Elastic Beanstalk + RDS."""

import aws_cdk as cdk
from stacks.yggdrasil_stack import YggdrasilStack

app = cdk.App()
YggdrasilStack(
    app,
    "YggdrasilStack",
    env=cdk.Environment(account=cdk.Aws.ACCOUNT_ID, region="us-east-1"),
)
app.synth()
