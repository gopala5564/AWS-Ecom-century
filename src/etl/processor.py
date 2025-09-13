"""ETL Processor for data transformation."""

import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

class EtlProcessor:
    """Handles ETL operations using AWS services."""
    
    def __init__(self):
        """Initialize AWS clients and environment variables."""
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.client('dynamodb')
        self.sns = boto3.client('sns')
        
        # Get environment variables
        self.raw_bucket = os.environ['RAW_BUCKET']
        self.processed_bucket = os.environ['PROCESSED_BUCKET']
        self.metadata_table = os.environ['METADATA_TABLE']
        self.notification_topic = os.environ['NOTIFICATION_TOPIC']

    def process_data(self):
        """Main ETL processing logic."""
        try:
            # List objects in raw bucket
            response = self.s3.list_objects_v2(Bucket=self.raw_bucket)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    self._process_single_file(obj['Key'])
                    
            return {"statusCode": 200, "body": "ETL process completed successfully"}
            
        except Exception as e:
            error_message = f"Error in ETL process: {str(e)}"
            self.send_notification(error_message)
            raise Exception(error_message)

    def _process_single_file(self, raw_key: str):
        """Process a single file from raw to processed bucket."""
        processed_key = f"processed_{raw_key}"
        
        # Get raw data
        raw_data = self.s3.get_object(
            Bucket=self.raw_bucket, 
            Key=raw_key
        )['Body'].read()
        
        # Transform data
        processed_data = self.transform_data(raw_data)
        
        # Save processed data
        self.s3.put_object(
            Bucket=self.processed_bucket,
            Key=processed_key,
            Body=processed_data
        )
        
        # Update metadata
        self.update_metadata(raw_key, processed_key)
        
        # Send notification
        self.send_notification(f"Processed file: {raw_key}")

    def transform_data(self, data: bytes) -> bytes:
        """Transform the input data. Override this method for specific transformations."""
        return data

    def update_metadata(self, raw_key: str, processed_key: str):
        """Update processing metadata in DynamoDB."""
        timestamp = datetime.utcnow().isoformat()
        self.dynamodb.put_item(
            TableName=self.metadata_table,
            Item={
                'id': {'S': raw_key},
                'timestamp': {'S': timestamp},
                'processed_file': {'S': processed_key},
                'status': {'S': 'completed'}
            }
        )

    def send_notification(self, message: str):
        """Send SNS notification."""
        self.sns.publish(
            TopicArn=self.notification_topic,
            Message=message
        )

def main():
    """Main entry point."""
    processor = EtlProcessor()
    processor.process_data()

if __name__ == "__main__":
    main()