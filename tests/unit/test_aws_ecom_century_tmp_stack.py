import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_ecom_century_tmp.aws_ecom_century_tmp_stack import AwsEcomCenturyTmpStack

# example tests. To run these tests, uncomment this file along with the example as show below
# resource in aws_ecom_century_tmp/aws_ecom_century_tmp_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsEcomCenturyTmpStack(app, "aws-ecom-century-tmp")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
