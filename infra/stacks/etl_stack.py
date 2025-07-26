from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_ecr_assets as ecr_assets,
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

        # Lambda for ETL processing using container image
        etl_lambda = lambda_.DockerImageFunction(
            self, "EtlProcessor",
            code=lambda_.DockerImageCode.from_image_asset(
                directory=".",
                file="Dockerfile"
            ),
            timeout=Duration.minutes(15),
            memory_size=1024,
            environment={
                "RAW_BUCKET": raw_bucket.bucket_name,
                "PROCESSED_BUCKET": processed_bucket.bucket_name,
                "METADATA_TABLE": etl_metadata_table.table_name,
                "NOTIFICATION_TOPIC": notification_topic.topic_arn
            }
        )

        # Grant permissions
        raw_bucket.grant_read(etl_lambda)
        processed_bucket.grant_write(etl_lambda)
        etl_metadata_table.grant_read_write_data(etl_lambda)
        notification_topic.grant_publish(etl_lambda)

        # EventBridge rule to trigger ETL
        schedule = events.Rule(
            self, "EtlSchedule",
            schedule=events.Schedule.rate(Duration.hours(1))
        )
        schedule.add_target(targets.LambdaFunction(etl_lambda))
