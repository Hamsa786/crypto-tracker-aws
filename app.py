from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
from datetime import datetime, timedelta
import os
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-later'

COINGECKO_API = "https://api.coingecko.com/api/v3"

# In-memory storage with thread lock
users = {}
watchlists = {}
market_prices = []
price_alerts = {}
data_lock = threading.Lock()

# Cache variables - per crypto caching
price_cache = {}
cache_timestamps = {}
CACHE_DURATION = 30  # Increased to 30 seconds to reduce API calls

# Rate limiting
last_api_call = None
MIN_API_INTERVAL = 2.5  # 2.5 seconds between API calls to respect rate limits
api_lock = threading.Lock()

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
                
                # Update cache with fresh data
                for crypto_id, data in fresh_data.items():
                    price_cache[crypto_id] = data
                    cache_timestamps[crypto_id] = datetime.now()
                    result[crypto_id] = data
                    print(f"✅ Fresh data for {crypto_id}: ${data.get('usd', 'N/A')}")
                    
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/prices')
def get_prices():
    crypto_ids = request.args.get('ids', 'bitcoin,ethereum,cardano,solana,dogecoin').split(',')
    prices = fetch_crypto_prices(crypto_ids)
    return jsonify(prices)

@app.route('/test-api')
def test_api():
    prices = fetch_crypto_prices()
    return jsonify({
        'prices': prices,
        'cached': {k: v.isoformat() for k, v in cache_timestamps.items()}
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        with data_lock:
            if username in users:
                return render_template('register.html', error="Username already exists!")
            
            users[username] = {
                'password': password,
                'email': email,
                'created_at': datetime.now().isoformat()
            }
            watchlists[username] = []
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            with data_lock:
                if username not in watchlists:
                    watchlists[username] = []
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    return render_template('dashboard.html', username=username)

@app.route('/historical')
def historical():
    return render_template('historical.html')

@app.route('/api/watchlist/add', methods=['POST'])
def add_to_watchlist():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in', 'success': False}), 401
    
    username = session['username']
    crypto_id = request.json.get('crypto_id')
    
    if not crypto_id:
        return jsonify({'success': False, 'message': 'No crypto specified'})
    
    with data_lock:
        if username not in watchlists:
            watchlists[username] = []
        
        if crypto_id in watchlists[username]:
            print(f"❌ {crypto_id} already in {username}'s watchlist: {watchlists[username]}")
            return jsonify({'success': False, 'message': 'Already in watchlist'})
        
        watchlists[username].append(crypto_id)
        current_watchlist = watchlists[username].copy()
    
    print(f"✅ Added {crypto_id} to {username}'s watchlist: {current_watchlist}")
    
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
        'message': 'Added to watchlist',
        'watchlist': current_watchlist,
        'crypto_data': {crypto_id: crypto_data} if crypto_data else {},
        'from_cache': crypto_id in price_cache and bool(crypto_data)
    })

@app.route('/api/watchlist/remove', methods=['POST'])
def remove_from_watchlist():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in', 'success': False}), 401
    
    username = session['username']
    crypto_id = request.json.get('crypto_id')
    
    if not crypto_id:
        return jsonify({'success': False, 'message': 'No crypto specified'})
    
    with data_lock:
        if username not in watchlists:
            watchlists[username] = []
            return jsonify({'success': False, 'message': 'Watchlist not found'})
        
        if crypto_id not in watchlists[username]:
            print(f"❌ {crypto_id} not in {username}'s watchlist: {watchlists[username]}")
            return jsonify({'success': False, 'message': 'Not in watchlist'})
        
        # Remove the crypto
        watchlists[username].remove(crypto_id)
        current_watchlist = watchlists[username].copy()
    
    print(f"✅ Removed {crypto_id} from {username}'s watchlist. Remaining: {current_watchlist}")
    
    return jsonify({
        'success': True, 
        'message': 'Removed from watchlist',
        'watchlist': current_watchlist
    })

@app.route('/api/watchlist')
def get_watchlist():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    
    with data_lock:
        if username not in watchlists:
            watchlists[username] = []
        user_watchlist = watchlists[username].copy()
    
    print(f"📊 Watchlist for {username}: {user_watchlist}")
    
    if not user_watchlist:
        return jsonify({})
    
    # Fetch prices for user's watchlist (will use cache when available)
    prices = fetch_crypto_prices(user_watchlist)
    
    print(f"📈 Returning prices for: {list(prices.keys())}")
    return jsonify(prices)

@app.route('/api/alerts/create', methods=['POST'])
def create_alert():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.json
    
    with data_lock:
        alert = {
            'id': len(price_alerts.get(username, [])) + 1,
            'crypto_id': data.get('crypto_id'),
            'threshold': float(data.get('threshold')),
            'condition': data.get('condition'),
            'active': True,
            'created_at': datetime.now().isoformat()
        }
        
        if username not in price_alerts:
            price_alerts[username] = []
        
        price_alerts[username].append(alert)
    
    return jsonify({'success': True, 'alert': alert})

@app.route('/api/alerts')
def get_alerts():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    with data_lock:
        user_alerts = price_alerts.get(username, []).copy()
    return jsonify(user_alerts)

@app.route('/api/alerts/delete', methods=['POST'])
def delete_alert():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    alert_id = request.json.get('alert_id')
    
    with data_lock:
        if username in price_alerts:
            price_alerts[username] = [a for a in price_alerts[username] if a['id'] != alert_id]
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Alert not found'})

@app.route('/api/alerts/check')
def check_alerts():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    with data_lock:
        user_alerts = price_alerts.get(username, []).copy()
    
    triggered = []
    
    for alert in user_alerts:
        if not alert['active']:
            continue
        
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
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)