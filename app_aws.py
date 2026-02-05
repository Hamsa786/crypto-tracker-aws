from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
from datetime import datetime, timedelta
import os
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import threading
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-later')

# CoinGecko API Base URL
COINGECKO_API = "https://api.coingecko.com/api/v3"

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS Services
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns = boto3.client('sns', region_name=AWS_REGION)

# DynamoDB Table Names
USERS_TABLE = 'CryptoTracker_Users'
WATCHLISTS_TABLE = 'CryptoTracker_Watchlists'
ALERTS_TABLE = 'CryptoTracker_Alerts'
PRICES_TABLE = 'CryptoTracker_MarketPrices'

# Cache variables - per crypto caching
price_cache = {}
cache_timestamps = {}
CACHE_DURATION = 30  # Increased to 30 seconds to reduce API calls

# Rate limiting
last_api_call = None
MIN_API_INTERVAL = 2.5  # 2.5 seconds between API calls to respect rate limits
api_lock = threading.Lock()

# Helper function to convert float to Decimal for DynamoDB
def float_to_decimal(obj):
    """Convert float to Decimal for DynamoDB"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [float_to_decimal(v) for v in obj]
    return obj

# Helper function to convert Decimal to float
def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(v) for v in obj]
    return obj

# DynamoDB Operations - Users
def create_user_dynamodb(username, password, email):
    """Create user in DynamoDB"""
    try:
        table = dynamodb.Table(USERS_TABLE)
        table.put_item(
            Item={
                'username': username,
                'password': password,  # In production, hash this!
                'email': email,
                'created_at': datetime.now().isoformat()
            },
            ConditionExpression='attribute_not_exists(username)'
        )
        return True, "User created successfully"
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False, "Username already exists"
        return False, str(e)

def get_user_dynamodb(username):
    """Get user from DynamoDB"""
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'username': username})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting user: {e}")
        return None

def verify_user_dynamodb(username, password):
    """Verify user credentials"""
    user = get_user_dynamodb(username)
    if user and user.get('password') == password:
        return True
    return False

# DynamoDB Operations - Watchlists
def get_user_watchlist_dynamodb(username):
    """Get user's watchlist from DynamoDB"""
    try:
        table = dynamodb.Table(WATCHLISTS_TABLE)
        response = table.get_item(Key={'username': username})
        item = response.get('Item', {})
        return item.get('cryptos', [])
    except ClientError as e:
        print(f"Error getting watchlist: {e}")
        return []

def add_to_watchlist_dynamodb(username, crypto_id):
    """Add crypto to watchlist in DynamoDB"""
    try:
        table = dynamodb.Table(WATCHLISTS_TABLE)
        response = table.get_item(Key={'username': username})
        
        if 'Item' in response:
            cryptos = response['Item'].get('cryptos', [])
            if crypto_id in cryptos:
                return False, "Already in watchlist"
            cryptos.append(crypto_id)
        else:
            cryptos = [crypto_id]
        
        table.put_item(Item={'username': username, 'cryptos': cryptos})
        return True, "Added to watchlist"
    except ClientError as e:
        return False, str(e)

def remove_from_watchlist_dynamodb(username, crypto_id):
    """Remove crypto from watchlist in DynamoDB"""
    try:
        table = dynamodb.Table(WATCHLISTS_TABLE)
        response = table.get_item(Key={'username': username})
        
        if 'Item' in response:
            cryptos = response['Item'].get('cryptos', [])
            if crypto_id in cryptos:
                cryptos.remove(crypto_id)
                table.put_item(Item={'username': username, 'cryptos': cryptos})
                return True, "Removed from watchlist"
        return False, "Not in watchlist"
    except ClientError as e:
        return False, str(e)

# DynamoDB Operations - Alerts
def create_alert_dynamodb(username, crypto_id, threshold, condition):
    """Create alert in DynamoDB"""
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        alert_id = f"{username}_{crypto_id}_{int(datetime.now().timestamp())}"
        
        alert = {
            'alert_id': alert_id,
            'username': username,
            'crypto_id': crypto_id,
            'threshold': float_to_decimal(threshold),
            'condition': condition,
            'active': True,
            'created_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=alert)
        return True, decimal_to_float(alert)
    except ClientError as e:
        return False, str(e)

def get_user_alerts_dynamodb(username):
    """Get user's alerts from DynamoDB"""
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        response = table.query(
            IndexName='username-index',
            KeyConditionExpression='username = :username',
            ExpressionAttributeValues={':username': username}
        )
        return decimal_to_float(response.get('Items', []))
    except ClientError as e:
        print(f"Error getting alerts: {e}")
        # If index doesn't exist, scan table (less efficient)
        try:
            response = table.scan(
                FilterExpression='username = :username',
                ExpressionAttributeValues={':username': username}
            )
            return decimal_to_float(response.get('Items', []))
        except:
            return []

def delete_alert_dynamodb(alert_id):
    """Delete alert from DynamoDB"""
    try:
        table = dynamodb.Table(ALERTS_TABLE)
        table.delete_item(Key={'alert_id': alert_id})
        return True, "Alert deleted"
    except ClientError as e:
        return False, str(e)

# DynamoDB Operations - Market Prices
def save_price_dynamodb(crypto_id, price_data):
    """Save price to DynamoDB"""
    try:
        table = dynamodb.Table(PRICES_TABLE)
        timestamp = datetime.now().isoformat()
        
        item = {
            'crypto_id': crypto_id,
            'timestamp': timestamp,
            'price': float_to_decimal(price_data.get('usd', 0)),
            'market_cap': float_to_decimal(price_data.get('usd_market_cap', 0)),
            'change_24h': float_to_decimal(price_data.get('usd_24h_change', 0))
        }
        
        table.put_item(Item=item)
        return True
    except ClientError as e:
        print(f"Error saving price: {e}")
        return False

# SNS Notification
def send_alert_notification(username, message):
    """Send SNS notification for price alert"""
    try:
        # Get user to retrieve phone/email for SNS
        user = get_user_dynamodb(username)
        if user and 'email' in user:
            # In production, you would create SNS topic and subscribe user's email
            print(f"Alert for {username}: {message}")
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:881490086317:CryptoTrackerAlerts',
                Message=message,
                Subject='Crypto Price Alert'
            )
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

# Helper function to fetch crypto prices with rate limiting and per-crypto caching
def fetch_crypto_prices(crypto_ids=['bitcoin', 'ethereum', 'cardano', 'solana', 'dogecoin'], force_fresh=False):
    """Fetch current prices with per-crypto caching and rate limiting"""
    global price_cache, cache_timestamps, last_api_call
    
    result = {}
    cryptos_to_fetch = []
    
    # Check which cryptos need fresh data
    for crypto_id in crypto_ids:
        if not force_fresh and crypto_id in price_cache and crypto_id in cache_timestamps:
            age = datetime.now() - cache_timestamps[crypto_id]
            if age < timedelta(seconds=CACHE_DURATION):
                result[crypto_id] = price_cache[crypto_id]
                print(f"Using cached data for {crypto_id} (age: {age.seconds}s)")
                continue
        cryptos_to_fetch.append(crypto_id)
    
    # Fetch fresh data for cryptos that need it
    if cryptos_to_fetch:
        with api_lock:
            # Rate limiting - wait if needed
            if last_api_call:
                time_since_last = (datetime.now() - last_api_call).total_seconds()
                if time_since_last < MIN_API_INTERVAL:
                    wait_time = MIN_API_INTERVAL - time_since_last
                    print(f"Rate limiting: waiting {wait_time:.2f}s before API call")
                    time.sleep(wait_time)
            
            try:
                ids = ','.join(cryptos_to_fetch)
                url = f"{COINGECKO_API}/simple/price"
                params = {
                    'ids': ids,
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_market_cap': 'true'
                }
                print(f"Fetching fresh prices for: {ids}")
                response = requests.get(url, params=params, timeout=10)
                last_api_call = datetime.now()
                
                if response.status_code == 429:
                    print("⚠️ Rate limited by CoinGecko API!")
                    # Return cached data if available
                    for crypto_id in cryptos_to_fetch:
                        if crypto_id in price_cache:
                            result[crypto_id] = price_cache[crypto_id]
                    return result
                
                response.raise_for_status()
                fresh_data = response.json()
                
                # Update cache with fresh data and save to DynamoDB
                for crypto_id, data in fresh_data.items():
                    price_cache[crypto_id] = data
                    cache_timestamps[crypto_id] = datetime.now()
                    result[crypto_id] = data
                    print(f"✅ Fresh data for {crypto_id}: ${data.get('usd', 'N/A')}")
                    
                    # Save to DynamoDB
                    save_price_dynamodb(crypto_id, data)
                    
            except requests.exceptions.Timeout:
                print(f"⚠️ Timeout fetching prices")
                # Return whatever we have in cache
                for crypto_id in cryptos_to_fetch:
                    if crypto_id in price_cache:
                        result[crypto_id] = price_cache[crypto_id]
            except Exception as e:
                print(f"Error fetching prices: {e}")
                # Return whatever we have in cache for the requested cryptos
                for crypto_id in cryptos_to_fetch:
                    if crypto_id in price_cache:
                        result[crypto_id] = price_cache[crypto_id]
    
    return result

# Routes
@app.route('/')
def index():
    """Homepage showing real-time cryptocurrency prices"""
    return render_template('index.html')

@app.route('/api/prices')
def get_prices():
    """API endpoint to fetch current crypto prices"""
    crypto_ids = request.args.get('ids', 'bitcoin,ethereum,cardano,solana,dogecoin').split(',')
    prices = fetch_crypto_prices(crypto_ids)
    return jsonify(prices)

@app.route('/test-api')
def test_api():
    """Test if CoinGecko API is working"""
    prices = fetch_crypto_prices()
    return jsonify({
        'prices': prices,
        'cached': {k: v.isoformat() for k, v in cache_timestamps.items()}
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        success, message = create_user_dynamodb(username, password, email)
        if success:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=message)
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_user_dynamodb(username, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard with watchlist"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user_watchlist = get_user_watchlist_dynamodb(username)
    
    return render_template('dashboard.html', username=username, watchlist=user_watchlist)

@app.route('/historical')
def historical():
    """Historical data visualization page"""
    return render_template('historical.html')

@app.route('/api/watchlist/add', methods=['POST'])
def add_to_watchlist():
    """Add cryptocurrency to user's watchlist"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in', 'success': False}), 401
    
    username = session['username']
    crypto_id = request.json.get('crypto_id')
    
    if not crypto_id:
        return jsonify({'success': False, 'message': 'No crypto specified'})
    
    success, message = add_to_watchlist_dynamodb(username, crypto_id)
    
    if success:
        # Try to fetch the price for the newly added crypto
        crypto_data = {}
        try:
            # First check cache
            if crypto_id in price_cache and crypto_id in cache_timestamps:
                age = datetime.now() - cache_timestamps[crypto_id]
                if age < timedelta(seconds=CACHE_DURATION):
                    crypto_data = price_cache[crypto_id]
                    print(f"Using cached data for {crypto_id}")
                else:
                    fresh_prices = fetch_crypto_prices([crypto_id])
                    crypto_data = fresh_prices.get(crypto_id, {})
            else:
                fresh_prices = fetch_crypto_prices([crypto_id])
                crypto_data = fresh_prices.get(crypto_id, {})
        except Exception as e:
            print(f"Error fetching price for {crypto_id}: {e}")
            # Check if we have any cached data
            if crypto_id in price_cache:
                crypto_data = price_cache[crypto_id]
        
        return jsonify({
            'success': True,
            'message': message,
            'crypto_data': {crypto_id: crypto_data} if crypto_data else {},
            'from_cache': crypto_id in price_cache and bool(crypto_data)
        })
    
    return jsonify({'success': False, 'message': message})

@app.route('/api/watchlist/remove', methods=['POST'])
def remove_from_watchlist():
    """Remove cryptocurrency from user's watchlist"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in', 'success': False}), 401
    
    username = session['username']
    crypto_id = request.json.get('crypto_id')
    
    success, message = remove_from_watchlist_dynamodb(username, crypto_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/watchlist')
def get_watchlist():
    """Get user's watchlist with current prices"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    user_watchlist = get_user_watchlist_dynamodb(username)
    
    if user_watchlist:
        prices = fetch_crypto_prices(user_watchlist)
        return jsonify(prices)
    
    return jsonify({})

@app.route('/api/alerts/create', methods=['POST'])
def create_alert():
    """Create a price alert"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.json
    
    success, alert = create_alert_dynamodb(
        username,
        data.get('crypto_id'),
        data.get('threshold'),
        data.get('condition')
    )
    
    if success:
        return jsonify({'success': True, 'alert': alert})
    return jsonify({'success': False, 'message': 'Error creating alert'})

@app.route('/api/alerts')
def get_alerts():
    """Get user's active alerts"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    user_alerts = get_user_alerts_dynamodb(username)
    return jsonify(user_alerts)

@app.route('/api/alerts/delete', methods=['POST'])
def delete_alert():
    """Delete a price alert"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    alert_id = request.json.get('alert_id')
    success, message = delete_alert_dynamodb(alert_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/alerts/check')
def check_alerts():
    """Check if any alerts have been triggered"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    user_alerts = get_user_alerts_dynamodb(username)
    triggered = []
    
    for alert in user_alerts:
        if not alert.get('active'):
            continue
        
        prices = fetch_crypto_prices([alert['crypto_id']])
        if alert['crypto_id'] in prices:
            current_price = prices[alert['crypto_id']]['usd']
            
            if alert['condition'] == 'above' and current_price >= float(alert['threshold']):
                message = f"{alert['crypto_id'].capitalize()} is now ${current_price:,.2f} (above ${float(alert['threshold']):,.2f})"
                triggered.append({
                    'alert': alert,
                    'current_price': current_price,
                    'message': message
                })
                send_alert_notification(username, message)
            elif alert['condition'] == 'below' and current_price <= float(alert['threshold']):
                message = f"{alert['crypto_id'].capitalize()} is now ${current_price:,.2f} (below ${float(alert['threshold']):,.2f})"
                triggered.append({
                    'alert': alert,
                    'current_price': current_price,
                    'message': message
                })
                send_alert_notification(username, message)
    
    return jsonify(triggered)

@app.route('/api/historical')
def get_historical():
    """Get historical price data for a cryptocurrency"""
    global last_api_call
    
    crypto = request.args.get('crypto', 'bitcoin')
    days = request.args.get('days', '7')
    
    # Rate limiting - wait if needed
    with api_lock:
        if last_api_call:
            time_since_last = (datetime.now() - last_api_call).total_seconds()
            if time_since_last < MIN_API_INTERVAL:
                wait_time = MIN_API_INTERVAL - time_since_last
                print(f"Rate limiting historical API: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        
        try:
            url = f"{COINGECKO_API}/coins/{crypto}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily' if int(days) > 1 else 'hourly'
            }
            
            print(f"Fetching historical data for {crypto}, {days} days")
            response = requests.get(url, params=params, timeout=10)
            last_api_call = datetime.now()
            
            if response.status_code == 429:
                print("⚠️ Rate limited by CoinGecko API on historical endpoint!")
                return jsonify({
                    'error': 'Rate limit reached. Please wait a moment and try again.',
                    'prices': []
                }), 429
            
            response.raise_for_status()
            data = response.json()
            
            return jsonify(data)
        except requests.exceptions.Timeout:
            print(f"⚠️ Timeout fetching historical data for {crypto}")
            return jsonify({
                'error': 'Request timed out. Please try again.',
                'prices': []
            }), 500
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return jsonify({
                'error': str(e),
                'prices': []
            }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
