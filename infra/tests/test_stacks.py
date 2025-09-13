import aws_cdk as cdk
import aws_cdk.assertions as assertions
from infra.stacks.etl_stack import EtlStack

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
    
    # Test VPC
    template.resource_count_is("AWS::EC2::VPC", 1)
    
    # Test ECS Cluster
    template.resource_count_is("AWS::ECS::Cluster", 1)
    
    # Test ECS Task Definition
    template.resource_count_is("AWS::ECS::TaskDefinition", 1)
    template.has_resource_properties("AWS::ECS::TaskDefinition", {
        "Memory": "4096",
        "Cpu": "2048"
    })
    
    # Test SNS Topic
    template.resource_count_is("AWS::SNS::Topic", 1)
    
    # Test EventBridge Rule
    template.resource_count_is("AWS::Events::Rule", 1)
    
    # Test IAM Roles
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [{
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                }
            }]
        }
    })