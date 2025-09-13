import os
import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

class EtlProcessor:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.client('dynamodb')
        self.sns = boto3.client('sns')
        
        # Get environment variables
        self.raw_bucket = os.environ['RAW_BUCKET']
        self.processed_bucket = os.environ['PROCESSED_BUCKET']
        self.metadata_table = os.environ['METADATA_TABLE']
        self.notification_topic = os.environ['NOTIFICATION_TOPIC']

    def process_data(self):
        try:
            # List objects in raw bucket
            response = self.s3.list_objects_v2(Bucket=self.raw_bucket)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Process each file
                    raw_key = obj['Key']
                    processed_key = f"processed_{raw_key}"
                    
                    # Get raw data
                    raw_data = self.s3.get_object(
                        Bucket=self.raw_bucket, 
                        Key=raw_key
                    )['Body'].read()
                    
                    # Transform data (add your transformation logic here)
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
                    
            return {"statusCode": 200, "body": "ETL process completed successfully"}
            
        except Exception as e:
            error_message = f"Error in ETL process: {str(e)}"
            self.send_notification(error_message)
            raise Exception(error_message)

    def transform_data(self, data):
        # Add your data transformation logic here
        # This is a placeholder that returns the data unchanged
        return data

    def update_metadata(self, raw_key, processed_key):
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

    def send_notification(self, message):
        self.sns.publish(
            TopicArn=self.notification_topic,
            Message=message
        )

def main():
    processor = EtlProcessor()
    processor.process_data()

if __name__ == "__main__":
    main()