#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
İzin Takip Sistemi - Railway.app Deployment
Bu dosya Railway'de otomatik çalışacak
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'izin-takip-railway-secret-key-2024')

class IzinDatabase:
    def __init__(self, db_path="izin_takip.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Veritabanı tablolarını oluştur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Çalışanlar tablosu
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
        
        # İzin talepleri tablosu
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
                approved_date TEXT,
                FOREIGN KEY (employee_name) REFERENCES employees (name)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # İlk çalıştırmada demo veriler ekle
        self.add_demo_data_if_empty()
    
    def add_demo_data_if_empty(self):
        """Eğer veritabanı boşsa demo veriler ekle"""
        employees = self.get_all_employees()
        if not employees:
            # Demo çalışanlar
            demo_employees = [
                ("Ahmet Yılmaz", "2023-01-15", 20),
                ("Ayşe Demir", "2023-03-01", 25),
                ("Mehmet Kaya", "2023-06-10", 20),
                ("Fatma Özkan", "2023-09-01", 22)
            ]
            
            for name, start_date, annual_leave in demo_employees:
                self.add_employee(name, start_date, annual_leave)
            
            # Demo izin talepleri
            demo_leaves = [
                ("Ahmet Yılmaz", "Yıllık İzin", "2024-08-15", "2024-08-20", "Tatil için"),
                ("Ayşe Demir", "Hastalık İzni", "2024-08-10", "2024-08-12", "Grip"),
                ("Mehmet Kaya", "Mazeret İzni", "2024-08-05", "2024-08-06", "Kişisel işler"),
            ]
            
            for emp_name, leave_type, start_date, end_date, reason in demo_leaves:
                self.add_leave_request(emp_name, leave_type, start_date, end_date, reason)
    
    def add_employee(self, name, start_date=None, annual_leave_days=20):
        """Yeni çalışan ekle"""
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO employees (name, start_date, annual_leave_days)
                VALUES (?, ?, ?)
            ''', (name, start_date, annual_leave_days))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_all_employees(self):
        """Tüm çalışanları getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'name', 'start_date', 'annual_leave_days', 'used_leave_days', 'created_at']
        return [dict(zip(columns, row)) for row in employees]
    
    def get_employee(self, name):
        """Belirli bir çalışanı getir"""
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
        """İzin talebi ekle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO leave_requests (employee_name, leave_type, start_date, end_date, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (employee_name, leave_type, start_date, end_date, reason))
        
        conn.commit()
        conn.close()
        return True
    
    def get_employee_leaves(self, employee_name):
        """Çalışanın izin taleplerini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM leave_requests 
            WHERE employee_name = ? 
            ORDER BY request_date DESC
        ''', (employee_name,))
        
        leaves = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'employee_name', 'leave_type', 'start_date', 'end_date', 'reason', 'status', 'request_date', 'approved_by', 'approved_date']
        return [dict(zip(columns, row)) for row in leaves]
    
    def get_all_leave_requests(self):
        """Tüm izin taleplerini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM leave_requests 
            ORDER BY request_date DESC
        ''')
        
        leaves = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'employee_name', 'leave_type', 'start_date', 'end_date', 'reason', 'status', 'request_date', 'approved_by', 'approved_date']
        return [dict(zip(columns, row)) for row in leaves]
    
    def update_leave_status(self, leave_id, status, approved_by=None):
        """İzin talebinin durumunu güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        approved_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status != 'pending' else None
        
        cursor.execute('''
            UPDATE leave_requests 
            SET status = ?, approved_by = ?, approved_date = ?
            WHERE id = ?
        ''', (status, approved_by, approved_date, leave_id))
        
        conn.commit()
        conn.close()
        return True

# Veritabanı bağlantısı
db = IzinDatabase()

@app.route('/')
def index():
    """Ana sayfa - Giriş seçimi"""
    return render_template('web_index.html')

@app.route('/employee', methods=['GET', 'POST'])
def employee_panel():
    """İşçi paneli"""
    if request.method == 'POST':
        employee_name = request.form.get('employee_name')
        employee = db.get_employee(employee_name)
        if employee:
            leaves = db.get_employee_leaves(employee_name)
            return render_template('web_employee.html', employee=employee, leaves=leaves)
        else:
            flash('Çalışan bulunamadı!', 'danger')
    
    employees = db.get_all_employees()
    return render_template('web_employee_login.html', employees=employees)

@app.route('/employer')
def employer_panel():
    """İşveren paneli"""
    employees = db.get_all_employees()
    leave_requests = db.get_all_leave_requests()
    return render_template('web_employer.html', employees=employees, leave_requests=leave_requests)

@app.route('/add_employee', methods=['POST'])
def add_employee():
    """Yeni çalışan ekle"""
    name = request.form.get('name')
    annual_leave = int(request.form.get('annual_leave', 20))
    
    if db.add_employee(name, annual_leave_days=annual_leave):
        flash(f'{name} başarıyla eklendi!', 'success')
    else:
        flash('Çalışan zaten kayıtlı!', 'danger')
    
    return redirect(url_for('employer_panel'))

@app.route('/add_leave_request', methods=['POST'])
def add_leave_request():
    """İzin talebi ekle"""
    employee_name = request.form.get('employee_name')
    leave_type = request.form.get('leave_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    reason = request.form.get('reason', '')
    
    if db.add_leave_request(employee_name, leave_type, start_date, end_date, reason):
        flash('İzin talebi başarıyla oluşturuldu!', 'success')
    else:
        flash('İzin talebi oluşturulamadı!', 'danger')
    
    return redirect(url_for('employee_panel'))

@app.route('/update_leave_status', methods=['POST'])
def update_leave_status():
    """İzin talebini onayla/reddet"""
    leave_id = request.form.get('leave_id')
    status = request.form.get('status')
    approved_by = request.form.get('approved_by', 'İşveren')
    
    if db.update_leave_status(leave_id, status, approved_by):
        flash(f'İzin talebi {status} durumuna güncellendi!', 'success')
    else:
        flash('Güncelleme başarısız!', 'danger')
    
    return redirect(url_for('employer_panel'))

@app.route('/api/employees')
def api_employees():
    """API: Çalışanları JSON olarak döndür"""
    employees = db.get_all_employees()
    return jsonify(employees)

@app.route('/api/leaves/<employee_name>')
def api_employee_leaves(employee_name):
    """API: Çalışanın izinlerini JSON olarak döndür"""
    leaves = db.get_employee_leaves(employee_name)
    return jsonify(leaves)

@app.route('/health')
def health_check():
    """Sağlık kontrolü"""
    return jsonify({"status": "healthy", "message": "İzin Takip Sistemi çalışıyor!"})

if __name__ == '__main__':
    # Railway için port ayarı
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
