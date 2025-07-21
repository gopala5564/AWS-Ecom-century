import os
import json
import boto3
import datetime
from typing import Dict, Any

def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the raw data according to business rules
    """
    # Add your transformation logic here
    processed_data = data.copy()
    processed_data['processed_timestamp'] = datetime.datetime.now().isoformat()
    return processed_data

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main ETL processor function
    """
    try:
        # Initialize AWS clients
        s3 = boto3.client('s3')
        dynamodb = boto3.client('dynamodb')
        sns = boto3.client('sns')

        raw_bucket = os.environ['RAW_BUCKET']
        processed_bucket = os.environ['PROCESSED_BUCKET']
        metadata_table = os.environ['METADATA_TABLE']
        topic_arn = os.environ['NOTIFICATION_TOPIC']

        # List files in raw bucket
        response = s3.list_objects_v2(Bucket=raw_bucket)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                # Get the raw data
                raw_file = s3.get_object(Bucket=raw_bucket, Key=obj['Key'])
                raw_data = json.loads(raw_file['Body'].read().decode('utf-8'))

                # Process the data
                processed_data = process_data(raw_data)

                # Save processed data
                processed_key = f"processed_{obj['Key']}"
                s3.put_object(
                    Bucket=processed_bucket,
                    Key=processed_key,
                    Body=json.dumps(processed_data)
                )

                # Update metadata
                dynamodb.put_item(
                    TableName=metadata_table,
                    Item={
                        'id': {'S': obj['Key']},
                        'timestamp': {'S': datetime.datetime.now().isoformat()},
                        'status': {'S': 'PROCESSED'},
                        'source_bucket': {'S': raw_bucket},
                        'destination_bucket': {'S': processed_bucket},
                        'processed_key': {'S': processed_key}
                    }
                )

                # Archive or delete the raw file
                s3.delete_object(Bucket=raw_bucket, Key=obj['Key'])

        # Send notification
        sns.publish(
            TopicArn=topic_arn,
            Subject='ETL Process Completed',
            Message=f'ETL process completed successfully at {datetime.datetime.now().isoformat()}'
        )

        return {
            'statusCode': 200,
            'body': json.dumps('ETL process completed successfully')
        }

    except Exception as e:
        error_message = f'Error in ETL process: {str(e)}'
        
        # Send error notification
        sns.publish(
            TopicArn=topic_arn,
            Subject='ETL Process Error',
            Message=error_message
        )

        return {
            'statusCode': 500,
            'body': json.dumps(error_message)
        }
