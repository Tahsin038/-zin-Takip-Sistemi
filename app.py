#!/usr/bin/env python3
"""
İzin Takip Sistemi - Güvenli Versiyon (Düzeltilmiş)
Şifre sistemi ve işçi silme özellikleri
"""

import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secure-izin-takip-2024')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Ana sayfa şablonu
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>İzin Takip Sistemi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
        }
        .main-card { 
            background: rgba(255, 255, 255, 0.95); 
            border-radius: 20px; 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); 
        }
        .btn-custom { 
            border-radius: 15px; 
            padding: 15px 30px; 
            font-size: 1.2rem; 
            font-weight: 600; 
        }
    </style>
</head>
<body>
    <div class="container-fluid d-flex align-items-center justify-content-center min-vh-100">
        <div class="main-card p-5 text-center" style="max-width: 500px; width: 90%;">
            <h1 class="mb-4">🔐 Güvenli İzin Takip Sistemi</h1>
            <p class="text-muted mb-4">Şifre korumalı giriş sistemi</p>
            <div class="d-grid gap-3">
                <a href="/employee_login" class="btn btn-success btn-custom">👤 İşçi Girişi</a>
                <a href="/employer_login" class="btn btn-warning btn-custom">👔 İşveren Girişi</a>
            </div>
            <div class="mt-4">
                <small class="text-muted">Demo şifreler - İşçi: 123456, İşveren: admin123</small>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Giriş şablonları
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, {{ bg_color }}); 
            min-height: 100vh; 
        }
        .login-card { 
            background: rgba(255, 255, 255, 0.95); 
            border-radius: 20px; 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); 
        }
    </style>
</head>
<body>
    <div class="container-fluid d-flex align-items-center justify-content-center min-vh-100">
        <div class="login-card p-5" style="max-width: 500px; width: 90%;">
            <h2 class="text-center mb-4">{{ title }}</h2>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'danger' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST">
                {% if show_employee_select %}
                <div class="mb-3">
                    <label class="form-label">Çalışan Adı</label>
                    <select class="form-select" name="employee_name" required>
                        <option value="">Seçiniz...</option>
                        {% for emp in employees %}
                            <option value="{{ emp.name }}">{{ emp.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                {% endif %}
                
                <div class="mb-3">
                    <label class="form-label">Şifre</label>
                    <input type="password" class="form-control" name="password" required placeholder="Şifrenizi giriniz">
                    {% if show_demo_info %}
                        <div class="form-text">Varsayılan şifre: admin123</div>
                    {% endif %}
                </div>
                
                <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-primary btn-lg">🔓 Giriş Yap</button>
                    <a href="/" class="btn btn-outline-secondary">← Ana Sayfa</a>
                </div>
            </form>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

# Panel şablonu
PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, {{ bg_color }}); 
            min-height: 100vh; 
        }
        .panel-card { 
            background: rgba(255, 255, 255, 0.95); 
            border-radius: 20px; 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); 
        }
    </style>
</head>
<body>
    <div class="container my-4">
        <div class="panel-card p-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>{{ title }}</h2>
                <div>
                    <a href="/logout" class="btn btn-outline-danger me-2">🔓 Çıkış</a>
                    <a href="/" class="btn btn-outline-secondary">← Ana Sayfa</a>
                </div>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'danger' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            {{ content|safe }}
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
    function deleteEmployee(name) {
        if (confirm('⚠️ UYARI: ' + name + ' adlı çalışanı kalıcı olarak silmek istediğinizden emin misiniz?\\n\\n• Tüm izin kayıtları silinecek\\n• Bu işlem geri alınamaz!\\n\\nDevam etmek istiyor musunuz?')) {
            fetch('/delete_employee', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'employee_name=' + encodeURIComponent(name)
            }).then(response => {
                if (response.ok) {
                    alert('✅ ' + name + ' başarıyla silindi!');
                    location.reload();
                } else {
                    alert('❌ Silme işlemi başarısız! Lütfen tekrar deneyin.');
                }
            }).catch(error => {
                alert('❌ Bağlantı hatası! Lütfen tekrar deneyin.');
            });
        }
    }
    </script>
</body>
</html>
'''

class SecureDatabase:
    def __init__(self):
        self.db_path = "secure_izin.db"
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY, name TEXT UNIQUE, password_hash TEXT,
            start_date TEXT, annual_leave_days INTEGER DEFAULT 20, used_leave_days INTEGER DEFAULT 0)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY, employee_name TEXT, leave_type TEXT,
            start_date TEXT, end_date TEXT, reason TEXT, status TEXT DEFAULT 'pending',
            request_date TEXT DEFAULT CURRENT_TIMESTAMP)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS employers (
            id INTEGER PRIMARY KEY, password_hash TEXT)''')
        
        conn.commit()
        conn.close()
        self.add_demo_data()
    
    def add_demo_data(self):
        if not self.get_all_employees():
            # Demo çalışanlar (şifre: 123456)
            for name in ["Ahmet Yılmaz", "Ayşe Demir", "Mehmet Kaya"]:
                self.add_employee(name, "123456", 20)
        
        # İşveren şifresi (admin123)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM employers')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO employers (password_hash) VALUES (?)', (hash_password("admin123"),))
            conn.commit()
        conn.close()
    
    def verify_employer(self, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM employers WHERE password_hash = ?', (hash_password(password),))
        result = cursor.fetchone()[0] > 0
        conn.close()
        return result
    
    def verify_employee(self, name, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM employees WHERE name = ? AND password_hash = ?', 
                      (name, hash_password(password)))
        result = cursor.fetchone()[0] > 0
        conn.close()
        return result
    
    def add_employee(self, name, password, annual_leave=20):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO employees (name, password_hash, start_date, annual_leave_days) VALUES (?, ?, ?, ?)',
                         (name, hash_password(password), datetime.now().strftime("%Y-%m-%d"), annual_leave))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def delete_employee(self, name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM employees WHERE name = ?', (name,))
        cursor.execute('DELETE FROM leave_requests WHERE employee_name = ?', (name,))
        conn.commit()
        conn.close()
    
    def get_all_employees(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name, start_date, annual_leave_days, used_leave_days FROM employees')
        employees = cursor.fetchall()
        conn.close()
        return [{'name': row[0], 'start_date': row[1], 'annual_leave_days': row[2], 'used_leave_days': row[3]} 
                for row in employees]
    
    def get_employee(self, name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name, start_date, annual_leave_days, used_leave_days FROM employees WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        return {'name': row[0], 'start_date': row[1], 'annual_leave_days': row[2], 'used_leave_days': row[3]} if row else None
    
    def add_leave_request(self, employee_name, leave_type, start_date, end_date, reason=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO leave_requests (employee_name, leave_type, start_date, end_date, reason) VALUES (?, ?, ?, ?, ?)',
                      (employee_name, leave_type, start_date, end_date, reason))
        conn.commit()
        conn.close()
    
    def get_employee_leaves(self, employee_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT leave_type, start_date, end_date, status FROM leave_requests WHERE employee_name = ? ORDER BY request_date DESC', (employee_name,))
        leaves = cursor.fetchall()
        conn.close()
        return [{'leave_type': row[0], 'start_date': row[1], 'end_date': row[2], 'status': row[3]} for row in leaves]
    
    def get_all_leave_requests(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, employee_name, leave_type, start_date, end_date, status FROM leave_requests ORDER BY request_date DESC')
        leaves = cursor.fetchall()
        conn.close()
        return [{'id': row[0], 'employee_name': row[1], 'leave_type': row[2], 'start_date': row[3], 'end_date': row[4], 'status': row[5]} for row in leaves]
    
    def update_leave_status(self, leave_id, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE leave_requests SET status = ? WHERE id = ?', (status, leave_id))
        conn.commit()
        conn.close()

db = SecureDatabase()

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/employee_login', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'POST':
        name = request.form.get('employee_name')
        password = request.form.get('password')
        if db.verify_employee(name, password):
            session['user_type'] = 'employee'
            session['user_name'] = name
            return redirect('/employee_panel')
        flash('Hatalı giriş bilgileri!', 'danger')
    
    employees = db.get_all_employees()
    return render_template_string(LOGIN_TEMPLATE, title="🔐 İşçi Girişi", show_employee_select=True, 
                                employees=employees, show_demo_info=False, bg_color="#56ab2f 0%, #a8e6cf 100%")

@app.route('/employer_login', methods=['GET', 'POST'])
def employer_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if db.verify_employer(password):
            session['user_type'] = 'employer'
            return redirect('/employer_panel')
        flash('Hatalı işveren şifresi!', 'danger')
    
    return render_template_string(LOGIN_TEMPLATE, title="🔐 İşveren Girişi", show_employee_select=False, 
                                employees=[], show_demo_info=True, bg_color="#ff6b6b 0%, #ffa726 100%")

@app.route('/employee_panel')
def employee_panel():
    if session.get('user_type') != 'employee':
        return redirect('/')
    
    employee = db.get_employee(session['user_name'])
    leaves = db.get_employee_leaves(session['user_name'])
    
    content = f'''
    <div class="row mb-4">
    <div class="col-md-6"><div class="card bg-primary text-white"><div class="card-body text-center">
    <h5>📅 Yıllık İzin</h5><h3>{employee['annual_leave_days']} Gün</h3></div></div></div>
    <div class="col-md-6"><div class="card bg-warning text-white"><div class="card-body text-center">
    <h5>✅ Kullanılan</h5><h3>{employee['used_leave_days']} Gün</h3></div></div></div>
    </div>
    
    <div class="card mb-4"><div class="card-header"><h5>📝 İzin Talebi</h5></div><div class="card-body">
    <form action="/add_leave_request" method="POST">
    <div class="row">
    <div class="col-md-4 mb-3"><select class="form-select" name="leave_type" required>
    <option value="Yıllık İzin">Yıllık İzin</option><option value="Hastalık İzni">Hastalık İzni</option>
    <option value="Mazeret İzni">Mazeret İzni</option></select></div>
    <div class="col-md-3 mb-3"><input type="date" class="form-control" name="start_date" required></div>
    <div class="col-md-3 mb-3"><input type="date" class="form-control" name="end_date" required></div>
    <div class="col-md-2 mb-3"><button type="submit" class="btn btn-success w-100">Gönder</button></div>
    </div>
    <textarea class="form-control" name="reason" placeholder="Açıklama" rows="2"></textarea>
    </form></div></div>
    
    <div class="card"><div class="card-header"><h5>📋 İzin Geçmişim</h5></div><div class="card-body">
    '''
    
    if leaves:
        content += '<div class="table-responsive"><table class="table table-striped"><thead><tr><th>Tür</th><th>Tarih</th><th>Durum</th></tr></thead><tbody>'
        for leave in leaves:
            status_badge = {'approved': 'success">✅ Onaylandı', 'rejected': 'danger">❌ Reddedildi', 'pending': 'warning">⏳ Beklemede'}
            content += f'<tr><td>{leave["leave_type"]}</td><td>{leave["start_date"]} - {leave["end_date"]}</td><td><span class="badge bg-{status_badge.get(leave["status"], "secondary")}</span></td></tr>'
        content += '</tbody></table></div>'
    else:
        content += '<p class="text-muted text-center">Henüz izin talebiniz yok.</p>'
    
    content += '</div></div>'
    
    return render_template_string(PANEL_TEMPLATE, title=f"👤 {employee['name']} - İşçi Paneli", content=content, bg_color="#56ab2f 0%, #a8e6cf 100%")

@app.route('/employer_panel')
def employer_panel():
    if session.get('user_type') != 'employer':
        return redirect('/')
    
    employees = db.get_all_employees()
    leave_requests = db.get_all_leave_requests()
    
    content = f'''
    <div class="card mb-4"><div class="card-header"><h5>👤 Yeni Çalışan Ekle</h5></div><div class="card-body">
    <form action="/add_employee" method="POST">
    <div class="row">
    <div class="col-md-4 mb-3"><input type="text" class="form-control" name="name" placeholder="Ad" required></div>
    <div class="col-md-3 mb-3"><input type="password" class="form-control" name="password" placeholder="Şifre" required></div>
    <div class="col-md-3 mb-3"><input type="number" class="form-control" name="annual_leave" value="20" min="0"></div>
    <div class="col-md-2 mb-3"><button type="submit" class="btn btn-primary w-100">Ekle</button></div>
    </div></form></div></div>
    
    <div class="card mb-4"><div class="card-header"><h5>👥 Çalışanlar ({len(employees)})</h5></div><div class="card-body">
    '''
    
    if employees:
        content += '<div class="table-responsive"><table class="table table-striped"><thead><tr><th>Ad</th><th>İzin</th><th>Kullanılan</th><th>Kalan</th><th>İşlem</th></tr></thead><tbody>'
        for emp in employees:
            remaining = emp['annual_leave_days'] - emp['used_leave_days']
            content += f'''<tr><td><strong>{emp["name"]}</strong></td>
            <td><span class="badge bg-primary">{emp["annual_leave_days"]}</span></td>
            <td><span class="badge bg-warning">{emp["used_leave_days"]}</span></td>
            <td><span class="badge bg-success">{remaining}</span></td>
            <td><button class="btn btn-danger btn-sm" onclick="deleteEmployee('{emp["name"]}')">🗑️ Sil</button></td></tr>'''
        content += '</tbody></table></div>'
    else:
        content += '<p class="text-muted text-center">Henüz çalışan yok.</p>'
    
    content += '</div></div><div class="card"><div class="card-header"><h5>📋 İzin Talepleri</h5></div><div class="card-body">'
    
    if leave_requests:
        content += '<div class="table-responsive"><table class="table table-striped"><thead><tr><th>Çalışan</th><th>Tür</th><th>Tarih</th><th>Durum</th><th>İşlem</th></tr></thead><tbody>'
        for leave in leave_requests:
            status_badge = {'approved': 'success">✅ Onaylandı', 'rejected': 'danger">❌ Reddedildi', 'pending': 'warning">⏳ Beklemede'}
            content += f'''<tr><td><strong>{leave["employee_name"]}</strong></td>
            <td>{leave["leave_type"]}</td><td>{leave["start_date"]} - {leave["end_date"]}</td>
            <td><span class="badge bg-{status_badge.get(leave["status"], "secondary")}</span></td><td>'''
            
            if leave['status'] == 'pending':
                content += f'''<form action="/update_leave_status" method="POST" style="display:inline">
                <input type="hidden" name="leave_id" value="{leave["id"]}">
                <input type="hidden" name="status" value="approved">
                <button type="submit" class="btn btn-success btn-sm">✅</button></form>
                <form action="/update_leave_status" method="POST" style="display:inline">
                <input type="hidden" name="leave_id" value="{leave["id"]}">
                <input type="hidden" name="status" value="rejected">
                <button type="submit" class="btn btn-danger btn-sm">❌</button></form>'''
            
            content += '</td></tr>'
        content += '</tbody></table></div>'
    else:
        content += '<p class="text-muted text-center">Henüz izin talebi yok.</p>'
    
    content += '</div></div>'
    
    return render_template_string(PANEL_TEMPLATE, title="👔 İşveren Paneli", content=content, bg_color="#ff6b6b 0%, #ffa726 100%")

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if session.get('user_type') != 'employer':
        return redirect('/')
    
    name = request.form.get('name')
    password = request.form.get('password')
    annual_leave = int(request.form.get('annual_leave', 20))
    
    if db.add_employee(name, password, annual_leave):
        flash(f'{name} başarıyla eklendi!', 'success')
    else:
        flash('Çalışan zaten kayıtlı!', 'danger')
    
    return redirect('/employer_panel')

@app.route('/delete_employee', methods=['POST'])
def delete_employee():
    if session.get('user_type') != 'employer':
        return redirect('/')
    
    name = request.form.get('employee_name')
    db.delete_employee(name)
    flash(f'{name} silindi!', 'success')
    return redirect('/employer_panel')

@app.route('/add_leave_request', methods=['POST'])
def add_leave_request():
    if session.get('user_type') != 'employee':
        return redirect('/')
    
    employee_name = session['user_name']
    leave_type = request.form.get('leave_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    reason = request.form.get('reason', '')
    
    db.add_leave_request(employee_name, leave_type, start_date, end_date, reason)
    flash('İzin talebi oluşturuldu!', 'success')
    return redirect('/employee_panel')

@app.route('/update_leave_status', methods=['POST'])
def update_leave_status():
    if session.get('user_type') != 'employer':
        return redirect('/')
    
    leave_id = request.form.get('leave_id')
    status = request.form.get('status')
    
    db.update_leave_status(leave_id, status)
    flash(f'İzin talebi {status}!', 'success')
    return redirect('/employer_panel')

@app.route('/logout')
def logout():
    session.clear()
    flash('Çıkış yapıldı!', 'success')
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
