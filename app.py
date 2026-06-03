from flask import Flask, render_template_string, request, redirect, session, flash
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "shahban_bhai_super_secure_key_2026"

# Database Configuration & Initialization
DB_FILE = 'medicine_tracker.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Table for global variables / counters
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # Table for medicines
    conn.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            capsules_per_strip INTEGER,
            strips INTEGER,
            days INTEGER,
            added_date TEXT
        )
    ''')
    # Initialize user counter if not exists
    cursor = conn.execute("SELECT value FROM settings WHERE key = 'user_counter'")
    if not cursor.fetchone():
        conn.execute("INSERT INTO settings (key, value) VALUES ('user_counter', '0')")
    conn.commit()
    conn.close()

# Initialize Database on boot
init_db()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "shahban123"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medicine Tracker</title>
    <style>
        body { font-family: Arial; margin: 15px; background: #F4F6F9; color: #333; }
        .box { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 15px; }
        input { width: 90%; padding: 8px; margin: 5px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #27ae60; color: white; border: none; padding: 10px; width: 95%; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .error-alert { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 12px; border-radius: 5px; margin-bottom: 15px; }
        .table-container { overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; white-space: nowrap; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; font-size: 14px; }
        th { background: #2c3e50; color: white; }
        .remained { background: #2ecc71; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .ended { background: #e74c3c; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .delete-btn { color: #e74c3c; font-size: 11px; text-decoration: none; font-weight: bold; opacity: 0.85; margin-left: 10px; }
        .ad-space { background: #eef2f5; border: 2px dashed #bdc3c7; padding: 10px; text-align: center; margin: 15px 0; font-size: 12px; color: #7f8c8d; }
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

    <h2>💊 Medicine Stock Reminder <small style="font-size:12px; color:#7f8c8d;">(Aap: User-{{ current_user_no }})</small></h2>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="error-alert">⚠️ Error: {{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <div class="box">
        <form action="/add" method="POST">
            <label>Medicine Name:</label>
            <input type="text" name="name" required><br>
            
            <label>Strip of:</label>
            <input type="number" name="capsules_per_strip" required><br>
            
            <label>No. of Strips:</label>
            <input type="number" name="strips" required><br>
            
            <label>No. of Days:</label>
            <input type="number" name="days" required><br>
            
            <button type="submit">Add Medicine</button>
        </form>
    </div>

    📋 Your Medicines List
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>S.No.</th>
                    <th>Medicine Name</th>
                    <th>Added Date</th>
                    <th>Capsules/Strip</th>
                    <th>Total Stock</th>
                    <th>Days Limit</th>
                    <th>Status / Delete</th>
                </tr>
            </thead>
            <tbody>
                {% for med in user_medicines %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td><strong>{{ med.name }}</strong></td>
                    <td>{{ med.added_date }}</td>
                    <td>{{ med.capsules_per_strip }}</td>
                    <td>{{ med.capsules_per_strip * med.strips }} Caps ({{ med.strips }} Strips)</td>
                    <td>{{ med.days }} Days</td>
                    <td>
                        {% if med.is_expired %}
                            <span class="ended">Stock Ended</span>
                        {% else %}
                            <span class="remained">{{ med.days_left }} Days Left</span>
                        {% endif %}
                        <a href="/delete/{{ med.id }}" class="delete-btn" onclick="return confirm('Kya aap is dawa ko delete karna chahte hain?');">❌</a>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="7" style="text-align: center; color: #7f8c8d;">Koi dawa add nahi ki gayi hai.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="ad-space">
        Responsive Ad Unit
    </div>

    <div class="footer-link">
        <a href="/admin_login">🔒 Admin Login</a>
    </div>

</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard</title>
    <style>
        body { font-family: Arial; margin: 15px; background: #F4F6F9; color: #333; }
        .btn-back { background: #34495e; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-size: 14px; }
        .table-container { overflow-x: auto; background: white; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-top: 15px; }
        table { width: 100%; border-collapse: collapse; white-space: nowrap; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; font-size: 14px; }
        th { background: #2c3e50; color: white; }
    </style>
</head>
<body>

    <div style="margin-bottom: 20px;">
        <a href="/" class="btn-back">⬅️ Back to Home</a>
    </div>

    <h2>👨‍💻 System Admin Control Panel</h2>
    <p>Live Website Users Network Data Overview:</p>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>User ID</th>
                    <th>Medicine Name</th>
                    <th>Total Stock</th>
                    <th>Added Date</th>
                </tr>
            </thead>
            <tbody>
                {% for med in all_medicines %}
                <tr>
                    <td><code>{{ med.user_id }}</code></td>
                    <td><strong>{{ med.name }}</strong></td>
                    <td>{{ med.capsules_per_strip * med.strips }} Caps ({{ med.strips }} Strips)</td>
                    <td>{{ med.added_date }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="4" style="text-align: center; color: #7f8c8d;">Puri website par abhi koi data nahi hai.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

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
        body { font-family: Arial; margin: 15px; background: #F4F6F9; display: flex; justify-content: center; align-items: center; height: 80vh; }
        .login-box { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); width: 100%; max-width: 320px; }
        input { width: 92%; padding: 10px; margin: 10px 0 20px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #2c3e50; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .err { color: red; font-size: 14px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h3>Admin Secure Login</h3>
        {% if err %} <div class="err">{{ err }}</div> {% endif %}
        <form method="POST">
            <label>Username:</label>
            <input type="text" name="username" required>
            <label>Password:</label>
            <input type="password" name="password" required>
            <button type="submit">Access Dashboard</button>
        </form>
    </div>
</body>
</html>
"""

def get_or_create_user():
    if 'user_id' not in session:
        conn = get_db_connection()
        # Increment user counter in DB
        conn.execute("UPDATE settings SET value = CAST(value AS INTEGER) + 1 WHERE key = 'user_counter'")
        cursor = conn.execute("SELECT value FROM settings WHERE key = 'user_counter'")
        new_count = cursor.fetchone()['value']
        conn.commit()
        conn.close()
        
        session['user_id'] = f"User-{new_count}"
    return session['user_id']

@app.route('/')
def home():
    user_id = get_or_create_user()
    current_user_no = user_id.split('-')[1] if '-' in user_id else "1"
    
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM medicines WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    user_medicines = []
    now = datetime.now()
    
    for row in rows:
        med = dict(row)
        try:
            added_dt = datetime.strptime(med['added_date'], "%Y-%m-%d %H:%M")
            expiry_dt = added_dt + timedelta(days=med['days'])
            
            if now >= expiry_dt:
                med['is_expired'] = True
                med['days_left'] = 0
            else:
                med['is_expired'] = False
                med['days_left'] = (expiry_dt - now).days + 1
        except:
            med['is_expired'] = False
            med['days_left'] = med['days']
            
        user_medicines.append(med)
        
    return render_template_string(HTML_TEMPLATE, user_medicines=user_medicines, current_user_no=current_user_no)

@app.route('/add', methods=['POST'])
def add_medicine():
    user_id = get_or_create_user()
    name = request.form.get('name')
    capsules_per_strip = request.form.get('capsules_per_strip')
    strips = request.form.get('strips')
    days = request.form.get('days')
    
    try:
        caps_check = int(capsules_per_strip)
        strips_check = int(strips)
        days_check = int(days)
        
        if caps_check <= 0 or strips_check <= 0 or days_check <= 0:
            flash("Values hamesha 0 se badi honi chahiye!")
            return redirect('/')
    except ValueError:
        flash("Kripya sahi number hi darj karein!")
        return redirect('/')
        
    added_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO medicines (user_id, name, capsules_per_strip, strips, days, added_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, name, caps_check, strips_check, days_check, added_date))
    conn.commit()
    conn.close()
    
    return redirect('/')

@app.route('/delete/<int:med_id>')
def delete_medicine(med_id):
    user_id = get_or_create_user()
    conn = get_db_connection()
    # Security check: User can only delete their own medicine
    conn.execute('DELETE FROM medicines WHERE id = ? AND user_id = ?', (med_id, user_id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin_dashboard')
        else:
            return render_template_string(LOGIN_TEMPLATE, err="Galat Username ya Password!")
    return render_template_string(LOGIN_TEMPLATE, err=None)

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin_login')
        
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM medicines')
    all_medicines = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, all_medicines=all_medicines)

if __name__ == '__main__':
    app.run(debug=True)
