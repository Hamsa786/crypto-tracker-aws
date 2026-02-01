# AWS Deployment Checklist - CryptoTracker

⏰ **Time Required**: ~2-3 hours (within your 4-hour lab window)

---

## 🎯 Pre-Deployment Preparation (Complete BEFORE starting lab)

- [x] GitHub repository ready with all code
- [x] README.md completed
- [x] `create_dynamodb_tables.py` script ready
- [x] `app_aws.py` configured and tested locally
- [x] This checklist printed or open on second screen

---

## ⚡ Quick Start Guide (When Lab Opens)

### Phase 1: AWS Console Access (5 minutes)

1. **Open AWS Lab**
   - [ ] Click "Open Console" button in lab
   - [ ] Verify you're in **us-east-1** (N. Virginia) region
   - [ ] Note down any lab credentials provided

---

### Phase 2: DynamoDB Setup (15 minutes)

2. **Create DynamoDB Tables via CLI (Option A - Faster)**
   ```bash
   # If AWS CLI is available in lab
   cd ~/
   git clone https://github.com/Hamsa786/crypto-tracker-aws.git
   cd crypto-tracker-aws
   python3 create_dynamodb_tables.py
   ```
   
   - [ ] All 4 tables created successfully
   - [ ] Tables show "ACTIVE" status

   **OR Create via Console (Option B - If CLI not available)**
   
   Go to AWS Console → DynamoDB → Create Table:
   
   **Table 1: CryptoTracker_Users**
   - [ ] Table name: `CryptoTracker_Users`
   - [ ] Partition key: `username` (String)
   - [ ] Billing mode: On-demand
   - [ ] Create table
   
   **Table 2: CryptoTracker_Watchlists**
   - [ ] Table name: `CryptoTracker_Watchlists`
   - [ ] Partition key: `username` (String)
   - [ ] Billing mode: On-demand
   - [ ] Create table
   
   **Table 3: CryptoTracker_Alerts**
   - [ ] Table name: `CryptoTracker_Alerts`
   - [ ] Partition key: `alert_id` (String)
   - [ ] Billing mode: On-demand
   - [ ] Create Global Secondary Index:
     - Index name: `username-index`
     - Partition key: `username` (String)
     - Projection: All attributes
   - [ ] Create table
   
   **Table 4: CryptoTracker_MarketPrices**
   - [ ] Table name: `CryptoTracker_MarketPrices`
   - [ ] Partition key: `crypto_id` (String)
   - [ ] Sort key: `timestamp` (String)
   - [ ] Billing mode: On-demand
   - [ ] Create table

---

### Phase 3: IAM Role Setup (10 minutes)

3. **Create IAM Role**
   
   Go to AWS Console → IAM → Roles → Create Role
   
   - [ ] Select trusted entity: **AWS service**
   - [ ] Use case: **EC2**
   - [ ] Click Next
   
   **Attach Permissions:**
   - [ ] Search and select: `AmazonDynamoDBFullAccess`
   - [ ] Search and select: `AmazonSNSFullAccess`
   - [ ] Click Next
   
   **Name and Review:**
   - [ ] Role name: `CryptoTrackerEC2Role`
   - [ ] Description: "EC2 role for CryptoTracker with DynamoDB and SNS access"
   - [ ] Click Create role
   
   ✅ **Verify**: Role appears in IAM Roles list

---

### Phase 4: EC2 Instance Setup (20 minutes)

4. **Launch EC2 Instance**
   
   Go to AWS Console → EC2 → Launch Instance
   
   **Instance Configuration:**
   - [ ] Name: `CryptoTracker-Server`
   - [ ] AMI: **Ubuntu Server 22.04 LTS** (Free tier eligible)
   - [ ] Instance type: **t2.micro**
   - [ ] Key pair: Create new or use existing (SAVE THE .pem FILE!)
   - [ ] IAM instance profile: Select `CryptoTrackerEC2Role`
   
   **Network Settings:**
   - [ ] Allow SSH (port 22) from your IP
   - [ ] Allow HTTP (port 80) from 0.0.0.0/0
   - [ ] Allow Custom TCP (port 8080) from 0.0.0.0/0
   
   - [ ] Storage: 8 GB (default)
   - [ ] Click Launch Instance
   
   **Wait for Instance:**
   - [ ] Status check: Running (green)
   - [ ] Note down Public IPv4 address: `___________________`

---

### Phase 5: Application Deployment (30-40 minutes)

5. **Connect to EC2 via SSH**
   
   ```bash
   # Change key permissions (Windows Git Bash / Mac / Linux)
   chmod 400 your-key.pem
   
   # SSH into instance
   ssh -i your-key.pem ubuntu@YOUR-EC2-PUBLIC-IP
   ```
   
   - [ ] Successfully connected to EC2

6. **Install Dependencies**
   
   ```bash
   # Update system
   sudo apt update
   sudo apt upgrade -y
   
   # Install Python and tools
   sudo apt install python3-pip python3-venv git -y
   ```
   
   - [ ] All packages installed

7. **Clone Repository**
   
   ```bash
   # Clone your project
   git clone https://github.com/Hamsa786/crypto-tracker-aws.git
   cd crypto-tracker-aws
   ```
   
   - [ ] Repository cloned successfully

8. **Setup Python Environment**
   
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install gunicorn
   ```
   
   - [ ] All dependencies installed

9. **Test Application**
   
   ```bash
   # Quick test
   python app_aws.py
   ```
   
   - [ ] No errors shown
   - [ ] See "Running on http://0.0.0.0:8080"
   - [ ] Press Ctrl+C to stop

10. **Run with Gunicorn**
    
    ```bash
    # Start gunicorn
    gunicorn --bind 0.0.0.0:8080 app_aws:app --daemon
    
    # Check if running
    ps aux | grep gunicorn
    ```
    
    - [ ] Gunicorn process running

11. **Test in Browser**
    
    Open: `http://YOUR-EC2-PUBLIC-IP:8080`
    
    - [ ] Homepage loads
    - [ ] Crypto prices display
    - [ ] No errors in browser console

---

### Phase 6: Application Testing (20 minutes)

12. **Test All Features**
    
    - [ ] Register new user
    - [ ] Login works
    - [ ] Dashboard loads
    - [ ] Add cryptocurrency to watchlist
    - [ ] Create price alert
    - [ ] View historical data page
    - [ ] Prices update (wait 15 seconds)
    - [ ] Logout works

---

### Phase 7: Make it Production Ready (15 minutes)

13. **Configure System Service (Optional but Recommended)**
    
    ```bash
    # Create service file
    sudo nano /etc/systemd/system/cryptotracker.service
    ```
    
    **Paste this content:**
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
    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable cryptotracker
    sudo systemctl start cryptotracker
    
    # Check status
    sudo systemctl status cryptotracker
    ```
    
    - [ ] Service running and enabled

---

### Phase 8: Verification & Validation (10 minutes)

14. **Verify DynamoDB Data**
    
    Go to AWS Console → DynamoDB → Explore items
    
    - [ ] CryptoTracker_Users has entries
    - [ ] CryptoTracker_Watchlists has entries
    - [ ] CryptoTracker_MarketPrices has entries
    - [ ] CryptoTracker_Alerts has entries (if you created alerts)

15. **Verify IAM Role**
    
    Go to AWS Console → EC2 → Your Instance → Security tab
    
    - [ ] IAM role: `CryptoTrackerEC2Role` is attached

16. **Final Application Test**
    
    - [ ] Open: `http://YOUR-EC2-PUBLIC-IP:8080`
    - [ ] Register a new account
    - [ ] Add 3 cryptos to watchlist
    - [ ] Create 2 price alerts
    - [ ] View historical chart for Bitcoin
    - [ ] Wait 30 seconds for price update
    - [ ] Verify prices changed with animation

---

## ✅ Lab Validation

17. **Click "Validate" in Lab Interface**
    
    The lab should check:
    - [ ] DynamoDB tables created
    - [ ] EC2 instance running
    - [ ] IAM role configured
    - [ ] Application accessible
    
    - [ ] ✅ Validation passed

18. **Click "Submit" to Complete Lab**

---

## 📸 Documentation (For Portfolio)

19. **Take Screenshots**
    
    - [ ] Application homepage with live prices
    - [ ] Dashboard with watchlist
    - [ ] Historical chart page
    - [ ] DynamoDB tables in AWS Console
    - [ ] EC2 instance details
    - [ ] IAM role configuration

---

## 🐛 Troubleshooting Quick Fixes

### Problem: Can't SSH into EC2
**Solution:**
- Check security group has SSH port 22 open
- Verify you're using correct key file
- Check instance is in "Running" state

### Problem: Application won't start
**Solution:**
```bash
# Check logs
cd ~/crypto-tracker-aws
source venv/bin/activate
python app_aws.py  # Look for error messages
```

### Problem: DynamoDB connection error
**Solution:**
- Verify IAM role is attached to EC2 instance
- Check app_aws.py has correct region (us-east-1)
- Verify tables exist in DynamoDB console

### Problem: Page won't load in browser
**Solution:**
- Check security group allows port 8080
- Verify gunicorn is running: `ps aux | grep gunicorn`
- Check for errors: `sudo journalctl -u cryptotracker -n 50`

### Problem: Prices not showing
**Solution:**
- CoinGecko API rate limit - wait 1 minute
- Check internet connectivity from EC2
- Verify no firewall blocking outbound HTTPS

---

## ⏱️ Time Management

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Console Access | 5 min |
| 2 | DynamoDB Setup | 15 min |
| 3 | IAM Role | 10 min |
| 4 | EC2 Launch | 20 min |
| 5 | App Deployment | 40 min |
| 6 | Testing | 20 min |
| 7 | Production Setup | 15 min |
| 8 | Validation | 10 min |
| **Total** | | **~2h 15min** |

**Buffer time**: 1h 45min for troubleshooting/screenshots

---

## 🎉 Completion Checklist

- [ ] All AWS resources created
- [ ] Application fully functional
- [ ] Lab validated and submitted
- [ ] Screenshots taken for documentation
- [ ] GitHub repository is up to date

**Congratulations! You've successfully deployed a scalable cryptocurrency tracker on AWS! 🚀**