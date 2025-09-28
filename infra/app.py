#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.etl_stack import EtlStack
from stacks.spotify_etl_stack import SpotifyEtlStack

app = cdk.App()
EtlStack(app, "EtlStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    ))

SpotifyEtlStack(app, "SpotifyEtlStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    ))

app.synth()