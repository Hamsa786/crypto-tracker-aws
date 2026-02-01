import boto3
from botocore.exceptions import ClientError
import sys

# AWS Configuration
AWS_REGION = 'us-east-1'

# Initialize DynamoDB
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    print(f"✓ Connected to AWS DynamoDB in region: {AWS_REGION}")
except Exception as e:
    print(f"✗ Failed to connect to AWS: {e}")
    print("Please ensure AWS CLI is configured with 'aws configure'")
    sys.exit(1)

def create_users_table():
    """Create Users table"""
    try:
        table = dynamodb.create_table(
            TableName='CryptoTracker_Users',
            KeySchema=[
                {'AttributeName': 'username', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'username', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("⏳ Creating CryptoTracker_Users table...")
        table.wait_until_exists()
        print("✓ CryptoTracker_Users table created successfully!")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("✓ CryptoTracker_Users table already exists")
            return True
        else:
            print(f"✗ Error creating Users table: {e}")
            return False

def create_watchlists_table():
    """Create Watchlists table"""
    try:
        table = dynamodb.create_table(
            TableName='CryptoTracker_Watchlists',
            KeySchema=[
                {'AttributeName': 'username', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'username', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("⏳ Creating CryptoTracker_Watchlists table...")
        table.wait_until_exists()
        print("✓ CryptoTracker_Watchlists table created successfully!")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("✓ CryptoTracker_Watchlists table already exists")
            return True
        else:
            print(f"✗ Error creating Watchlists table: {e}")
            return False

def create_alerts_table():
    """Create Alerts table with Global Secondary Index"""
    try:
        table = dynamodb.create_table(
            TableName='CryptoTracker_Alerts',
            KeySchema=[
                {'AttributeName': 'alert_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'alert_id', 'AttributeType': 'S'},
                {'AttributeName': 'username', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'username-index',
                    'KeySchema': [
                        {'AttributeName': 'username', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("⏳ Creating CryptoTracker_Alerts table with GSI...")
        table.wait_until_exists()
        print("✓ CryptoTracker_Alerts table created successfully!")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("✓ CryptoTracker_Alerts table already exists")
            return True
        else:
            print(f"✗ Error creating Alerts table: {e}")
            return False

def create_market_prices_table():
    """Create MarketPrices table"""
    try:
        table = dynamodb.create_table(
            TableName='CryptoTracker_MarketPrices',
            KeySchema=[
                {'AttributeName': 'crypto_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'crypto_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("⏳ Creating CryptoTracker_MarketPrices table...")
        table.wait_until_exists()
        print("✓ CryptoTracker_MarketPrices table created successfully!")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("✓ CryptoTracker_MarketPrices table already exists")
            return True
        else:
            print(f"✗ Error creating MarketPrices table: {e}")
            return False

def verify_tables():
    """Verify all tables exist and are active"""
    print("\n" + "="*50)
    print("Verifying Tables...")
    print("="*50)
    
    table_names = [
        'CryptoTracker_Users',
        'CryptoTracker_Watchlists',
        'CryptoTracker_Alerts',
        'CryptoTracker_MarketPrices'
    ]
    
    all_active = True
    for table_name in table_names:
        try:
            table = dynamodb.Table(table_name)
            status = table.table_status
            if status == 'ACTIVE':
                print(f"✓ {table_name}: {status}")
            else:
                print(f"⚠ {table_name}: {status}")
                all_active = False
        except Exception as e:
            print(f"✗ {table_name}: NOT FOUND")
            all_active = False
    
    return all_active

if __name__ == '__main__':
    print("="*50)
    print("Creating DynamoDB Tables for CryptoTracker")
    print("="*50)
    print()
    
    # Create all tables
    success_count = 0
    
    if create_users_table():
        success_count += 1
    
    if create_watchlists_table():
        success_count += 1
    
    if create_alerts_table():
        success_count += 1
    
    if create_market_prices_table():
        success_count += 1
    
    # Verify all tables
    if verify_tables():
        print("\n" + "="*50)
        print("✓ All tables created and active!")
        print("="*50)
        print("\nYou can now run: python app_aws.py")
    else:
        print("\n" + "="*50)
        print("⚠ Some tables may not be active yet")
        print("="*50)
        print("Please wait a moment and check AWS Console")
    
    print(f"\n📊 Total tables processed: {success_count}/4")