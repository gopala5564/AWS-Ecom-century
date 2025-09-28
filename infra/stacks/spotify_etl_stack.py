from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
)


class SpotifyEtlStack(Stack):
    """Serverless Spotify ETL stack.

    Resources created:
    - S3 raw and curated buckets
    - DynamoDB metadata table
    - SNS topic for notifications
    - Lambda for OAuth callback (API Gateway)
    - Lambda for ingest worker (scheduled)
    - EventBridge rule to schedule ingest
    """

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 buckets
        raw_bucket = s3.Bucket(
            self,
            "SpotifyRawBucket",
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        curated_bucket = s3.Bucket(
            self,
            "SpotifyCuratedBucket",
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # DynamoDB table
        metadata_table = dynamodb.Table(
            self,
            "SpotifyMetadataTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # SNS topic
        notification_topic = sns.Topic(self, "SpotifyNotificationTopic")

        # IAM role for lambdas
        lambda_role = iam.Role(
            self,
            "SpotifyLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        # permissions to S3 / DynamoDB / SNS
        raw_bucket.grant_read_write(lambda_role)
        curated_bucket.grant_read_write(lambda_role)
        metadata_table.grant_read_write_data(lambda_role)
        notification_topic.grant_publish(lambda_role)

        # OAuth callback Lambda (API Gateway)
        oauth_fn = _lambda.Function(
            self,
            "SpotifyOauthHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="oauth_handler.handler",
            code=_lambda.Code.from_asset("src/etl"),
            environment={
                "RAW_BUCKET": raw_bucket.bucket_name,
                "METADATA_TABLE": metadata_table.table_name,
            },
            role=lambda_role,
            timeout=Duration.seconds(30),
        )

        api = apigw.LambdaRestApi(self, "SpotifyOauthApi", handler=oauth_fn, proxy=False)
        oauth = api.root.add_resource("oauth")
        oauth.add_method("GET")

        # Ingest worker Lambda (scheduled)
        ingest_fn = _lambda.Function(
            self,
            "SpotifyIngestWorker",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="ingest_worker.handler",
            code=_lambda.Code.from_asset("src/etl"),
            environment={
                "RAW_BUCKET": raw_bucket.bucket_name,
                "CURATED_BUCKET": curated_bucket.bucket_name,
                "METADATA_TABLE": metadata_table.table_name,
                "NOTIFICATION_TOPIC": notification_topic.topic_arn,
            },
            role=lambda_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
        )

        # Schedule ingest every hour
        rule = events.Rule(
            self,
            "SpotifyIngestSchedule",
            schedule=events.Schedule.rate(Duration.hours(1)),
        )
        rule.add_target(targets.LambdaFunction(ingest_fn))

        # Expose resource names as outputs (optional)
        self.raw_bucket = raw_bucket
        self.curated_bucket = curated_bucket
        self.metadata_table = metadata_table
        self.notification_topic = notification_topic

*** End Patch