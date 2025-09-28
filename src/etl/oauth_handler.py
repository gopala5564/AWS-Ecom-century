import os
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RAW_BUCKET = os.getenv("RAW_BUCKET")
METADATA_TABLE = os.getenv("METADATA_TABLE")


def handler(event, context):
    """Minimal OAuth callback handler for Spotify.

    Expects a query parameter 'code' from Spotify and stores a placeholder
    refresh token in the metadata table or logs it. Real implementation
    should exchange the code for tokens and store securely.
    """
    logger.info("Received OAuth event: %s", event)
    params = event.get("queryStringParameters") or {}
    code = params.get("code")

    if not code:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "missing code"}),
        }

    # TODO: Exchange code for tokens and persist securely (Secrets Manager / DynamoDB)
    logger.info("Received auth code (stub): %s", code)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "ok", "code": code}),
    }
