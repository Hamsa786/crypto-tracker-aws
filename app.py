from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-later'  # Change this in production!

# CoinGecko API Base URL
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Temporary in-memory storage (we'll replace with DynamoDB later)
users = {}
watchlists = {}
market_prices = []
price_alerts = {}  # Format: {username: [{crypto_id, threshold, condition, active}]}

# Cache variables
price_cache = {}
cache_timestamp = None
CACHE_DURATION = 15  # Cache for 15 seconds (faster updates!)

# Helper function to fetch crypto prices from CoinGecko with caching
def fetch_crypto_prices(crypto_ids=['bitcoin', 'ethereum', 'cardano', 'solana', 'dogecoin']):
    """Fetch current prices for specified cryptocurrencies with caching"""
    global price_cache, cache_timestamp
    
    # Check if cache is still valid
    if cache_timestamp and datetime.now() - cache_timestamp < timedelta(seconds=CACHE_DURATION):
        print("Returning cached prices")
        return price_cache
    
    try:
        ids = ','.join(crypto_ids)
        url = f"{COINGECKO_API}/simple/price"
        params = {
            'ids': ids,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }
        print(f"Fetching fresh prices from API...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Update cache
        price_cache = response.json()
        cache_timestamp = datetime.now()
        print("Cache updated successfully")
        return price_cache
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Rate limit hit! Returning cached data if available...")
        else:
            print(f"HTTP Error fetching prices: {e}")
        # Return cached data if available, even if expired
        return price_cache if price_cache else {}
    except Exception as e:
        print(f"Error fetching prices: {e}")
        # Return cached data if available, even if expired
        return price_cache if price_cache else {}

# Route: Homepage - Display real-time crypto prices
@app.route('/')
def index():
    """Homepage showing real-time cryptocurrency prices"""
    return render_template('index.html')

# API Route: Get real-time prices
@app.route('/api/prices')
def get_prices():
    """API endpoint to fetch current crypto prices"""
    crypto_ids = request.args.get('ids', 'bitcoin,ethereum,cardano,solana,dogecoin').split(',')
    prices = fetch_crypto_prices(crypto_ids)
    return jsonify(prices)

# Test route to check if API is working
@app.route('/test-api')
def test_api():
    """Test if CoinGecko API is working"""
    prices = fetch_crypto_prices()
    return jsonify({
        'prices': prices,
        'cache_age': (datetime.now() - cache_timestamp).seconds if cache_timestamp else None,
        'cached': cache_timestamp is not None
    })

# Route: User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if username in users:
            return render_template('register.html', error="Username already exists!")
        
        # Store user (in production, hash the password!)
        users[username] = {
            'password': password,  # TODO: Hash this!
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        watchlists[username] = []
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Route: User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials!")
    
    return render_template('login.html')

# Route: Logout
@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('username', None)
    return redirect(url_for('index'))

# Route: User Dashboard
@app.route('/dashboard')
def dashboard():
    """User dashboard with watchlist"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user_watchlist = watchlists.get(username, [])
    
    return render_template('dashboard.html', username=username, watchlist=user_watchlist)

# Route: Historical Data Page
@app.route('/historical')
def historical():
    """Historical data visualization page"""
    return render_template('historical.html')

# API Route: Add to Watchlist
@app.route('/api/watchlist/add', methods=['POST'])
def add_to_watchlist():
    """Add cryptocurrency to user's watchlist"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    crypto_id = request.json.get('crypto_id')
    
    if username not in watchlists:
        watchlists[username] = []
    
    if crypto_id not in watchlists[username]:
        watchlists[username].append(crypto_id)
        return jsonify({'success': True, 'message': 'Added to watchlist'})
    
    return jsonify({'success': False, 'message': 'Already in watchlist'})

# API Route: Remove from Watchlist
@app.route('/api/watchlist/remove', methods=['POST'])
def remove_from_watchlist():
    """Remove cryptocurrency from user's watchlist"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    crypto_id = request.json.get('crypto_id')
    
    if username in watchlists and crypto_id in watchlists[username]:
        watchlists[username].remove(crypto_id)
        return jsonify({'success': True, 'message': 'Removed from watchlist'})
    
    return jsonify({'success': False, 'message': 'Not in watchlist'})

# API Route: Get Watchlist
@app.route('/api/watchlist')
def get_watchlist():
    """Get user's watchlist with current prices"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    user_watchlist = watchlists.get(username, [])
    
    if user_watchlist:
        prices = fetch_crypto_prices(user_watchlist)
        return jsonify(prices)
    
    return jsonify({})

# API Route: Create Price Alert
@app.route('/api/alerts/create', methods=['POST'])
def create_alert():
    """Create a price alert"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.json
    
    alert = {
        'id': len(price_alerts.get(username, [])) + 1,
        'crypto_id': data.get('crypto_id'),
        'threshold': float(data.get('threshold')),
        'condition': data.get('condition'),  # 'above' or 'below'
        'active': True,
        'created_at': datetime.now().isoformat()
    }
    
    if username not in price_alerts:
        price_alerts[username] = []
    
    price_alerts[username].append(alert)
    return jsonify({'success': True, 'alert': alert})

# API Route: Get User Alerts
@app.route('/api/alerts')
def get_alerts():
    """Get user's active alerts"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    user_alerts = price_alerts.get(username, [])
    return jsonify(user_alerts)

# API Route: Delete Alert
@app.route('/api/alerts/delete', methods=['POST'])
def delete_alert():
    """Delete a price alert"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    alert_id = request.json.get('alert_id')
    
    if username in price_alerts:
        price_alerts[username] = [a for a in price_alerts[username] if a['id'] != alert_id]
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Alert not found'})

# API Route: Check Alerts (returns triggered alerts)
@app.route('/api/alerts/check')
def check_alerts():
    """Check if any alerts have been triggered"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    user_alerts = price_alerts.get(username, [])
    triggered = []
    
    for alert in user_alerts:
        if not alert['active']:
            continue
        
        # Get current price
        prices = fetch_crypto_prices([alert['crypto_id']])
        if alert['crypto_id'] in prices:
            current_price = prices[alert['crypto_id']]['usd']
            
            if alert['condition'] == 'above' and current_price >= alert['threshold']:
                triggered.append({
                    'alert': alert,
                    'current_price': current_price,
                    'message': f"{alert['crypto_id'].capitalize()} is now ${current_price:,.2f} (above ${alert['threshold']:,.2f})"
                })
            elif alert['condition'] == 'below' and current_price <= alert['threshold']:
                triggered.append({
                    'alert': alert,
                    'current_price': current_price,
                    'message': f"{alert['crypto_id'].capitalize()} is now ${current_price:,.2f} (below ${alert['threshold']:,.2f})"
                })
    
    return jsonify(triggered)

# API Route: Get Historical Data
@app.route('/api/historical')
def get_historical():
    """Get historical price data for a cryptocurrency"""
    crypto = request.args.get('crypto', 'bitcoin')
    days = request.args.get('days', '7')
    
    try:
        url = f"{COINGECKO_API}/coins/{crypto}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily' if int(days) > 1 else 'hourly'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return jsonify({'error': str(e), 'prices': []}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)