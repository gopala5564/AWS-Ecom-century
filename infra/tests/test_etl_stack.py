import aws_cdk as cdk
import aws_cdk.assertions as assertions
from infra.stacks.etl_stack import EtlStack

def test_etl_stack_creates_resources():
    # GIVEN
    app = cdk.App()
    
    # WHEN
    stack = EtlStack(app, "TestEtlStack")
    template = assertions.Template.from_stack(stack)
    
    # THEN
    # Test S3 Buckets
    template.resource_count_is("AWS::S3::Bucket", 2)
    
    # Test DynamoDB Table
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"}
        ]
    })
    
    # Test VPC
    template.resource_count_is("AWS::EC2::VPC", 1)
    
    # Test ECS Task Definition
    template.has_resource_properties("AWS::ECS::TaskDefinition", {
        "RequiresCompatibilities": ["FARGATE"],
        "Memory": "4096",
        "Cpu": "2048"
    })
    
    # Test EventBridge Rule
    template.resource_count_is("AWS::Events::Rule", 1)

def test_etl_stack_security_configuration():
    # GIVEN
    app = cdk.App()
    
    # WHEN
    stack = EtlStack(app, "TestEtlStack")
    template = assertions.Template.from_stack(stack)
    
    # THEN
    # Test S3 Bucket Versioning
    template.has_resource_properties("AWS::S3::Bucket", {
        "VersioningConfiguration": {"Status": "Enabled"}
    })
    
    # Test Task Definition Role
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [{
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": ["ecs-tasks.amazonaws.com"]
                }
            }]
        }
    })
