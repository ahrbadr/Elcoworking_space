from flask import Flask, render_template, request, jsonify
from datetime import datetime, date, timedelta
import json
import os

app = Flask(__name__)

# File paths for data persistence
DATA_DIR = "data"
OCCUPANCY_FILE = os.path.join(DATA_DIR, "occupancy.json")
DAILY_INCOME_FILE = os.path.join(DATA_DIR, "daily_income.json")
SUBSCRIBERS_FILE = os.path.join(DATA_DIR, "subscribers.json")
MEMBERSHIPS_FILE = os.path.join(DATA_DIR, "active_memberships.json")
UNPAID_CUSTOMERS_FILE = os.path.join(DATA_DIR, "unpaid_customers.json")
DAILY_REPORTS_FILE = os.path.join(DATA_DIR, "daily_reports.json")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

def load_json_file(file_path, default=[]):
    """Load JSON data from file, return default if file doesn't exist"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json_file(file_path, data):
    """Save data to JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# Load existing data
occupancy_data = load_json_file(OCCUPANCY_FILE, [])
daily_income_records = load_json_file(DAILY_INCOME_FILE, [])
subscribers_data = load_json_file(SUBSCRIBERS_FILE, {})
active_memberships = load_json_file(MEMBERSHIPS_FILE, {})
unpaid_customers = load_json_file(UNPAID_CUSTOMERS_FILE, {})
daily_reports = load_json_file(DAILY_REPORTS_FILE, {})

# Updated pricing structure with duration
RATE_CARD = {
    # Fixed Daily/Session Fees
    'Half Day Pass':              {'rate_usd': 5.00, 'rate_egp': 250.00, 'unit': 'DAILY_FLAT', 'note': 'Charged $5.00 USD / EGP 250.00 for Half Day Session', 'duration_days': 1},
    'Full Day Pass':              {'rate_usd': 10.00, 'rate_egp': 500.00, 'unit': 'DAILY_FLAT', 'note': 'Charged $10.00 USD / EGP 500.00 for Full Day Session', 'duration_days': 1},
    
    # Fixed Membership Fees with duration
    'Weekly Membership':          {'rate_usd': 45.00, 'rate_egp': 2250.00, 'unit': 'WEEKLY_MEMBER', 'note': 'Weekly Member Session (Fee: $45 / EGP 2,250 paid externally)', 'duration_days': 7},
    'Bi-Weekly Membership':       {'rate_usd': 85.00, 'rate_egp': 4250.00, 'unit': 'BIWEEKLY_MEMBER', 'note': 'Bi-Weekly Member Session (Fee: $85 / EGP 4,250 paid externally)', 'duration_days': 14},
    'Monthly Membership':         {'rate_usd': 150.00, 'rate_egp': 7500.00, 'unit': 'MONTHLY_MEMBER', 'note': 'Monthly Member Session (Fee: $150 / EGP 7,500 paid externally)', 'duration_days': 30}
}

# Password for income calculation (change this in production)
INCOME_PASSWORD = "admin123"

class OccupancyTracker:
    def __init__(self):
        self.occupants = occupancy_data
    
    def check_in(self, name, telephone, membership):
        # Generate a simple identifier for tracking
        identifier = f"{name}_{telephone}" if telephone else name
        
        # Check if already checked in today
        today = date.today().isoformat()
        for occupant in self.occupants:
            if occupant['identifier'] == identifier and occupant['date'] == today:
                return False, "Already checked in today"
        
        check_in_time = datetime.now()
        rate_info = RATE_CARD.get(membership, {})
        
        # Check if this is a membership and handle subscription
        membership_status = None
        if rate_info.get('unit') in ['WEEKLY_MEMBER', 'BIWEEKLY_MEMBER', 'MONTHLY_MEMBER']:
            membership_status = self.handle_membership_subscription(identifier, name, telephone, membership, rate_info, check_in_time)
        
        occupant_data = {
            'name': name,
            'telephone': telephone,
            'identifier': identifier,
            'membership': membership,
            'rate_usd': rate_info.get('rate_usd', 0),
            'rate_egp': rate_info.get('rate_egp', 0),
            'unit_type': rate_info.get('unit', 'UNKNOWN'),
            'note': rate_info.get('note', ''),
            'check_in_time': check_in_time.isoformat(),
            'check_in_display': check_in_time.strftime("%I:%M %p"),
            'date': check_in_time.date().isoformat(),
            'timestamp': check_in_time.isoformat(),
            'membership_status': membership_status,
            'is_unpaid': identifier in unpaid_customers
        }
        
        self.occupants.append(occupant_data)
        save_json_file(OCCUPANCY_FILE, self.occupants)
        
        # Update subscriber data
        self.update_subscriber_data(name, telephone, membership, check_in_time)
        
        # Record income for daily passes AND first-time memberships
        if rate_info.get('unit') == 'DAILY_FLAT' or (membership_status and membership_status.get('status') == 'new'):
            income_record = {
                'name': name,
                'membership': membership,
                'rate_usd': rate_info.get('rate_usd', 0),
                'rate_egp': rate_info.get('rate_egp', 0),
                'timestamp': check_in_time.isoformat(),
                'date': check_in_time.date().isoformat(),
                'type': 'daily_pass' if rate_info.get('unit') == 'DAILY_FLAT' else 'membership_payment'
            }
            daily_income_records.append(income_record)
            save_json_file(DAILY_INCOME_FILE, daily_income_records)
        
        return True, "Checked in successfully"
    
    def handle_membership_subscription(self, identifier, name, telephone, membership, rate_info, check_in_time):
        """Handle membership subscription creation or validation"""
        today = check_in_time.date()
        duration_days = rate_info.get('duration_days', 7)
        
        if identifier in active_memberships:
            # Existing membership - check if still valid
            member_data = active_memberships[identifier]
            end_date = datetime.fromisoformat(member_data['end_date']).date()
            
            if today <= end_date:
                # Membership is still active
                days_remaining = (end_date - today).days
                return {
                    'status': 'active',
                    'days_remaining': days_remaining,
                    'end_date': member_data['end_date'],
                    'is_new': False
                }
            else:
                # Membership expired - don't auto-renew, treat as new check-in
                return {
                    'status': 'expired',
                    'days_remaining': 0,
                    'end_date': member_data['end_date'],
                    'is_new': False
                }
        else:
            # First time membership - create new subscription
            start_date = today
            end_date = today + timedelta(days=duration_days)
            active_memberships[identifier] = {
                'name': name,
                'telephone': telephone,
                'membership_type': membership,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': duration_days,
                'created_at': check_in_time.isoformat(),
                'payment_date': check_in_time.isoformat()  # Track when payment was made
            }
            save_json_file(MEMBERSHIPS_FILE, active_memberships)
            
            days_remaining = duration_days
            return {
                'status': 'new',
                'days_remaining': days_remaining,
                'end_date': end_date.isoformat(),
                'is_new': True
            }
    
    def update_subscriber_data(self, name, telephone, membership, check_in_time):
        """Update subscriber data with latest visit and calculate subscription status"""
        identifier = f"{name}_{telephone}" if telephone else name
        
        if identifier not in subscribers_data:
            subscribers_data[identifier] = {
                'name': name,
                'telephone': telephone,
                'membership_type': membership,
                'first_seen': check_in_time.isoformat(),
                'last_seen': check_in_time.isoformat(),
                'total_visits': 1,
                'visit_dates': [check_in_time.isoformat()],
                'last_membership': membership
            }
        else:
            subscriber = subscribers_data[identifier]
            subscriber['last_seen'] = check_in_time.isoformat()
            subscriber['last_membership'] = membership
            subscriber['total_visits'] += 1
            subscriber['visit_dates'].append(check_in_time.isoformat())
            
            # Keep only last 365 days of visits for performance
            if len(subscriber['visit_dates']) > 365:
                subscriber['visit_dates'] = subscriber['visit_dates'][-365:]
        
        save_json_file(SUBSCRIBERS_FILE, subscribers_data)
    
    def check_out(self, identifier):
        today = date.today().isoformat()
        for i, occupant in enumerate(self.occupants):
            if occupant['identifier'] == identifier and occupant['date'] == today:
                removed_occupant = self.occupants.pop(i)
                save_json_file(OCCUPANCY_FILE, self.occupants)
                return True, removed_occupant
        return False, "User not found in today's occupancy"
    
    def mark_unpaid(self, identifier, name, telephone, amount, reason):
        """Mark a customer as unpaid"""
        unpaid_customers[identifier] = {
            'name': name,
            'telephone': telephone,
            'amount': amount,
            'reason': reason,
            'date_reported': datetime.now().isoformat(),
            'resolved': False
        }
        save_json_file(UNPAID_CUSTOMERS_FILE, unpaid_customers)
        return True
    
    def resolve_unpaid(self, identifier):
        """Mark an unpaid customer as resolved"""
        if identifier in unpaid_customers:
            unpaid_customers[identifier]['resolved'] = True
            unpaid_customers[identifier]['resolved_date'] = datetime.now().isoformat()
            save_json_file(UNPAID_CUSTOMERS_FILE, unpaid_customers)
            return True
        return False
    
    def get_today_occupancy(self):
        """Get only today's occupancy"""
        today = date.today().isoformat()
        return [occupant for occupant in self.occupants if occupant['date'] == today]
    
    def get_subscriber_info(self, name, telephone):
        """Get subscriber information for auto-fill"""
        identifier = f"{name}_{telephone}" if telephone else name
        
        subscriber_info = {'found': False}
        
        # Check if user exists in subscribers
        if identifier in subscribers_data:
            subscriber = subscribers_data[identifier]
            
            # Calculate subscription frequency
            visit_dates = [datetime.fromisoformat(date_str) for date_str in subscriber['visit_dates']]
            if len(visit_dates) > 1:
                visit_dates.sort()
                time_spans = [(visit_dates[i+1] - visit_dates[i]).days for i in range(len(visit_dates)-1)]
                avg_days_between_visits = sum(time_spans) / len(time_spans)
            else:
                avg_days_between_visits = 0
            
            # Determine likely membership type based on frequency
            if avg_days_between_visits <= 2:
                suggested_membership = 'Monthly Membership'
            elif avg_days_between_visits <= 7:
                suggested_membership = 'Weekly Membership'
            elif avg_days_between_visits <= 14:
                suggested_membership = 'Bi-Weekly Membership'
            else:
                suggested_membership = subscriber['last_membership']
            
            subscriber_info.update({
                'found': True,
                'name': subscriber['name'],
                'last_membership': subscriber['last_membership'],
                'suggested_membership': suggested_membership,
                'total_visits': subscriber['total_visits'],
                'last_seen': subscriber['last_seen'],
                'avg_visit_frequency': round(avg_days_between_visits, 1)
            })
        
        # Check if user has active membership
        if identifier in active_memberships:
            membership_data = active_memberships[identifier]
            end_date = datetime.fromisoformat(membership_data['end_date']).date()
            today = date.today()
            days_remaining = (end_date - today).days
            
            subscriber_info['active_membership'] = {
                'type': membership_data['membership_type'],
                'start_date': membership_data['start_date'],
                'end_date': membership_data['end_date'],
                'days_remaining': days_remaining,
                'is_expired': days_remaining < 0
            }
            subscriber_info['has_active_membership'] = True
        
        # Check if user is marked as unpaid
        if identifier in unpaid_customers and not unpaid_customers[identifier].get('resolved', False):
            subscriber_info['is_unpaid'] = True
            subscriber_info['unpaid_info'] = unpaid_customers[identifier]
        
        return subscriber_info

    def generate_daily_report(self, report_date):
        """Generate a comprehensive report for a specific date"""
        if report_date in daily_reports:
            return daily_reports[report_date]
        
        # Calculate report data
        day_occupancy = [occ for occ in self.occupants if occ['date'] == report_date]
        day_income = [inc for inc in daily_income_records if inc['date'] == report_date]
        
        # Calculate totals
        total_income_usd = sum(inc['rate_usd'] for inc in day_income)
        total_income_egp = sum(inc['rate_egp'] for inc in day_income)
        
        # Count membership types
        membership_counts = {}
        for occ in day_occupancy:
            membership = occ['membership']
            membership_counts[membership] = membership_counts.get(membership, 0) + 1
        
        # Generate report
        report = {
            'date': report_date,
            'total_visitors': len(day_occupancy),
            'total_income_usd': total_income_usd,
            'total_income_egp': total_income_egp,
            'membership_breakdown': membership_counts,
            'visitors': day_occupancy,
            'transactions': day_income,
            'generated_at': datetime.now().isoformat()
        }
        
        # Save report
        daily_reports[report_date] = report
        save_json_file(DAILY_REPORTS_FILE, daily_reports)
        
        return report

tracker = OccupancyTracker()

def calculate_daily_income(target_date=None):
    """Calculate income for a specific date (default: today)"""
    if target_date is None:
        target_date = date.today().isoformat()
    
    date_income = [record for record in daily_income_records if record['date'] == target_date]
    
    total_usd = sum(record['rate_usd'] for record in date_income)
    total_egp = sum(record['rate_egp'] for record in date_income)
    
    return {
        'total_usd': total_usd,
        'total_egp': total_egp,
        'transaction_count': len(date_income),
        'transactions': date_income,
        'date': target_date
    }

def calculate_date_range_income(start_date, end_date):
    """Calculate income for a date range"""
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    
    range_income = []
    for record in daily_income_records:
        record_date = datetime.fromisoformat(record['date']).date()
        if start <= record_date <= end:
            range_income.append(record)
    
    total_usd = sum(record['rate_usd'] for record in range_income)
    total_egp = sum(record['rate_egp'] for record in range_income)
    
    return {
        'total_usd': total_usd,
        'total_egp': total_egp,
        'transaction_count': len(range_income),
        'transactions': range_income,
        'start_date': start_date,
        'end_date': end_date
    }

@app.route('/')
def index():
    today_date = date.today().strftime('%Y-%m-%d')
    return render_template('index.html', 
                         occupancy=tracker.get_today_occupancy(),
                         rate_card=RATE_CARD,
                         today_date=today_date)

@app.route('/sign_action', methods=['POST'])
def sign_action():
    try:
        data = request.get_json()
        action = data.get('action')
        name = data.get('name')
        telephone = data.get('telephone', '').strip()
        membership = data.get('membership')
        
        if not name:
            return jsonify({'success': False, 'message': 'Name is required'})
        
        identifier = f"{name}_{telephone}" if telephone else name
        
        if action == 'checkin':
            success, message = tracker.check_in(name, telephone, membership)
            if success:
                # Get the occupant to check membership status
                today_occupancy = tracker.get_today_occupancy()
                current_occupant = None
                for occupant in today_occupancy:
                    if occupant['identifier'] == identifier:
                        current_occupant = occupant
                        break
                
                response_message = f'Welcome {name}! (ask for your free drink)'
                
                # Add membership info if applicable
                if current_occupant and current_occupant.get('membership_status'):
                    status = current_occupant['membership_status']
                    if status['status'] == 'new':
                        response_message += f" 🎉 New {membership} activated! Valid for {status['days_remaining']} days."
                    elif status['status'] == 'active':
                        if status['days_remaining'] <= 3:
                            response_message += f" ⚠️ Your {membership} expires in {status['days_remaining']} days."
                        else:
                            response_message += f" ✅ {membership} active ({status['days_remaining']} days remaining)"
                    elif status['status'] == 'expired':
                        response_message += f" ❌ {membership} expired. Please renew."
                
                return jsonify({
                    'success': True,
                    'message': response_message,
                    'occupancy': today_occupancy,
                    'membership_status': current_occupant.get('membership_status') if current_occupant else None
                })
            else:
                return jsonify({'success': False, 'message': message})
        
        elif action == 'checkout':
            success, result = tracker.check_out(identifier)
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Goodbye {result["name"]}!',
                    'occupancy': tracker.get_today_occupancy()
                })
            else:
                return jsonify({'success': False, 'message': result})
        
        return jsonify({'success': False, 'message': 'Invalid action'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/mark_unpaid', methods=['POST'])
def mark_unpaid():
    try:
        data = request.get_json()
        name = data.get('name')
        telephone = data.get('telephone', '').strip()
        amount = data.get('amount', 0)
        reason = data.get('reason', '')
        
        if not name:
            return jsonify({'success': False, 'message': 'Name is required'})
        
        identifier = f"{name}_{telephone}" if telephone else name
        success = tracker.mark_unpaid(identifier, name, telephone, amount, reason)
        
        if success:
            return jsonify({'success': True, 'message': f'Marked {name} as unpaid'})
        else:
            return jsonify({'success': False, 'message': 'Failed to mark as unpaid'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/resolve_unpaid', methods=['POST'])
def resolve_unpaid():
    try:
        data = request.get_json()
        name = data.get('name')
        telephone = data.get('telephone', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Name is required'})
        
        identifier = f"{name}_{telephone}" if telephone else name
        success = tracker.resolve_unpaid(identifier)
        
        if success:
            return jsonify({'success': True, 'message': f'Resolved unpaid status for {name}'})
        else:
            return jsonify({'success': False, 'message': 'No unpaid record found'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/get_subscriber', methods=['GET'])
def get_subscriber():
    name = request.args.get('name', '').strip()
    telephone = request.args.get('telephone', '').strip()
    
    if name:
        subscriber_info = tracker.get_subscriber_info(name, telephone)
        return jsonify(subscriber_info)
    
    return jsonify({'found': False})

@app.route('/calculate_income', methods=['POST'])
def calculate_income():
    try:
        data = request.get_json()
        password = data.get('password', '')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if password != INCOME_PASSWORD:
            return jsonify({'success': False, 'message': 'Invalid password'})
        
        if start_date and end_date:
            # Date range calculation
            income_data = calculate_date_range_income(start_date, end_date)
            message = f"Income from {start_date} to {end_date}: ${income_data['total_usd']:.2f} USD / £{income_data['total_egp']:.2f} EGP from {income_data['transaction_count']} transactions"
        else:
            # Single day calculation (today)
            income_data = calculate_daily_income()
            message = f"Today's Income ({income_data['date']}): ${income_data['total_usd']:.2f} USD / £{income_data['total_egp']:.2f} EGP from {income_data['transaction_count']} transactions"
        
        return jsonify({
            'success': True,
            'income_data': income_data,
            'message': message
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        password = data.get('password', '')
        report_date = data.get('report_date', date.today().isoformat())
        
        if password != INCOME_PASSWORD:
            return jsonify({'success': False, 'message': 'Invalid password'})
        
        report = tracker.generate_daily_report(report_date)
        
        return jsonify({
            'success': True,
            'report': report,
            'message': f'Daily report generated for {report_date}'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/occupancy')
def api_occupancy():
    return jsonify(tracker.get_today_occupancy())

# Add this to fix CORS issues for local development
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Use these settings to fix the 403 error
    app.run(
        debug=True,
        host='127.0.0.1',  # Explicitly use localhost
        port=5000,
        threaded=True
    )