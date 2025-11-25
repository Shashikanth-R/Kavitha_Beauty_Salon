from flask import Flask, render_template, redirect, url_for, session, request, flash
import mysql.connector
import sqlite3
import os
from config import Config, ProductionConfig, DevelopmentConfig
from flask_mail import Mail, Message

# Initialize Flask
app = Flask(__name__)
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)

# Initialize Mail
mail = Mail(app)

# Database connection
def get_db_connection():
    if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
        # Use SQLite for free hosting
        conn = sqlite3.connect('beauty_salon.db')
        conn.row_factory = sqlite3.Row
        return conn, conn.cursor()
    else:
        # Use MySQL for local development
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        return conn, conn.cursor(dictionary=True)

# Initialize database tables
def init_db():
    conn, cursor = get_db_connection()
    
    if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
        # SQLite syntax
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            service TEXT NOT NULL,
            date TEXT NOT NULL,
            slot TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            total_amount REAL DEFAULT 0,
            amount_paid REAL DEFAULT 0,
            confirmed INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create default admin user for production
        cursor.execute("SELECT * FROM users WHERE username=? AND is_admin=1", ('admin',))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'admin123', 1))
    else:
        # MySQL syntax
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(30) NOT NULL,
            service VARCHAR(100) NOT NULL,
            date DATE NOT NULL,
            slot VARCHAR(20) NOT NULL,
            completed TINYINT(1) DEFAULT 0,
            total_amount DECIMAL(10,2) DEFAULT 0,
            amount_paid DECIMAL(10,2) DEFAULT 0,
            confirmed TINYINT(1) DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create default admin user for development
        cursor.execute("SELECT * FROM users WHERE username=%s AND is_admin=TRUE", ('admin',))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)", ('admin', 'admin123', True))
    
    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        date = request.form['date']
        slot = request.form['slot']
        selected_services = request.form.getlist('services')

        service_prices = {
            '399 Offer': 399,
            '599 Offer': 599,
            '799 Offer': 799,
            'Full arm waxing': 249,
            'Under arm waxing': 99,
            'Half leg waxing': 199
        }
        total = sum(service_prices.get(s, 0) for s in selected_services)
        service_str = ', '.join(selected_services)

        conn, cursor = get_db_connection()
        if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
            cursor.execute(
                "INSERT INTO appointments (name, email, phone, service, date, slot, total_amount, amount_paid) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, email, phone, service_str, date, slot, total, 0))
        else:
            cursor.execute(
                "INSERT INTO appointments (name, email, phone, service, date, slot, total_amount, amount_paid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (name, email, phone, service_str, date, slot, total, 0))
        conn.commit()
        conn.close()

        flash('Successfully booked appointment!', 'success')
        return redirect(url_for('booking'))

    return render_template('booking.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        conn, cursor = get_db_connection()
        if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
            cursor.execute(
                "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
                (name, email, message))
        else:
            cursor.execute(
                "INSERT INTO contacts (name, email, message) VALUES (%s, %s, %s)",
                (name, email, message))
        conn.commit()
        conn.close()
        flash('Your message was sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn, cursor = get_db_connection()
    
    if request.method == 'POST':
        appt_id = request.form.get('appt_id')
        completed = 1 if request.form.get('completed') == 'on' else 0
        
        if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
            cursor.execute("UPDATE appointments SET completed = ? WHERE id = ?", (completed, appt_id))
            if 'amount_paid' in request.form:
                amount_paid = int(request.form.get('amount_paid'))
                cursor.execute("UPDATE appointments SET amount_paid = ? WHERE id = ?", (amount_paid, appt_id))
        else:
            cursor.execute("UPDATE appointments SET completed = %s WHERE id = %s", (completed, appt_id))
            if 'amount_paid' in request.form:
                amount_paid = int(request.form.get('amount_paid'))
                cursor.execute("UPDATE appointments SET amount_paid = %s WHERE id = %s", (amount_paid, appt_id))
        conn.commit()

    cursor.execute("SELECT * FROM appointments ORDER BY date, slot")
    appointments = cursor.fetchall()
    cursor.execute("SELECT * FROM contacts ORDER BY submitted_at DESC")
    messages = cursor.fetchall()
    conn.close()
    return render_template('admin.html', appointments=appointments, messages=messages)

@app.route('/admin/confirm', methods=['POST'])
def admin_confirm():
    appt_id = request.form.get('appt_id')
    confirmed = int(request.form.get('confirmed', 0))
    
    conn, cursor = get_db_connection()
    if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
        cursor.execute("UPDATE appointments SET confirmed = ? WHERE id = ?", (confirmed, appt_id))
        conn.commit()
        cursor.execute("SELECT name, email, slot, service, date FROM appointments WHERE id = ?", (appt_id,))
    else:
        cursor.execute("UPDATE appointments SET confirmed = %s WHERE id = %s", (confirmed, appt_id))
        conn.commit()
        cursor.execute("SELECT name, email, slot, service, date FROM appointments WHERE id = %s", (appt_id,))
    
    appt = cursor.fetchone()

    if not appt:
        flash('Appointment not found.', 'error')
        conn.close()
        return redirect(url_for('admin'))

    recipient = appt['email']

    if confirmed:
        subject = "Your Booking is Confirmed!"
        body = (
            f"Dear {appt['name']},\n\n"
            f"Your booking for {appt['service']} on {appt['date']} at {appt['slot']} is confirmed!\n"
            f"We look forward to welcoming you.\n\n"
            f"Thank you for choosing Kavitha Beauty Salon!\n\n"
            f"Best wishes,\nKavitha Beauty Salon Team"
        )
    else:
        subject = "Your Booking is Cancelled"
        body = (
            f"Dear {appt['name']},\n\n"
            f"We regret to inform you that your booking for {appt['service']} on {appt['date']} at {appt['slot']} "
            f"has been cancelled.\n\n"
            f"Please contact us for further details.\n\n"
            f"Best wishes,\nKavitha Beauty Salon Team"
        )

    try:
        msg = Message(subject=subject, recipients=[recipient], body=body)
        mail.send(msg)
        flash(f'{"Confirmation" if confirmed else "Cancellation"} email sent successfully!', 'success')
    except Exception as e:
        flash(f'Failed to send email: {e}', 'error')

    conn.close()
    return redirect(url_for('admin'))

@app.route('/loginorregister', methods=['GET'])
def loginorregister():
    return render_template('loginorregister.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    
    conn, cursor = get_db_connection()
    try:
        if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, 0))
        else:
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)", (username, password, False))
        conn.commit()
        flash('Successfully registered!', 'success')
    except Exception:
        flash('Username already exists.', 'error')
    finally:
        conn.close()
    return redirect(url_for('loginorregister'))

@app.route('/userlogin', methods=['POST'])
def userlogin():
    username = request.form['username']
    password = request.form['password']
    
    conn, cursor = get_db_connection()
    if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
        cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND is_admin=0", (username, password))
    else:
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND is_admin=FALSE", (username, password))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user'] = username
        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    else:
        flash('Invalid credentials.', 'error')
        return redirect(url_for('loginorregister'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn, cursor = get_db_connection()
        if app.config.get('DATABASE_URL') or os.environ.get('FLASK_ENV') == 'production':
            cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND is_admin=1", (username, password))
        else:
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND is_admin=TRUE", (username, password))
        
        admin = cursor.fetchone()
        conn.close()
        
        if admin:
            session['admin'] = username
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid admin credentials.', 'error')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ---------------- RUN ---------------- #

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])