import os
import sys
import subprocess

try:
    from supabase import create_client, Client
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
    from supabase import create_client, Client

from flask import Flask, render_template_string, request, redirect, session, flash
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = "Shahban_bhai_super_secure_key_2026"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xyz.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "your-supabase-anon-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

live_traffic = []

def get_or_create_user():
    global live_traffic
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    uid = session['user_id']
    
    if 'user_no' not in session:
        existing_users = []
        for log in live_traffic:
            if log['user_no'] not in existing_users:
                existing_users.append(log['user_no'])
        session['user_no'] = f"User-{len(existing_users) + 1}"
        
    return uid, session['user_no']

def log_traffic(user_no, action, med_name="-", capsules="-", strips="-", total_days="-", end_date="-"):
    now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
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

@app.route('/')
def index():
    uid, user_no = get_or_create_user()
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

    today = datetime.now().date()
    for med in medicines:
        try:
            end_dt = datetime.strptime(med['end'], '%d-%m-%Y').date()
            med['is_ended'] = today >= end_dt
        except Exception:
            med['is_ended'] = False

    return render_template_string(HTML_TEMPLATE, medicines=medicines)

@app.route('/add', methods=['POST'])
def add():
    uid, user_no = get_or_create_user()
    name = request.form.get('name')
    capsules_per_strip = int(request.form.get('capsules_per_strip'))
    strips = int(request.form.get('strips'))
    total_days = int(request.form.get('days'))

    total_capsules_available = capsules_per_strip * strips
    if total_days > total_capsules_available:
        flash(f"Invalid calculation for '{name}'. Shortage of capsules!")
        return redirect('/')

    added_dt = datetime.now().date()
    end_dt = added_dt + timedelta(days=total_days)

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
    uid, user_no = get_or_create_user()
    try:
        supabase.table("medicines").delete().eq("id", med_id).eq("user_id", uid).execute()
    except Exception as e:
        flash(f"Delete Error: {e}")
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
