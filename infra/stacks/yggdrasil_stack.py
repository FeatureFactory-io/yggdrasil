"""Yggdrasil infrastructure stack — VPC, EB, RDS (skeleton)."""

from aws_cdk import CfnOutput, Stack
from constructs import Construct


class YggdrasilStack(Stack):
    """CDK stack placeholder — extend with VPC, EB, RDS per DCI-03..05."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # DCI-03..05: add ec2.Vpc, rds.DatabaseInstance, elasticbeanstalk.CfnEnvironment
        CfnOutput(self, "Status", value="CDK scaffold ready — deploy stacks in DCI-07")
