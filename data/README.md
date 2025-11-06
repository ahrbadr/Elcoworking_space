# Coworking Space Sign-In & Occupancy Tracker

A comprehensive web application for managing coworking space operations, including member check-ins, membership tracking, payment management, and daily reporting.

## 🌟 Features

### Core Functionality
- **Real-time Occupancy Tracking**: Live dashboard showing current members
- **Smart Check-in/Check-out**: Single interface for both actions
- **Membership Management**: Weekly, Bi-weekly, and Monthly subscriptions
- **Daily Passes**: Half-day and Full-day pass options
- **Free Drink Policy**: Automatic reminder for complimentary drinks

### Advanced Features
- **Subscriber Recognition**: Auto-fill and membership suggestions for returning members
- **Payment Tracking**: Daily income calculation with password protection
- **Unpaid Customer Management**: Flag customers who left without paying
- **Comprehensive Reporting**: Detailed daily reports with visitor analytics
- **Data Persistence**: All data saved locally in JSON files

### Membership System
- **Consecutive Day Memberships**: Subscriptions valid for consecutive calendar days
- **Time Reminders**: Visual warnings for expiring memberships
- **No Auto-renewal**: Manual renewal required after expiration
- **First-time Payment Tracking**: Membership payments calculated on activation day

## 🏗️ Project Structure

```
coworking-tracker/
│
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
│
├── templates/
│   └── index.html                 # Main web interface
│
├── data/                          # Data storage directory (auto-created)
│   ├── occupancy.json             # Historical occupancy records
│   ├── daily_income.json          # Income transaction records
│   ├── subscribers.json           # Subscriber profiles and visit history
│   ├── active_memberships.json    # Current active subscriptions
│   ├── unpaid_customers.json      # Customers marked as unpaid
│   └── daily_reports.json         # Generated daily reports
│
├── README.md                      # This file
└── SET.md          # Setup and deployment guide
```

## 📋 Prerequisites

- Python 3.8 or higher
- Flask web framework
- Modern web browser with JavaScript enabled

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd coworking-tracker
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv coworking_env
source coworking_env/bin/activate  # On Windows: coworking_env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

### 5. Access the Application
Open your browser and navigate to: `http://127.0.0.1:5000`

## ⚙️ Configuration

### Default Admin Password
The system uses a default admin password for sensitive operations.

**⚠️ Security Note**: Change the `INCOME_PASSWORD` in `app.py` before production use.

### Rate Card Configuration
Membership rates are configured in `app.py`:

## 🎯 Usage Guide

### Member Check-in Process
1. **Enter Name** (required) and Telephone (optional)
2. **Select Membership Type** from dropdown
3. **Click "Check In"** - system automatically:
   - Recognizes returning subscribers
   - Suggests appropriate memberships
   - Creates new subscriptions if needed
   - Tracks membership expiration

### Admin Functions
#### Income Calculation
1. Click "📊 Calculate Income" button
2. Enter admin password
3. Select date range (optional)
4. View income breakdown with transaction details

#### Daily Reports
1. Click "📈 Generate Daily Report" button
2. Enter admin password
3. Select report date
4. View comprehensive daily statistics

#### Mark Unpaid Customers
1. Fill customer details in main form
2. Enter amount and reason in unpaid section
3. Click "🚨 Mark as Unpaid" button

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main application interface |
| `/sign_action` | POST | Handle check-in/check-out actions |
| `/get_subscriber` | GET | Lookup subscriber information |
| `/calculate_income` | POST | Calculate income (password protected) |
| `/generate_report` | POST | Generate daily report (password protected) |
| `/mark_unpaid` | POST | Flag customer as unpaid |
| `/resolve_unpaid` | POST | Resolve unpaid status |
| `/api/occupancy` | GET | Get current occupancy data |

## 🎨 User Interface Features

### Visual Indicators
- **🟢 Green**: Active memberships, successful actions
- **🟠 Orange**: Expiring memberships (3 days or less)
- **🔴 Red**: Unpaid customers, expired memberships, errors
- **🟣 Purple**: Admin functions
- **🟡 Yellow**: Information and policy notices

### Smart Notifications
- Welcome back messages for returning subscribers
- Membership expiration warnings
- Payment confirmation for new subscriptions
- Unpaid customer alerts

## 🔒 Security Features

- Password protection for financial operations
- Data validation on all inputs
- CORS headers for development
- No sensitive data exposure in frontend

## 📈 Reporting & Analytics

### Daily Report Includes:
- Total visitors count
- Income breakdown (USD & EGP)
- Membership type distribution
- Visitor list with check-in times
- Transaction history

### Income Tracking:
- Daily pass payments
- First-time membership payments
- Date-range income calculations
- Transaction-level details

## 🛠️ Development

### Adding New Features
1. Backend: Modify `app.py` with new routes and logic
2. Frontend: Update `templates/index.html` with UI components
3. Data: Extend existing JSON structures or create new files

### Data Backup
All data is stored in JSON files in the `data/` directory. Regular backups are recommended.

### Customization
- Modify `RATE_CARD` for different pricing
- Adjust membership durations
- Change visual themes via Tailwind CSS classes
- Extend reporting features

## 🐛 Troubleshooting

### Common Issues
1. **Port already in use**: Change port in `app.run(port=5001)`
2. **Permission errors**: Ensure write permissions for `data/` directory
3. **JSON decode errors**: Delete corrupted JSON files to regenerate
4. **CORS issues**: Check browser console for errors

### Logs
- Application logs appear in console
- Data changes are logged to respective JSON files
- Error messages are displayed to users when appropriate

## 📄 License

This project is completely free to use, modify, and distribute. No restrictions apply.
