from flask import Flask, render_template_string, request, redirect, session, flash
from datetime import datetime, timedelta
import uuid
import os

app = Flask(__name__)
app.secret_key = "shahban_bhai_super_secure_key_2026"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "shahban123"

# Data Storage
user_medicines = {} 
live_traffic = []   
user_mapping = {}   
user_counter = 0

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medicine Tracker</title>
    <style>
        body { font-family: Arial; margin: 15px; background: #f4f6f9; color: #333; }
        .box { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        input { width: 90%; padding: 8px; margin: 5px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #27ae60; color: white; border: none; padding: 10px; width: 95%; border-radius: 4px; font-size: 16px; cursor: pointer; }
        
        .error-alert { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 12px; border-radius: 5px; margin-bottom: 15px; font-size: 14px; font-weight: bold; text-align: left; }
        
        .table-container { overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; white-space: nowrap; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; font-size: 14px; }
        th { background: #2c3e50; color: white; }
        
        .remained { background: #2ecc71; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .ended { background: #e74c3c; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        
        .delete-btn { color: #e74c3c; font-size: 11px; text-decoration: none; font-weight: bold; opacity: 0.35; margin-right: 6px; padding: 0 2px; }
        .delete-btn:hover { opacity: 1; color: #c0392b; }
        
        .ad-space { background: #eef2f5; border: 2px dashed #bdc3c7; padding: 10px; text-align: center; margin: 15px 0; font-size: 12px; color: #7f8c8d; font-weight: bold; }
        .footer-link { text-align: center; margin-top: 30px; font-size: 12px; }
        .footer-link a { color: #7f8c8d; text-decoration: none; }
        
        .admin-box { background: #2c3e50; color: white; padding: 15px; border-radius: 8px; margin-top: 30px; }
        .admin-table th { background: #34495e; }
        .admin-table td { color: #333; background: #f8f9fa; }
    </style>
</head>
<body>

    <div class="ad-space">
        Google Ads Display Area (Earning Block)
    </div>

    <h2>💊 Medicine Stock Reminder <small style="font-size:12px; color:#7f8c8d;">(Aap: {{ current_user_no }})</small></h2>
    
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="error-alert">⚠️ Error: {{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <div class="box">
        <form action="/add" method="POST">
            <label>Medicine Name:</label><br>
            <input type="text" name="name" required><br>
            
            <label>Strip of:</label><br>
            <input type="number" name="capsules_per_strip" required><br>
            
            <label>No. of Strips:</label><br>
            <input type="number" name="strips" required><br>
            
            <label>No. of Days:</label><br>
            <input type="number" name="days" required><br>
            
            <button type="submit">Add Medicine</button>
        </form>
    </div>

    <h3>📋 Your Medicines List</h3>
    <div class="table-container">
        <table>
            <tr>
                <th>S.No.</th>
                <th>Medicine Name</th>
                <th>Added Date</th>
                <th>Capsules/Strip</th>
                <th>Total Strips</th>
                <th>Total Days</th>
                <th>End Date</th>
                <th>Status</th>
            </tr>
            {% for med in medicines %}
            <tr class="med-row" data-name="{{ med.name }}" data-end="{{ med.end }}" data-alert="{{ med.alert_tomorrow }}">
                <td>{{ loop.index }}</td>
                <td>
                    <a href="/delete/{{ loop.index0 }}" class="delete-btn" onclick="return confirm('Kya aap ise delete karna chahte hain?')">✖</a><b>{{ med.name }}</b>
                </td>
                <td>{{ med.added }}</td>
                <td>{{ med.capsules_per_strip }} caps</td>
                <td>{{ med.strips }} strip</td>
                <td>{{ med.total_days }} days</td>
                <td>{{ med.end }}</td>
                <td>
                    {% if med.is_ended %}
                    <span class="ended">❌ Ended</span>
                    {% else %}
                    <span class="remained">✅ Remained</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="ad-space">
        Responsive Ad Unit
    </div>

    {% if is_admin %}
    <div class="admin-box">
        <a href="/admin/logout" style="background: #e74c3c; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-size: 12px; float: right;">Logout Admin</a>
        <h3>🛡️ Owner Control Room (Live Traffic & Data Monitor)</h3>
        <div class="table-container">
            <table class="admin-table">
                <tr>
                    <th style="color:white;">User ID</th>
                    <th style="color:white;">Action</th>
                    <th style="color:white;">Medicine</th>
                    <th style="color:white;">Caps/Strip</th>
                    <th style="color:white;">Strips</th>
                    <th style="color:white;">Days</th>
                    <th style="color:white;">End Date</th>
                    <th style="color:white;">Timestamp</th>
                </tr>
                {% for log in traffic %}
                <tr>
                    <td><b>{{ log.user_no }}</b></td>
                    <td>{{ log.action }}</td>
                    <td>{{ log.med_name }}</td>
                    <td>{{ log.capsules }}</td>
                    <td>{{ log.strips }}</td>
                    <td>{{ log.total_days }}</td>
                    <td>{{ log.end_date }}</td>
                    <td>{{ log.time }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
    {% else %}
    <div class="footer-link">
        <a href="/admin/login">🔒 Admin Login</a>
    </div>
    {% endif %}

    <script>
        document.addEventListener('DOMContentLoaded', function () {
            if (Notification.permission !== "granted" && Notification.permission !== "denied") {
                Notification.requestPermission();
            }
            checkMedicineAlerts();
        });

        function checkMedicineAlerts() {
            let rows = document.querySelectorAll('.med-row');
            rows.forEach(row => {
                let isAlertTomorrow = row.getAttribute('data-alert') === 'True';
                let medName = row.getAttribute('data-name');
                let endDate = row.getAttribute('data-end');

                if (isAlertTomorrow && Notification.permission === "granted") {
                    new Notification("💊 Medicine Stock Warning Alert!", {
                        body: "Shahban Bhai, aapki dawa '" + medName + "' kal (" + endDate + ") ko khatam hone wali hai!",
                        icon: "https://cdn-icons-png.flaticon.com/512/822/822143.png"
                    });
                }
            });
        }
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
    <style>
        body { font-family: Arial; margin: 30px; background: #f4f6f9; text-align: center; }
        .login-box { max-width: 320px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #2c3e50; color: white; border: none; padding: 10px; width: 96%; border-radius: 4px; font-size: 16px; cursor: pointer; }
        .error { color: red; font-size: 14px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h3>🛡️ Control Room Login</h3>
        {% if error %} <p class="error">{{ error }}</p> {% endif %}
        <form action="/admin/login" method="POST">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Verify & Entry</button>
        </form>
        <br>
        <a href="/" style="color:#7f8c8d; text-decoration:none; font-size:14px;">← Back to App</a>
    </div>
</body>
</html>
"""

def get_or_create_user():
    global user_counter
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    uid = session['user_id']
    if uid not in user_mapping:
        user_counter += 1
        user_mapping[uid] = f"User-{user_counter}"
    return uid, user_mapping[uid]

def log_traffic(user_no, action, med_name="-", capsules="-", strips="-", total_days="-", end_date="-"):
    now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    live_traffic.insert(0, {
        'user_no': user_no, 'action': action, 'med_name': med_name,
        'capsules': capsules, 'strips': strips, 'total_days': total_days, 'end_date': end_date, 'time': now
    })

@app.route('/')
def index():
    uid, user_no = get_or_create_user()
    log_traffic(user_no, "Opened/Refreshed App")
    
    if uid not in user_medicines:
        user_medicines[uid] = []
        
    today = datetime.now().date()
    medicines = user_medicines[uid]
    
    for med in medicines:
        end_dt = datetime.strptime(med['end'], '%d-%m-%Y').date()
        med['is_ended'] = today >= end_dt
        med['alert_tomorrow'] = (end_dt - today).days == 1

    is_admin = session.get('is_admin', False)
    return render_template_string(HTML_TEMPLATE, medicines=medicines, traffic=live_traffic, current_user_no=user_no, is_admin=is_admin)

@app.route('/add', methods=['POST'])
def add():
    uid, user_no = get_or_create_user()
    name = request.form.get('name')
    capsules_per_strip = int(request.form.get('capsules_per_strip'))
    strips = int(request.form.get('strips'))
    total_days = int(request.form.get('days'))
    
    total_capsules_available = capsules_per_strip * strips
    if total_days > total_capsules_available:
        error_msg = f"Invalid calculation for '{name}'. You have only {total_capsules_available} total capsules ({capsules_per_strip} caps x {strips} strips), which cannot last for {total_days} days. Please update your strip count or days."
        flash(error_msg)
        log_traffic(user_no, f"Failed Add (Error: Invalid Days)", name, f"{capsules_per_strip} caps", f"{strips} strip", f"{total_days} days", "N/A")
        return redirect('/')
        
    added_dt = datetime.now().date()
    end_dt = added_dt + timedelta(days=total_days)
    
    formatted_added = added_dt.strftime('%d-%m-%Y')
    formatted_end = end_dt.strftime('%d-%m-%Y')
    
    new_med = {
        'name': name, 'added': formatted_added, 'capsules_per_strip': capsules_per_strip,
        'total_days': total_days, 'strips': strips,
        'end': formatted_end, 'is_ended': False, 'alert_tomorrow': False
    }
    
    user_medicines[uid].append(new_med)
    log_traffic(user_no, "Added Medicine ➕", name, f"{capsules_per_strip} caps", f"{strips} strip", f"{total_days} days", formatted_end)
    return redirect('/')

@app.route('/delete/<int:index>')
def delete(index):
    uid, user_no = get_or_create_user()
    if uid in user_medicines and 0 <= index < len(user_medicines[uid]):
        deleted_med = user_medicines[uid].pop(index)
        log_traffic(user_no, "Deleted Medicine ✖", deleted_med['name'], "-", "-", "-", deleted_med['end'])
    return redirect('/')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect('/')
        else:
            error = "Galat Password, Shahban bhai!"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect('/')

if __name__ == '__main__':
    # Cloud server ke liye port dynamic kar diya hai
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
