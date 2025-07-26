#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_ecom_century_tmp.aws_ecom_century_tmp_stack import AwsEcomCenturyTmpStack
from aws_ecom_century_tmp.etl_stack import EtlStack


app = cdk.App()
AwsEcomCenturyTmpStack(app, "AwsEcomCenturyTmpStack")
EtlStack(app, "EtlStack",
        env=cdk.Environment(
            account=os.getenv('CDK_DEFAULT_ACCOUNT'),
            region=os.getenv('CDK_DEFAULT_REGION')
        ))

app.synth()
