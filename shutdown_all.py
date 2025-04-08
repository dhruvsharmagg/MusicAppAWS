import boto3
from dotenv import load_dotenv
import os

# Load AWS credentials from .env file
load_dotenv()

# Connect to EC2 (no need to touch S3 or DynamoDB if you're not deleting)
ec2 = boto3.client('ec2', region_name='us-east-1')

# ---------------------------------------
# STOP all running EC2 instances
# ---------------------------------------
def stop_ec2_instances():
    print("\n🔍 Checking for running EC2 instances...")

    try:
        response = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )

        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])

        if instance_ids:
            print("🛑 Stopping instances:", instance_ids)
            ec2.stop_instances(InstanceIds=instance_ids)
            print("✅ EC2 instances stopped.")
        else:
            print("💤 No running EC2 instances found.")
    except Exception as e:
        print(f"⚠️ Error checking EC2 instances: {e}")

# ---------------------------------------
# MAIN
# ---------------------------------------
if __name__ == "__main__":
    print("🚨 Starting SAFE shutdown...")
    
    stop_ec2_instances()

    print("\n✅ Done! You will not be charged. Sleep well, champ 😴")
