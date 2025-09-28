import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RAW_BUCKET = os.getenv("RAW_BUCKET")
CURATED_BUCKET = os.getenv("CURATED_BUCKET")
METADATA_TABLE = os.getenv("METADATA_TABLE")
NOTIFICATION_TOPIC = os.getenv("NOTIFICATION_TOPIC")

s3 = boto3.client("s3")
ddb = boto3.client("dynamodb")
sns = boto3.client("sns")


def handler(event, context):
    """Minimal ingest worker that simulates fetching data from Spotify and
    writing a placeholder JSON to the raw S3 bucket.
    """
    logger.info("Ingest worker triggered: %s", event)

    # Create a dummy payload and write to S3
    payload = {"source": "spotify", "data": [], "ts": context.aws_request_id if context else "local"}
    key = f"spotify/raw/{payload['ts']}.json"

    s3.put_object(Bucket=RAW_BUCKET, Key=key, Body=json.dumps(payload).encode("utf-8"))
    logger.info("Wrote dummy payload to s3://%s/%s", RAW_BUCKET, key)

    # Optionally publish a notification
    if NOTIFICATION_TOPIC:
        sns.publish(TopicArn=NOTIFICATION_TOPIC, Message=json.dumps({"s3_key": key}))

    return {"status": "ok", "s3_key": key}
