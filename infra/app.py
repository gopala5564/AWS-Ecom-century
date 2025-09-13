#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.etl_stack import EtlStack

app = cdk.App()
EtlStack(app, "EtlStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    ))

app.synth()