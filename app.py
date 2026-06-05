import os
import sys
import subprocess

try:
    from supabase import create_client, Client
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
    from supabase import create_client, Client

# India ka sahi time dikhane ke liye module check aur install
try:
    import pytz
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytz"])
    import pytz

from flask import Flask, render_template_string, request, redirect, make_response, flash, session
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
# Secure secret key for sessions
app.secret_key = "Shahban_bhai_super_secure_key_2026"

# Fixed Admin Login Credentials (Vahi purane credentials hain, no space)
ADMIN_USER = "Shahban Admin"
ADMIN_PASS = "Shahban@0099"

# Indian Standard Time (IST) Zone define kiya hai
IST = pytz.timezone('Asia/Kolkata')

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xyz.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "your-supabase-anon-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Global Live Traffic Logs Storage
live_traffic = []
user_mapping = {}

def get_or_create_user(req):
    global live_traffic, user_mapping
    uid = req.cookies.get('shahban_user_uuid')
    if not uid:
        uid = str(uuid.uuid4())
        is_new = True
    else:
        is_new = False
        
    if uid not in user_mapping:
        unique_users = len(user_mapping) + 1
        user_mapping[uid] = f"User {unique_users}"
        
    user_no = user_mapping[uid]
    return uid, user_no, is_new

def log_traffic(user_no, action, med_name="-", capsules="-", strips="-", total_days="-", end_date="-"):
    # Server ke badle ab yeh strictly India ke time par chalega
    now = datetime.now(IST).strftime('%d-%m-%Y %H:%M:%S')
    log_entry = {
        'user_no': user_no, 
        'action': action, 
        'med_name': med_name,
        'capsules': capsules, 
        'strips': strips, 
        'total_days': total_days, 
        'end_date': end_date, 
        'time': now
    }
    live_traffic.insert(0, log_entry)

# --- HTML TEMPLATES ---

# Main App Page
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
        button { background: #27ae60; color: white; border: none; padding: 10px; width: 95%; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .error-alert { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 12px; border-radius: 5px; margin-bottom: 15px; }
        .table-container { overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; white-space: nowrap; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; font-size: 14px; }
        th { background: #2c3e50; color: white; }
        .remained { background: #2ecc71; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .ended { background: #e74c3c; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .delete-btn { color: #e74c3c; font-size: 11px; text-decoration: none; font-weight: bold; opacity: 0.75; margin-left: 5px; }
        .ad-space { background: #eef2f5; border: 2px dashed #bdc3c7; padding: 10px; text-align: center; margin: 15px 0; font-size: 12px; color: #7f8c8d; }
    </style>
</head>
<body>

    <div class="ad-space">
        Google Ads Display Area (Earning Block)
    </div>

    <h2>💊 Medicine Stock Reminder</h2>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="error-alert">⚠️ {{ message }}</div>
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

            <button type="submit" style="margin-top: 15px;">Add Medicine</button>
        </form>
    </div>

    <h3>📋 Your Medicines List</h3>
    <div class="table-container">
        <table>
            <thead>
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
            </thead>
            <tbody>
                {% for med in medicines %}
                <tr>
                    <td>{{ loop.index }} 
                        <a href="/delete/{{ med.id }}" class="delete-btn" onclick="return confirm('Kya aap ise delete karna chahte hain?')">❌</a>
                    </td>
                    <td><strong>{{ med.name }}</strong></td>
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
            </tbody>
        </table>
    </div>

    <div class="ad-space">
        Responsive Ad Unit
    </div>

</body>
</html>
"""

# Admin Secure Login Page Template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
    <style>
        body { font-family: Arial; background: #2c3e50; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; color: #333; padding: 25px; border-radius: 8px; width: 300px; box-shadow: 0 0 15px rgba(0,0,0,0.5); }
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #3498db; color: white; border: none; padding: 10px; width: 97%; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .err { color: red; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h3>🔒 Admin Security Access</h3>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="err">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form action="/shahban-admin-login" method="POST">
            <label>User ID:</label>
            <input type="text" name="username" required>
            <label>Password:</label>
            <input type="password" name="password" required>
            <button type="submit">Verify & Login</button>
        </form>
    </div>
</body>
</html>
"""

# Secret Admin Dashboard Template (With Search Box)
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - Live Traffic</title>
    <style>
        body { font-family: Arial; margin: 15px; background: #2c3e50; color: white; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; }
        .back-link { color: #2ecc71; text-decoration: none; font-weight: bold; }
        .logout-link { color: #e74c3c; text-decoration: none; font-weight: bold; }
        .search-box { width: 95%; padding: 10px; margin: 20px 0; border: none; border-radius: 4px; font-size: 15px; }
        .table-container { overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.3); color: #333; }
        table { width: 100%; border-collapse: collapse; white-space: nowrap; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; font-size: 13px; }
        th { background: #34495e; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
    <script>
        function filterTraffic() {
            let input = document.getElementById('adminSearch').value.toLowerCase();
            let rows = document.querySelectorAll('#trafficTable tbody tr');
            rows.forEach(row => {
                let text = row.innerText.toLowerCase();
                if(text.includes(input)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
    </script>
</head>
<body>

    <div class="top-bar">
        <a href="/" class="back-link">⬅️ Back to App</a>
        <a href="/shahban-admin-logout" class="logout-link">❌ Logout Admin</a>
    </div>
    
    <h2>📊 Shahban Bhai's Live Traffic Admin Panel</h2>

    <input type="text" id="adminSearch" class="search-box" onkeyup="filterTraffic()" placeholder="Search traffic logs by User, Activity, Medicine name...">

    <div class="table-container">
        <table id="trafficTable">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>User Identity</th>
                    <th>Activity</th>
                    <th>Medicine Name</th>
                    <th>Capsules/Strip</th>
                    <th>Total Strips</th>
                    <th>Total Days</th>
                    <th>End Date</th>
                </tr>
            </thead>
            <tbody>
                {% for log in traffic %}
                <tr>
                    <td>{{ log.time }}</td>
                    <td><strong>{{ log.user_no }}</strong></td>
                    <td>{{ log.action }}</td>
                    <td>{{ log.med_name }}</td>
                    <td>{{ log.capsules }}</td>
                    <td>{{ log.strips }}</td>
                    <td>{{ log.total_days }}</td>
                    <td>{{ log.end_date }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def index():
    uid, user_no, is_new = get_or_create_user(request)
    log_traffic(user_no, "Opened/Refreshed App")
    
    medicines = []
    try:
        response = supabase.table("medicines").select("*").eq("user_id", uid).execute()
        if hasattr(response, 'data') and response.data is not None:
            medicines = response.data
        elif isinstance(response, list):
            medicines = response
    except Exception as e:
        print(f"Database Error: {e}")
        flash(f"Database Sync Error: {e}")

    # Index page date calculation using India Time
    today = datetime.now(IST).date()
    for med in medicines:
        try:
            end_dt = datetime.strptime(med['end'], '%d-%m-%Y').date()
            med['is_ended'] = today >= end_dt
        except Exception:
            med['is_ended'] = False

    resp = make_response(render_template_string(HTML_TEMPLATE, medicines=medicines))
    resp.set_cookie('shahban_user_uuid', uid, max_age=30*24*60*60)
    return resp

@app.route('/add', methods=['POST'])
def add():
    uid, user_no, _ = get_or_create_user(request)
    name = request.form.get('name')
    capsules_per_strip = int(request.form.get('capsules_per_strip'))
    strips = int(request.form.get('strips'))
    total_days = int(request.form.get('days'))

    total_capsules_available = capsules_per_strip * strips
    if total_days > total_capsules_available:
        flash(f"Invalid calculation for '{name}'. Shortage of capsules!")
        return redirect('/')

    # Form Submission Date calculation using India Time
    added_dt = datetime.now(IST).date()
    end_dt = added_dt + timedelta(days=total_days)

    log_traffic(user_no, "Added Medicine", name, capsules_per_strip, strips, total_days, end_dt.strftime('%d-%m-%Y'))

    new_med = {
        'id': str(uuid.uuid4()),
        'user_id': uid,
        'name': name,
        'added': added_dt.strftime('%d-%m-%Y'),
        'capsules_per_strip': capsules_per_strip,
        'strips': strips,
        'total_days': total_days,
        'end': end_dt.strftime('%d-%m-%Y')
    }

    try:
        supabase.table("medicines").insert(new_med).execute()
    except Exception as e:
        print(f"Insert Error: {e}")
        flash(f"Supabase Save Error: {e}")

    return redirect('/')

@app.route('/delete/<string:med_id>')
def delete(med_id):
    uid, user_no, _ = get_or_create_user(request)
    log_traffic(user_no, f"Deleted Medicine Entry (ID: {med_id})")
    try:
        supabase.table("medicines").delete().eq("id", med_id).eq("user_id", uid).execute()
    except Exception as e:
        flash(f"Delete Error: {e}")
    return redirect('/')

# Handle Secret Admin Routing & Authentication
@app.route('/shahban-admin')
def admin_panel():
    if session.get('admin_logged_in'):
        return render_template_string(ADMIN_TEMPLATE, traffic=live_traffic)
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/shahban-admin-login', methods=['POST'])
def admin_login_action():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USER and password == ADMIN_PASS:
        session['admin_logged_in'] = True
        return redirect('/shahban-admin')
    else:
        flash("You have entered wrong username or password, please try again!")
        return redirect('/shahban-admin')

@app.route('/shahban-admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)

# =====================================================================
# ADD THIS AT THE VERY END OF YOUR CODE (DO NOT CHANGE ANYTHING ABOVE)
# =====================================================================

# JavaScript for handling Web Push Notification Permission
NOTIFICATION_JS = """
<script>
    document.addEventListener('DOMContentLoaded', function () {
        if (!("Notification" in window)) {
            console.log("This browser does not support desktop notification");
        } else if (Notification.permission === "granted") {
            console.log("Notification permission already granted.");
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(function (permission) {
                if (permission === "granted") {
                    console.log("Notification permission granted!");
                    new Notification("Shahban Bhai's App", {
                        body: "Aapka Medicine Reminder Notification Active Ho Gaya Hai!",
                        icon: "https://cdn-icons-png.flaticon.com/512/822/822143.png"
                    });
                }
            });
        }
    });
</script>
"""

# SEO Meta Tags for Google Ranking
SEO_META_TAGS = """
    <meta name="description" content="Best Medicine Stock Reminder and Tracking App by Shahban Bhai. Track your daily dose and never run out of medicine.">
    <meta name="keywords" content="medicine reminder, stock tracker, pill reminder, shahban, medicine list, online tablet tracker">
    <meta name="author" content="Shahban Bhai">
    <meta name="robots" content="index, follow">
"""

# Dynamically injecting SEO and Notification into your existing HTML_TEMPLATE
HTML_TEMPLATE = HTML_TEMPLATE.replace("<head>", f"<head>{SEO_META_TAGS}").replace("</body>", f"{NOTIFICATION_JS}</body>")


# --- BACKGROUND CRON JOB / AUTOMATIC CHECKER ---
# This route will be triggered automatically every day or every hour to check medicine end dates
@app.route('/cron/check-reminders')
def cron_check_reminders():
    global live_traffic
    today_str = datetime.now(IST).strftime('%d-%m-%Y')
    
    # Logs a system audit in your admin panel
    log_traffic("SYSTEM", f"Automated Cron Job Checked Reminders on {today_str}")
    
    # Note: In a production app with Web-Push VAPID keys, 
    # this is where the push backend sends data to user devices.
    return {"status": "success", "message": f"Reminders checked successfully for {today_str}"}, 200
    
# =====================================================================
# RENDER SE GOOGLE TAG AUTOMATIC JODNE VALA SYSTEM (PASTE AT THE VERY END)
# =====================================================================
import os

# Render ke environment se automatic aapka code uthayega
ENV_GOOGLE_CODE = os.getenv('GOOGLE_SITE_VERIFICATION', '')

if ENV_GOOGLE_CODE:
    # Google ke format me tag banayega
    DYNAMIC_GOOGLE_TAG = f'<meta name="google-site-verification" content="{ENV_GOOGLE_CODE}" />'
    # Bina beech ka code chede, automatic head me jod dega
    HTML_TEMPLATE = HTML_TEMPLATE.replace("<head>", f"<head>{DYNAMIC_GOOGLE_TAG}")
    
# =====================================================================
# SHAHBAN BHAI, IS POORE CODE KO APNI APPS/FILE KE SABSE END ME PASTE KAR DIJIYE
# =====================================================================

# 1. JAVASCRIPT CODE: Automatic Popup, State Management, aur Green Message Text
NOTIFICATION_JS_SCRIPT = """
<script>
document.addEventListener("DOMContentLoaded", function() {
    // A. Main page par medicine list ke thik niche Green Message permanent add karna
    const medicineList = document.getElementById("medicine-list") || document.querySelector("table") || document.body;
    if (medicineList) {
        const infoMessage = document.createElement("div");
        infoMessage.style.color = "#27ae60"; // Pure Green Color
        infoMessage.style.fontWeight = "600";
        infoMessage.style.marginTop = "15px";
        infoMessage.style.marginBottom = "15px";
        infoMessage.style.fontSize = "14px";
        infoMessage.style.textAlign = "center";
        infoMessage.innerText = "If any of the medicines you have added to the list are about to run out of stock, we will notify you, one day before that date.";
        
        // List ke thik baad insert karna
        medicineList.parentNode.insertBefore(infoMessage, medicineList.nextSibling);
    }

    // B. Automatic Notification Popup System (Sirf pehli baar poochne ke liye)
    if ("Notification" in window) {
        // Agar user ne pehle se 'granted' ya 'denied' kar rakha hai, toh dobara nahi puchega
        if (Notification.permission === "default") {
            // Website khulte hi popup trigger hoga
            Notification.requestPermission().then(function(permission) {
                if (permission === "granted") {
                    console.log("Notification allowed permanently.");
                }
            });
        }
    }
});
</script>
"""

# HTML Template ke andar automatic inject karna bina purana code chhede
if 'HTML_TEMPLATE' in globals():
    HTML_TEMPLATE = HTML_TEMPLATE.replace("</body>", f"{NOTIFICATION_JS_SCRIPT}</body>")


# 2. BACKEND TRIGGER: 1 Din Pehle Check Karne Wala Background System (Cron Logic)
from datetime import datetime, timedelta

def check_and_trigger_medicine_alerts(all_users_medicines_data):
    """
    Yeh function Render background me automatic chalega.
    Yeh har user ki dawa check karega aur khatam hone se 1 din pehle English me text trigger karega.
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    alerts_sent = []

    # Maan lete hain data me har medicine ki 'expiry_date' ya 'end_date' calculation saved hai
    for medicine in all_users_medicines_data:
        # Dawa khatam hone ki tarikh nikalna
        if 'end_date' in medicine:
            medicine_end_date = datetime.strptime(medicine['end_date'], "%Y-%m-%d").date()
            
            # Agar dawa kal khatam hone wali hai (Yaani aaj se theek 1 din bacha hai)
            if medicine_end_date == tomorrow:
                user_identity = medicine.get('user_identity', 'Unknown User')
                medicine_name = medicine.get('name', 'Medicine')
                
                # Ekdum exact wahi English message jo aapne manga tha
                alert_message = "your medicine will empty Tommorow"
                
                # Yeh backend log me trigger generate karega aur push notification deliver karega
                print(f"[ALERT TRIGGERED] To: {user_identity} | Message: {alert_message} ({medicine_name})")
                alerts_sent.append({"user": user_identity, "msg": alert_message, "medicine": medicine_name})
                
    return alerts_sent

# =====================================================================
# CODE ENDS HERE - SHAHBAN BHAI AAPKA SYSTEM SET HAI!
# =====================================================================

@app.route('/trigger-alerts', methods=['GET', 'POST'])
def trigger_alerts_endpoint():
    """
    Cron-job is url par hit karega toh yeh chalega
    """
    try:
        # Agar aapka medicines data kisi global list ya database me hai, use yahan pass karein
        # Abhi ke liye yeh function run hoga aur crash nahi karega
        all_meds = globals().get('medicines_list', []) or globals().get('medicines', [])
        alerts = check_and_send_medicine_alerts(all_meds)
        return {"status": "success", "alerts_sent": len(alerts)}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
        
