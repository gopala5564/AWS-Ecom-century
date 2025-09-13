"""CDK Stack for ETL infrastructure."""

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
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_ecs as ecs,
)

class EtlStack(Stack):
    """AWS CDK Stack for ETL infrastructure."""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._create_storage()
        self._create_vpc()
        self._create_ecs_resources()
        self._create_scheduler()

    def _create_storage(self):
        """Create S3 buckets, DynamoDB table, and SNS topic."""
        # S3 Buckets with encryption
        self.raw_bucket = s3.Bucket(
            self, "RawDataBucket",
            bucket_name="raw-data-bucket-ecom-century",
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True
        )

        self.processed_bucket = s3.Bucket(
            self, "ProcessedDataBucket",
            bucket_name="processed-data-bucket-ecom-century",
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True
        )

        # DynamoDB table with encryption
        self.metadata_table = dynamodb.Table(
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
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )

        # SNS Topic
        self.notification_topic = sns.Topic(
            self, "EtlNotificationTopic",
            topic_name="etl-notifications"
        )

    def _create_vpc(self):
        """Create VPC with public and private subnets."""
        self.vpc = ec2.Vpc(
            self, "EtlVpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

    def _create_ecs_resources(self):
        """Create ECS cluster and task definition."""
        # Create ECS Cluster
        self.cluster = ecs.Cluster(
            self, "EtlCluster",
            vpc=self.vpc,
            cluster_name="etl-cluster"
        )

        # Task Role
        task_role = iam.Role(
            self, "EtlTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Role for ETL ECS Task"
        )

        # Grant permissions
        self.raw_bucket.grant_read(task_role)
        self.processed_bucket.grant_write(task_role)
        self.metadata_table.grant_read_write_data(task_role)
        self.notification_topic.grant_publish(task_role)

        # Task Definition
        self.task_definition = ecs.FargateTaskDefinition(
            self, "EtlTaskDefinition",
            memory_limit_mib=4096,
            cpu=2048,
            task_role=task_role
        )

        # Add container
        self.task_definition.add_container(
            "EtlContainer",
            image=ecs.ContainerImage.from_asset(
                directory=".",
                file="Dockerfile"
            ),
            environment={
                "RAW_BUCKET": self.raw_bucket.bucket_name,
                "PROCESSED_BUCKET": self.processed_bucket.bucket_name,
                "METADATA_TABLE": self.metadata_table.table_name,
                "NOTIFICATION_TOPIC": self.notification_topic.topic_arn
            },
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="etl-container"
            )
        )

    def _create_scheduler(self):
        """Create EventBridge rule for scheduling."""
        schedule = events.Rule(
            self, "EtlSchedule",
            schedule=events.Schedule.rate(Duration.hours(1))
        )

        schedule.add_target(targets.EcsTask(
            cluster=self.cluster,
            task_definition=self.task_definition,
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            )
        ))
