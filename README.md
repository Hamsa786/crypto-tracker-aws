# Scalable Cryptocurrency Real-Time Price Tracker on AWS

![AWS](https://img.shields.io/badge/AWS-Cloud-orange)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![DynamoDB](https://img.shields.io/badge/DynamoDB-Database-yellow)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📋 Project Overview

A scalable cryptocurrency price tracking web application built with Flask and deployed on AWS. The application provides real-time price monitoring, personalized watchlists, price alerts, and historical data visualization for multiple cryptocurrencies.

### 🎯 Project Objectives

- Build a scalable web application for tracking cryptocurrency prices in real-time
- Implement cloud-native architecture using AWS services
- Develop RESTful APIs for cryptocurrency data management
- Create an intuitive user interface with real-time price updates
- Implement secure user authentication and data persistence

## 🏗️ Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   CoinGecko API │
                                    └────────┬────────┘
                                             │
                                             │
                                    ┌────────▼────────┐
                                    │                 │
                                    │   EC2 Instance  │
                                    │   Flask App     │
                                    │   (Port 8080)   │
                                    │                 │
                                    └────┬───────┬────┘
                                         │       │
                              ┌──────────┘       └──────────┐
                              │                             │
                    ┌─────────▼──────────┐      ┌──────────▼─────────┐
                    │                    │      │                    │
                    │     DynamoDB       │      │        SNS         │
                    │   (4 Tables)       │      │  (Notifications)   │
                    │                    │      │                    │
                    └────────────────────┘      └────────────────────┘
                              ▲
                              │
                    ┌─────────┴──────────┐
                    │                    │
                    │     IAM Role       │
                    │  (EC2 → DynamoDB)  │
                    │  (EC2 → SNS)       │
                    │                    │
                    └────────────────────┘
```

## 🚀 Features

### Core Functionality
- ✅ **Real-Time Price Tracking**: Live cryptocurrency prices updated every 15 seconds
- ✅ **User Authentication**: Secure registration and login system
- ✅ **Personal Watchlist**: Add/remove cryptocurrencies to track
- ✅ **Price Alerts**: Set custom alerts for price thresholds with SNS notifications
- ✅ **Historical Data Visualization**: Interactive charts showing price trends (24h, 7d, 30d, 90d, 1yr)
- ✅ **Animated Price Changes**: Visual indicators for price movements
- ✅ **Responsive Design**: Works seamlessly on desktop and mobile devices

### Technical Features
- ✅ API rate limiting and caching
- ✅ Data persistence with DynamoDB
- ✅ SNS notifications for price alerts
- ✅ IAM role-based access control
- ✅ Secure password handling

## 🛠️ Technology Stack

### Frontend
- **HTML5/CSS3**: Modern, responsive design
- **JavaScript (ES6+)**: Dynamic interactions
- **Chart.js**: Historical data visualization

### Backend
- **Python 3.11**: Core programming language
- **Flask 3.0**: Web framework
- **boto3**: AWS SDK for Python
- **requests**: HTTP library for CoinGecko API calls

### AWS Services
- **EC2**: Hosts the Flask application
- **DynamoDB**: NoSQL database for storing user data, watchlists, alerts, and market prices
- **IAM**: Manages secure access between EC2 and AWS services
- **SNS**: Sends notifications when price alerts are triggered

### External APIs
- **CoinGecko API**: Provides real-time cryptocurrency price data

## 📁 Project Structure

```
crypto-tracker-aws/
│
├── app.py                      # Local version with file-based database
├── app_aws.py                  # AWS production version with DynamoDB
├── database.py                 # Local database module (pickle)
├── create_dynamodb_tables.py   # Script to create DynamoDB tables
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore files
├── README.md                   # Project documentation
│
├── templates/                  # HTML templates
│   ├── index.html             # Homepage with real-time prices
│   ├── login.html             # User login page
│   ├── register.html          # User registration page
│   ├── dashboard.html         # User dashboard with watchlist & alerts
│   └── historical.html        # Historical data visualization
│
└── static/                     # Static assets
    ├── css/
    │   └── style.css          # Application styles
    └── js/
        └── main.js            # Client-side JavaScript (if needed)
```

## 🗄️ Database Schema (DynamoDB)

### Table 1: CryptoTracker_Users
**Purpose**: Store user account information

| Attribute    | Type   | Key Type       | Description              |
|-------------|--------|----------------|--------------------------|
| username    | String | Partition Key  | Unique username          |
| password    | String | -              | User password (hashed)   |
| email       | String | -              | User email address       |
| created_at  | String | -              | Account creation date    |

### Table 2: CryptoTracker_Watchlists
**Purpose**: Store user cryptocurrency watchlists

| Attribute | Type         | Key Type       | Description                    |
|-----------|--------------|----------------|--------------------------------|
| username  | String       | Partition Key  | User's username                |
| cryptos   | List(String) | -              | List of cryptocurrency IDs     |

### Table 3: CryptoTracker_Alerts
**Purpose**: Store price alert configurations

| Attribute   | Type    | Key Type       | Description                           |
|-------------|---------|----------------|---------------------------------------|
| alert_id    | String  | Partition Key  | Unique alert identifier               |
| username    | String  | GSI Partition  | User who created the alert            |
| crypto_id   | String  | -              | Cryptocurrency to monitor             |
| threshold   | Number  | -              | Price threshold                       |
| condition   | String  | -              | 'above' or 'below'                    |
| active      | Boolean | -              | Alert status                          |
| created_at  | String  | -              | Alert creation timestamp              |

**Global Secondary Index**: `username-index` on `username` attribute

### Table 4: CryptoTracker_MarketPrices
**Purpose**: Store historical price data

| Attribute   | Type   | Key Type      | Description                    |
|-------------|--------|---------------|--------------------------------|
| crypto_id   | String | Partition Key | Cryptocurrency identifier      |
| timestamp   | String | Sort Key      | Price timestamp (ISO format)   |
| price       | Number | -             | Price in USD                   |
| market_cap  | Number | -             | Market capitalization          |
| change_24h  | Number | -             | 24-hour price change %         |

## 📦 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- AWS Account with CLI configured
- Git installed
- pip (Python package manager)

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/Hamsa786/crypto-tracker-aws.git
cd crypto-tracker-aws
```

2. **Create and activate virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run locally (uses file-based database)**
```bash
python app.py
```

5. **Access the application**
```
Open browser: http://localhost:5000
```

The local version uses pickle files to store data. No AWS credentials needed for local testing.

## ☁️ AWS Deployment Guide

### Step 1: Configure AWS Credentials

```bash
# Configure AWS CLI with your credentials
aws configure

# You will be prompted for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region name: us-east-1
# - Default output format: json
```

### Step 2: Create DynamoDB Tables

```bash
# Run the table creation script
python create_dynamodb_tables.py
```

This creates 4 DynamoDB tables:
- `CryptoTracker_Users`
- `CryptoTracker_Watchlists`
- `CryptoTracker_Alerts`
- `CryptoTracker_MarketPrices`

**Verification**: Check AWS Console → DynamoDB → Tables to confirm all tables are created.

### Step 3: Create IAM Role for EC2

1. **Go to AWS Console → IAM → Roles → Create Role**

2. **Select trusted entity**: AWS service → EC2

3. **Attach policies**:
   - `AmazonDynamoDBFullAccess` - For DynamoDB operations
   - `AmazonSNSFullAccess` - For sending notifications

4. **Name the role**: `CryptoTrackerEC2Role`

5. **Create role**

**OR use AWS CLI**:

```bash
# Create trust policy file
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name CryptoTrackerEC2Role \
  --assume-role-policy-document file://trust-policy.json

# Attach DynamoDB policy
aws iam attach-role-policy \
  --role-name CryptoTrackerEC2Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Attach SNS policy
aws iam attach-role-policy \
  --role-name CryptoTrackerEC2Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name CryptoTrackerEC2Profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name CryptoTrackerEC2Profile \
  --role-name CryptoTrackerEC2Role
```

### Step 4: Launch EC2 Instance

1. **Go to AWS Console → EC2 → Launch Instance**

2. **Configure instance**:
   - **Name**: CryptoTracker-Server
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance type**: t2.micro (free tier eligible)
   - **Key pair**: Create new or use existing
   - **IAM Role**: Select `CryptoTrackerEC2Role`

3. **Configure Security Group**:
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 80) from anywhere (0.0.0.0/0)
   - Allow Custom TCP (port 8080) from anywhere (0.0.0.0/0)

4. **Launch instance**

### Step 5: Deploy Application on EC2

```bash
# 1. SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# 2. Update system packages
sudo apt update
sudo apt upgrade -y

# 3. Install Python and dependencies
sudo apt install python3-pip python3-venv git -y

# 4. Clone your repository
git clone https://github.com/Hamsa786/crypto-tracker-aws.git
cd crypto-tracker-aws

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install Python packages
pip install -r requirements.txt
pip install gunicorn

# 7. Test the application
python app_aws.py
# Press Ctrl+C to stop

# 8. Run with Gunicorn (production server)
gunicorn --bind 0.0.0.0:8080 app_aws:app --daemon

# 9. Access your app
# http://your-ec2-public-ip:8080
```

### Step 6: Configure as System Service (Optional - Recommended)

This ensures the app starts automatically on server reboot.

```bash
# 1. Create systemd service file
sudo nano /etc/systemd/system/cryptotracker.service
```

**Add this content**:
```ini
[Unit]
Description=CryptoTracker Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/crypto-tracker-aws
Environment="PATH=/home/ubuntu/crypto-tracker-aws/venv/bin"
ExecStart=/home/ubuntu/crypto-tracker-aws/venv/bin/gunicorn --bind 0.0.0.0:8080 app_aws:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable cryptotracker
sudo systemctl start cryptotracker

# 3. Check status
sudo systemctl status cryptotracker

# 4. View logs if needed
sudo journalctl -u cryptotracker -f
```

### Step 7: Setup SNS for Alerts (Optional)

```bash
# Create SNS topic
aws sns create-topic --name CryptoTrackerAlerts

# Subscribe email to topic (for testing)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:CryptoTrackerAlerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Confirm subscription via email
```

Update `app_aws.py` to use your SNS topic ARN in the `send_alert_notification()` function.

## 📊 API Endpoints

### Public Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Homepage with live prices |
| GET | `/register` | User registration page |
| GET | `/login` | User login page |
| GET | `/historical` | Historical data page |

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prices?ids=bitcoin,ethereum` | Get current cryptocurrency prices |
| GET | `/api/historical?crypto=bitcoin&days=7` | Get historical price data |

### Protected Endpoints (Requires Login)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | User dashboard |
| GET | `/api/watchlist` | Get user's watchlist with prices |
| POST | `/api/watchlist/add` | Add crypto to watchlist |
| POST | `/api/watchlist/remove` | Remove crypto from watchlist |
| GET | `/api/alerts` | Get user's alerts |
| POST | `/api/alerts/create` | Create new price alert |
| POST | `/api/alerts/delete` | Delete price alert |
| GET | `/api/alerts/check` | Check for triggered alerts |

## 🔐 Security Features

- ✅ Session-based authentication
- ✅ IAM role-based access (no hardcoded credentials)
- ✅ Password protection (hashing recommended for production)
- ✅ Secure cookie handling
- ✅ Input validation
- ⚠️ **Before production**: Implement bcrypt/argon2 for password hashing

## 🧪 Testing

### Test Locally
```bash
# Run local version
python app.py

# Test in browser
http://localhost:5000
```

### Test AWS Version Locally
```bash
# Set environment variables
export AWS_REGION=us-east-1
export SECRET_KEY=your-secret-key

# Run AWS version (connects to real DynamoDB)
python app_aws.py
```

### Verify DynamoDB Tables
```bash
# List all tables
aws dynamodb list-tables

# Scan Users table
aws dynamodb scan --table-name CryptoTracker_Users

# Check table details
aws dynamodb describe-table --table-name CryptoTracker_Users
```

## 🐛 Troubleshooting

### Issue: CoinGecko API Rate Limit (429 Error)
**Solution**: The app has built-in caching (15 seconds). If you still hit limits:
```python
# In app_aws.py, increase cache duration
CACHE_DURATION = 60  # Change from 15 to 60 seconds
```

### Issue: Cannot connect to DynamoDB
**Causes & Solutions**:
1. IAM role not attached to EC2 → Attach `CryptoTrackerEC2Role`
2. Wrong AWS region → Check `AWS_REGION` in app_aws.py matches your DynamoDB region
3. Tables not created → Run `python create_dynamodb_tables.py`

### Issue: Port 80 permission denied
**Solution**: Either use port 8080 or run with sudo:
```bash
# Option 1: Use port 8080 (recommended)
gunicorn --bind 0.0.0.0:8080 app_aws:app

# Option 2: Use port 80 with sudo
sudo $(which gunicorn) --bind 0.0.0.0:80 app_aws:app
```

### Issue: Application not starting on EC2
**Debug steps**:
```bash
# Check if Python is installed
python3 --version

# Check if venv is activated
which python  # Should show path with venv

# Check for errors in logs
sudo journalctl -u cryptotracker -n 50

# Test manually
cd /home/ubuntu/crypto-tracker-aws
source venv/bin/activate
python app_aws.py  # Look for error messages
```

## 📝 Project Deliverables

### ✅ Completed Features
- [x] Flask web application with real-time crypto prices
- [x] User authentication (register/login)
- [x] Watchlist management
- [x] Price alerts with notifications
- [x] Historical data visualization
- [x] DynamoDB integration (4 tables)
- [x] IAM role configuration
- [x] EC2 deployment
- [x] SNS integration for alerts
- [x] Responsive UI with animations

### 📦 GitHub Repository Contents
- [x] Complete source code
- [x] requirements.txt
- [x] README.md with documentation
- [x] DynamoDB table creation script
- [x] .gitignore file

## 🎓 Learning Outcomes

By completing this project, you will have learned:

1. **Flask Web Development**: Building REST APIs, handling sessions, routing
2. **AWS DynamoDB**: NoSQL database design, CRUD operations, GSI
3. **AWS IAM**: Role-based access control, policies, security
4. **AWS EC2**: Linux server management, deployment, systemd services
5. **AWS SNS**: Notification services, topic management
6. **API Integration**: Working with external APIs (CoinGecko)
7. **Frontend Development**: HTML/CSS/JavaScript, Chart.js
8. **DevOps**: Git, deployment automation, server configuration

## 📈 Future Enhancements

- [ ] Add HTTPS with SSL certificate
- [ ] Implement password hashing (bcrypt)
- [ ] Add email verification for new users
- [ ] Implement WebSocket for true real-time updates
- [ ] Add more cryptocurrencies (100+ coins)
- [ ] Portfolio tracking feature
- [ ] Export data to CSV
- [ ] Mobile-responsive improvements
- [ ] Add CloudWatch monitoring dashboard
- [ ] Implement auto-scaling with Load Balancer

## 👥 Author

**Hamsa Bhargav**
- GitHub: [@Hamsa786](https://github.com/Hamsa786)
- Project Repository: [crypto-tracker-aws](https://github.com/Hamsa786/crypto-tracker-aws)

## 📄 License

This project is created for educational purposes as part of AWS training.

## 🙏 Acknowledgments

- [CoinGecko](https://www.coingecko.com/) - Free cryptocurrency API
- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [Chart.js](https://www.chartjs.org/) - JavaScript charting library
- [AWS](https://aws.amazon.com/) - Cloud infrastructure

---

**⭐ If you found this project helpful, please star the repository!**

**📧 For questions or suggestions, please open an issue on GitHub.**