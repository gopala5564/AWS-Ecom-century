import aws_cdk as cdk
import aws_cdk.assertions as assertions
from infra.stacks.main_stack import MainStack
from infra.stacks.etl_stack import EtlStack

def test_main_stack_creates_resources():
    app = cdk.App()
    stack = MainStack(app, "TestMainStack")
    template = assertions.Template.from_stack(stack)
    
    # Add assertions here for main stack resources

def test_etl_stack_creates_resources():
    app = cdk.App()
    stack = EtlStack(app, "TestEtlStack")
    template = assertions.Template.from_stack(stack)
    
    # Test S3 buckets
    template.resource_count_is("AWS::S3::Bucket", 2)
    
    # Test DynamoDB table
    template.resource_count_is("AWS::DynamoDB::Table", 1)
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "BillingMode": "PAY_PER_REQUEST"
    })
    
    # Test Lambda function
    template.resource_count_is("AWS::Lambda::Function", 1)
    
    # Test SNS Topic
    template.resource_count_is("AWS::SNS::Topic", 1)
    
    # Test EventBridge Rule
    template.resource_count_is("AWS::Events::Rule", 1)
