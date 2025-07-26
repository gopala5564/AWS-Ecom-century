from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
    DockerImageAsset
)

class EtlStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Buckets
        raw_bucket = s3.Bucket(
            self, "RawDataBucket",
            bucket_name="raw-data-bucket-ecom-century",
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True
        )

        processed_bucket = s3.Bucket(
            self, "ProcessedDataBucket",
            bucket_name="processed-data-bucket-ecom-century",
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True
        )

        # DynamoDB table for ETL metadata
        etl_metadata_table = dynamodb.Table(
            self, "EtlMetadataTable",
            table_name="etl-metadata",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )

        # SNS Topic for notifications
        notification_topic = sns.Topic(
            self, "EtlNotificationTopic",
            topic_name="etl-notifications"
        )

        # Create ECR repository
        repository = ecr.Repository(
            self, "EtlRepository",
            repository_name="etl-processor-repo",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_images=True
        )

        # Create VPC for ECS
        vpc = ec2.Vpc(
            self, "EtlVpc",
            max_azs=2,
            nat_gateways=1
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(
            self, "EtlCluster",
            vpc=vpc,
            cluster_name="etl-cluster"
        )

        # Task Role for ECS
        task_role = iam.Role(
            self, "EtlTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Role for ETL ECS Task"
        )

        # Add necessary permissions to task role
        raw_bucket.grant_read(task_role)
        processed_bucket.grant_write(task_role)
        etl_metadata_table.grant_read_write_data(task_role)
        notification_topic.grant_publish(task_role)

        # Create Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self, "EtlTaskDefinition",
            memory_limit_mib=4096,
            cpu=2048,
            task_role=task_role
        )

        # Add container to task definition
        task_definition.add_container(
            "EtlContainer",
            image=ecs.ContainerImage.from_docker_image_asset(
                DockerImageAsset(
                    self, "EtlDockerImage",
                    directory=".",
                    file="Dockerfile"
                )
            ),
            environment={
                "RAW_BUCKET": raw_bucket.bucket_name,
                "PROCESSED_BUCKET": processed_bucket.bucket_name,
                "METADATA_TABLE": etl_metadata_table.table_name,
                "NOTIFICATION_TOPIC": notification_topic.topic_arn
            },
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="etl-container"
            )
        )

        # EventBridge rule to trigger ETL
        schedule = events.Rule(
            self, "EtlSchedule",
            schedule=events.Schedule.rate(Duration.hours(1))
        )

        # Add ECS Task target
        schedule.add_target(targets.EcsTask(
            cluster=cluster,
            task_definition=task_definition,
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        ))
