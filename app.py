#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
İzin Takip Sistemi - Tek Dosya Versiyonu
Bu dosyayı GitHub'a yükle ve Railway'de deploy et
"""

import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'izin-takip-railway-secret-key-2024')

# HTML Templates (inline)
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>İzin Takip Sistemi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .login-container { background: rgba(255, 255, 255, 0.95); border-radius: 20px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); }
        .btn-custom { border-radius: 15px; padding: 15px 30px; font-size: 1.2rem; font-weight: 600; }
        .btn-employee { background: linear-gradient(45deg, #56ab2f, #a8e6cf); border: none; color: white; }
        .btn-employer { background: linear-gradient(45deg, #ff6b6b, #ffa726); border: none; color: white; }
    </style>
</head>
<body>
    <div class="container-fluid d-flex align-items-center justify-content-center min-vh-100">
        <div class="login-container p-5 text-center" style="max-width: 500px; width: 90%;">
            <h1 class="mb-4">📋 İzin Takip Sistemi</h1>
            <p class="text-muted mb-4">Giriş türünüzü seçiniz</p>
            <div class="d-grid gap-3">
                <a href="/employee" class="btn btn-employee btn-custom">👤 İşçi Girişi</a>
                <a href="/employer" class="btn btn-employer btn-custom">👔 İşveren Girişi</a>
            </div>
            <div class="mt-4">
                <small class="text-muted">📱 Mobil uyumlu web arayüzü</small>
            </div>
        </div>
    </div>
</body>
</html>
'''

EMPLOYEE_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>İşçi Girişi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); min-height: 100vh; }
        .login-form { background: rgba(255, 255, 255, 0.95); border-radius: 20px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); }
    </style>
</head>
<body>
    <div class="container-fluid d-flex align-items-center justify-content-center min-vh-100">
        <div class="login-form p-5" style="max-width: 500px; width: 90%;">
            <h2 class="text-center mb-4">👤 İşçi Girişi</h2>
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
                <div class="mb-3">
                    <label class="form-label">Çalışan Adı</label>
                    <select class="form-select" name="employee_name" required>
                        <option value="">Seçiniz...</option>
                        {% for employee in employees %}
                            <option value="{{ employee.name }}">{{ employee.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-success btn-lg">Giriş Yap</button>
                    <a href="/" class="btn btn-outline-secondary">← Ana Sayfa</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

EMPLOYEE_PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>İşçi Paneli</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); min-height: 100vh; }
        .panel-container { background: rgba(255, 255, 255, 0.95); border-radius: 20px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); }
    </style>
</head>
<body>
    <div class="container my-4">
        <div class="panel-container p-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>👤 {{ employee.name }} - İşçi Paneli</h2>
                <a href="/" class="btn btn-outline-secondary">← Ana Sayfa</a>
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
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card bg-primary text-white">
                        <div class="card-body text-center">
                            <h5>📅 Yıllık İzin Hakkı</h5>
                            <h3>{{ employee.annual_leave_days }} Gün</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card bg-warning text-white">
                        <div class="card-body text-center">
                            <h5>✅ Kullanılan İzin</h5>
                            <h3>{{ employee.used_leave_days }} Gün</h3>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header"><h5>📝 Yeni İzin Talebi</h5></div>
                <div class="card-body">
                    <form action="/add_leave_request" method="POST">
                        <input type="hidden" name="employee_name" value="{{ employee.name }}">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">İzin Türü</label>
                                <select class="form-select" name="leave_type" required>
                                    <option value="Yıllık İzin">Yıllık İzin</option>
                                    <option value="Hastalık İzni">Hastalık İzni</option>
                                    <option value="Mazeret İzni">Mazeret İzni</option>
                                </select>
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">Başlangıç</label>
                                <input type="date" class="form-control" name="start_date" required>
                            </div>
                            <div class="col-md-3 mb-3">
                                <label class="form-label">Bitiş</label>
                                <input type="date" class="form-control" name="end_date" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Açıklama</label>
                            <textarea class="form-control" name="reason" rows="2"></textarea>
                        </div>
                        <button type="submit" class="btn btn-success">📤 İzin Talebi Gönder</button>
                    </form>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header"><h5>📋 İzin Geçmişim</h5></div>
                <div class="card-body">
                    {% if leaves %}
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr><th>İzin Türü</th><th>Tarih</th><th>Durum</th></tr>
                                </thead>
                                <tbody>
                                    {% for leave in leaves %}
                                        <tr>
                                            <td>{{ leave.leave_type }}</td>
                                            <td>{{ leave.start_date }} - {{ leave.end_date }}</td>
                                            <td>
                                                {% if leave.status == 'approved' %}
                                                    <span class="badge bg-success">✅ Onaylandı</span>
                                                {% elif leave.status == 'rejected' %}
                                                    <span class="badge bg-danger">❌ Reddedildi</span>
                                                {% else %}
                                                    <span class="badge bg-warning">⏳ Beklemede</span>
                                                {% endif %}
                                            </td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-muted text-center">Henüz izin talebiniz yok.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

EMPLOYER_PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>İşveren Paneli</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%); min-height: 100vh; }
        .panel-container { background: rgba(255, 255, 255, 0.95); border-radius: 20px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); }
    </style>
</head>
<body>
    <div class="container my-4">
        <div class="panel-container p-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>👔 İşveren Paneli</h2>
                <a href="/" class="btn btn-outline-secondary">← Ana Sayfa</a>
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
            
            <div class="card mb-4">
                <div class="card-header"><h5>👤 Yeni Çalışan Ekle</h5></div>
                <div class="card-body">
                    <form action="/add_employee" method="POST">
                        <div class="row">
                            <div class="col-md-8 mb-3">
                                <input type="text" class="form-control" name="name" placeholder="Çalışan adı" required>
                            </div>
                            <div class="col-md-4 mb-3">
                                <input type="number" class="form-control" name="annual_leave" value="20" min="0">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">➕ Çalışan Ekle</button>
                    </form>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header"><h5>👥 Çalışanlar ({{ employees|length }})</h5></div>
                <div class="card-body">
                    {% if employees %}
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead><tr><th>Ad</th><th>Yıllık İzin</th><th>Kullanılan</th><th>Kalan</th></tr></thead>
                                <tbody>
                                    {% for emp in employees %}
                                        <tr>
                                            <td><strong>{{ emp.name }}</strong></td>
                                            <td><span class="badge bg-primary">{{ emp.annual_leave_days }}</span></td>
                                            <td><span class="badge bg-warning">{{ emp.used_leave_days }}</span></td>
                                            <td><span class="badge bg-success">{{ emp.annual_leave_days - emp.used_leave_days }}</span></td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-muted text-center">Henüz çalışan yok.</p>
                    {% endif %}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header"><h5>📋 İzin Talepleri</h5></div>
                <div class="card-body">
                    {% if leave_requests %}
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead><tr><th>Çalışan</th><th>Tür</th><th>Tarih</th><th>Durum</th><th>İşlem</th></tr></thead>
                                <tbody>
                                    {% for leave in leave_requests %}
                                        <tr>
                                            <td><strong>{{ leave.employee_name }}</strong></td>
                                            <td>{{ leave.leave_type }}</td>
                                            <td>{{ leave.start_date }} - {{ leave.end_date }}</td>
                                            <td>
                                                {% if leave.status == 'approved' %}
                                                    <span class="badge bg-success">✅ Onaylandı</span>
                                                {% elif leave.status == 'rejected' %}
                                                    <span class="badge bg-danger">❌ Reddedildi</span>
                                                {% else %}
                                                    <span class="badge bg-warning">⏳ Beklemede</span>
                                                {% endif %}
                                            </td>
                                            <td>
                                                {% if leave.status == 'pending' %}
                                                    <form action="/update_leave_status" method="POST" style="display: inline;">
                                                        <input type="hidden" name="leave_id" value="{{ leave.id }}">
                                                        <input type="hidden" name="status" value="approved">
                                                        <button type="submit" class="btn btn-success btn-sm">✅</button>
                                                    </form>
                                                    <form action="/update_leave_status" method="POST" style="display: inline;">
                                                        <input type="hidden" name="leave_id" value="{{ leave.id }}">
                                                        <input type="hidden" name="status" value="rejected">
                                                        <button type="submit" class="btn btn-danger btn-sm">❌</button>
                                                    </form>
                                                {% endif %}
                                            </td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-muted text-center">Henüz izin talebi yok.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

class IzinDatabase:
    def __init__(self, db_path="izin_takip.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                start_date TEXT NOT NULL,
                annual_leave_days INTEGER DEFAULT 20,
                used_leave_days INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT NOT NULL,
                leave_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                request_date TEXT DEFAULT CURRENT_TIMESTAMP,
                approved_by TEXT,
                approved_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        self.add_demo_data_if_empty()
    
    def add_demo_data_if_empty(self):
        employees = self.get_all_employees()
        if not employees:
            demo_employees = [
                ("Ahmet Yılmaz", "2023-01-15", 20),
                ("Ayşe Demir", "2023-03-01", 25),
                ("Mehmet Kaya", "2023-06-10", 20),
                ("Fatma Özkan", "2023-09-01", 22)
            ]
            
            for name, start_date, annual_leave in demo_employees:
                self.add_employee(name, start_date, annual_leave)
            
            demo_leaves = [
                ("Ahmet Yılmaz", "Yıllık İzin", "2024-08-15", "2024-08-20", "Tatil"),
                ("Ayşe Demir", "Hastalık İzni", "2024-08-10", "2024-08-12", "Grip"),
            ]
            
            for emp_name, leave_type, start_date, end_date, reason in demo_leaves:
                self.add_leave_request(emp_name, leave_type, start_date, end_date, reason)
    
    def add_employee(self, name, start_date=None, annual_leave_days=20):
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO employees (name, start_date, annual_leave_days) VALUES (?, ?, ?)',
                         (name, start_date, annual_leave_days))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_all_employees(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'name', 'start_date', 'annual_leave_days', 'used_leave_days', 'created_at']
        return [dict(zip(columns, row)) for row in employees]
    
    def get_employee(self, name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees WHERE name = ?', (name,))
        employee = cursor.fetchone()
        conn.close()
        
        if employee:
            columns = ['id', 'name', 'start_date', 'annual_leave_days', 'used_leave_days', 'created_at']
            return dict(zip(columns, employee))
        return None
    
    def add_leave_request(self, employee_name, leave_type, start_date, end_date, reason=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO leave_requests (employee_name, leave_type, start_date, end_date, reason)
                         VALUES (?, ?, ?, ?, ?)''', (employee_name, leave_type, start_date, end_date, reason))
        conn.commit()
        conn.close()
        return True
    
    def get_employee_leaves(self, employee_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leave_requests WHERE employee_name = ? ORDER BY request_date DESC', (employee_name,))
        leaves = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'employee_name', 'leave_type', 'start_date', 'end_date', 'reason', 'status', 'request_date', 'approved_by', 'approved_date']
        return [dict(zip(columns, row)) for row in leaves]
    
    def get_all_leave_requests(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leave_requests ORDER BY request_date DESC')
        leaves = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'employee_name', 'leave_type', 'start_date', 'end_date', 'reason', 'status', 'request_date', 'approved_by', 'approved_date']
        return [dict(zip(columns, row)) for row in leaves]
    
    def update_leave_status(self, leave_id, status, approved_by=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        approved_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status != 'pending' else None
        cursor.execute('UPDATE leave_requests SET status = ?, approved_by = ?, approved_date = ? WHERE id = ?',
                      (status, approved_by, approved_date, leave_id))
        conn.commit()
        conn.close()
        return True

# Veritabanı
db = IzinDatabase()

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/employee', methods=['GET', 'POST'])
def employee_panel():
    if request.method == 'POST':
        employee_name = request.form.get('employee_name')
        employee = db.get_employee(employee_name)
        if employee:
            leaves = db.get_employee_leaves(employee_name)
            return render_template_string(EMPLOYEE_PANEL_TEMPLATE, employee=employee, leaves=leaves)
        else:
            flash('Çalışan bulunamadı!', 'danger')
    
    employees = db.get_all_employees()
    return render_template_string(EMPLOYEE_LOGIN_TEMPLATE, employees=employees)

@app.route('/employer')
def employer_panel():
    employees = db.get_all_employees()
    leave_requests = db.get_all_leave_requests()
    return render_template_string(EMPLOYER_PANEL_TEMPLATE, employees=employees, leave_requests=leave_requests)

@app.route('/add_employee', methods=['POST'])
def add_employee():
    name = request.form.get('name')
    annual_leave = int(request.form.get('annual_leave', 20))
    
    if db.add_employee(name, annual_leave_days=annual_leave):
        flash(f'{name} başarıyla eklendi!', 'success')
    else:
        flash('Çalışan zaten kayıtlı!', 'danger')
    
    return redirect(url_for('employer_panel'))

@app.route('/add_leave_request', methods=['POST'])
def add_leave_request():
    employee_name = request.form.get('employee_name')
    leave_type = request.form.get('leave_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    reason = request.form.get('reason', '')
    
    if db.add_leave_request(employee_name, leave_type, start_date, end_date, reason):
        flash('İzin talebi oluşturuldu!', 'success')
    else:
        flash('Hata oluştu!', 'danger')
    
    return redirect(url_for('employee_panel'))

@app.route('/update_leave_status', methods=['POST'])
def update_leave_status():
    leave_id = request.form.get('leave_id')
    status = request.form.get('status')
    
    if db.update_leave_status(leave_id, status, 'İşveren'):
        flash(f'İzin talebi {status}!', 'success')
    else:
        flash('Güncelleme başarısız!', 'danger')
    
    return redirect(url_for('employer_panel'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
