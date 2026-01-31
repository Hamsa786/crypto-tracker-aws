import pickle
import os
from datetime import datetime

# Database file paths
DB_DIR = 'data'
USERS_DB = os.path.join(DB_DIR, 'users.pkl')
WATCHLISTS_DB = os.path.join(DB_DIR, 'watchlists.pkl')
ALERTS_DB = os.path.join(DB_DIR, 'alerts.pkl')
PRICES_DB = os.path.join(DB_DIR, 'prices.pkl')

# Create data directory if it doesn't exist
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

def load_data(filename):
    """Load data from pickle file"""
    if os.path.exists(filename):
        try:
            with open(filename, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}
    return {}

def save_data(filename, data):
    """Save data to pickle file"""
    try:
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

# Database operations for Users
def get_all_users():
    """Get all users"""
    return load_data(USERS_DB)

def get_user(username):
    """Get a specific user"""
    users = get_all_users()
    return users.get(username)

def create_user(username, password, email):
    """Create a new user"""
    users = get_all_users()
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        'password': password,
        'email': email,
        'created_at': datetime.now().isoformat()
    }
    
    if save_data(USERS_DB, users):
        watchlists = get_all_watchlists()
        watchlists[username] = []
        save_data(WATCHLISTS_DB, watchlists)
        
        alerts = get_all_alerts()
        alerts[username] = []
        save_data(ALERTS_DB, alerts)
        
        return True, "User created successfully"
    return False, "Error creating user"

def verify_user(username, password):
    """Verify user credentials"""
    user = get_user(username)
    if user and user['password'] == password:
        return True
    return False

# Database operations for Watchlists
def get_all_watchlists():
    """Get all watchlists"""
    return load_data(WATCHLISTS_DB)

def get_user_watchlist(username):
    """Get watchlist for a specific user"""
    watchlists = get_all_watchlists()
    return watchlists.get(username, [])

def add_to_watchlist(username, crypto_id):
    """Add cryptocurrency to user's watchlist"""
    watchlists = get_all_watchlists()
    if username not in watchlists:
        watchlists[username] = []
    
    if crypto_id not in watchlists[username]:
        watchlists[username].append(crypto_id)
        if save_data(WATCHLISTS_DB, watchlists):
            return True, "Added to watchlist"
    return False, "Already in watchlist"

def remove_from_watchlist(username, crypto_id):
    """Remove cryptocurrency from user's watchlist"""
    watchlists = get_all_watchlists()
    if username in watchlists and crypto_id in watchlists[username]:
        watchlists[username].remove(crypto_id)
        if save_data(WATCHLISTS_DB, watchlists):
            return True, "Removed from watchlist"
    return False, "Not in watchlist"

# Database operations for Alerts
def get_all_alerts():
    """Get all alerts"""
    return load_data(ALERTS_DB)

def get_user_alerts(username):
    """Get alerts for a specific user"""
    alerts = get_all_alerts()
    return alerts.get(username, [])

def create_alert(username, crypto_id, threshold, condition):
    """Create a price alert"""
    alerts = get_all_alerts()
    if username not in alerts:
        alerts[username] = []
    
    alert = {
        'id': len(alerts[username]) + 1,
        'crypto_id': crypto_id,
        'threshold': float(threshold),
        'condition': condition,
        'active': True,
        'created_at': datetime.now().isoformat()
    }
    
    alerts[username].append(alert)
    if save_data(ALERTS_DB, alerts):
        return True, alert
    return False, None

def delete_alert(username, alert_id):
    """Delete a price alert"""
    alerts = get_all_alerts()
    if username in alerts:
        alerts[username] = [a for a in alerts[username] if a['id'] != alert_id]
        if save_data(ALERTS_DB, alerts):
            return True, "Alert deleted"
    return False, "Alert not found"

# Database operations for Price History
def get_all_prices():
    """Get all price history"""
    return load_data(PRICES_DB)

def save_price(crypto_id, price, timestamp=None):
    """Save a price point"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    prices = get_all_prices()
    if crypto_id not in prices:
        prices[crypto_id] = []
    
    prices[crypto_id].append({
        'price': price,
        'timestamp': timestamp
    })
    
    if len(prices[crypto_id]) > 1000:
        prices[crypto_id] = prices[crypto_id][-1000:]
    
    return save_data(PRICES_DB, prices)

def get_price_history(crypto_id, limit=100):
    """Get price history for a cryptocurrency"""
    prices = get_all_prices()
    if crypto_id in prices:
        return prices[crypto_id][-limit:]
    return []

# Initialize database files
if not os.path.exists(USERS_DB):
    save_data(USERS_DB, {})
if not os.path.exists(WATCHLISTS_DB):
    save_data(WATCHLISTS_DB, {})
if not os.path.exists(ALERTS_DB):
    save_data(ALERTS_DB, {})
if not os.path.exists(PRICES_DB):
    save_data(PRICES_DB, {})