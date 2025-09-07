from flask import Flask, render_template, redirect, url_for, session
import mysql.connector
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Database connection
conn = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)
cursor = conn.cursor(dictionary=True)

# Ensure users table exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
)
''')
conn.commit()
# Ensure appointments table exists
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
try:
    cursor.execute('ALTER TABLE appointments ADD COLUMN confirmed TINYINT(1) DEFAULT 0')
    conn.commit()
except Exception:
    pass
for column in [
    'completed TINYINT(1) DEFAULT 0',
    'total_amount DECIMAL(10,2) DEFAULT 0',
    'amount_paid DECIMAL(10,2) DEFAULT 0'
]:
    try:
        cursor.execute(f'ALTER TABLE appointments ADD COLUMN {column}')
        conn.commit()
    except Exception:
        pass
# Rename amount_pending to total_amount if exists (for schema consistency)
try:
    cursor.execute("ALTER TABLE appointments CHANGE amount_pending total_amount DECIMAL(10,2) DEFAULT 0")
    conn.commit()
except Exception:
    pass
conn.commit()

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
        # Services selection - may be a list or a single string
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
        cursor.execute(
            "INSERT INTO appointments (name, email, phone, service, date, slot, total_amount, amount_paid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (name, email, phone, service_str, date, slot, total, 0))
        conn.commit()
        flash('Successfully booked appointment!', 'success')
        return redirect(url_for('booking'))
    return render_template('booking.html')

# Ensure contacts/messages table exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        cursor.execute(
            "INSERT INTO contacts (name, email, message) VALUES (%s, %s, %s)",
            (name, email, message))
        conn.commit()
        flash('Your message was sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        appt_id = request.form.get('appt_id')
        # Update completed
        completed = 1 if request.form.get('completed') == 'on' else 0
        cursor.execute("UPDATE appointments SET completed = %s WHERE id = %s", (completed, appt_id))
        # Update amount_paid based on dropdown
        if 'amount_paid' in request.form:
            amount_paid = int(request.form.get('amount_paid'))
            cursor.execute("UPDATE appointments SET amount_paid = %s WHERE id = %s", (amount_paid, appt_id))
        conn.commit()
    cursor.execute("SELECT * FROM appointments ORDER BY date, slot")
    appointments = cursor.fetchall()
    cursor.execute("SELECT * FROM contacts ORDER BY submitted_at DESC")
    messages = cursor.fetchall()
    return render_template('admin.html', appointments=appointments, messages=messages)

from flask import request, flash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.route('/admin/confirm', methods=['POST'])
def admin_confirm():
    appt_id = request.form.get('appt_id')
    confirmed = int(request.form.get('confirmed', 0))
    cursor.execute("UPDATE appointments SET confirmed = %s WHERE id = %s", (confirmed, appt_id))
    conn.commit()
    if confirmed:
        cursor.execute("SELECT name, email, slot, service, date FROM appointments WHERE id = %s", (appt_id,))
        appt = cursor.fetchone()
        if appt:
            sender_email = app.config.get('MAIL_SENDER', 'your_email@example.com')
            receiver_email = appt['email']
            subject = "Your Booking is Confirmed!"
            happy_message = f"Dear {appt['name']},\n\nYour booking for {appt['service']} on {appt['date']} at {appt['slot']} is confirmed!\nWe look forward to welcoming you.\n\nThank you for choosing Kavitha Beauty Salon!\n\nBest wishes,\nKavitha Beauty Salon Team"
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = subject
            msg.attach(MIMEText(happy_message, 'plain'))
            try:
                with smtplib.SMTP(app.config.get('MAIL_SERVER', 'smtp.gmail.com'), app.config.get('MAIL_PORT', 587)) as server:
                    server.starttls()
                    server.login(app.config.get('MAIL_USERNAME', 'your_email@example.com'), app.config.get('MAIL_PASSWORD', 'your_password'))
                    server.sendmail(sender_email, receiver_email, msg.as_string())
                flash('Confirmation email sent!', 'success')
            except Exception as e:
                flash(f'Failed to send confirmation email: {e}', 'error')
    return redirect(url_for('admin'))

@app.route('/loginorregister', methods=['GET'])
def loginorregister():
    return render_template('loginorregister.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    # By default, registering users are not admins
    try:
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)", (username, password, False))
        conn.commit()
        flash('Successfully registered!', 'success')
    except mysql.connector.errors.IntegrityError:
        flash('Username already exists.', 'error')
    return redirect(url_for('loginorregister'))

@app.route('/userlogin', methods=['POST'])
def userlogin():
    username = request.form['username']
    password = request.form['password']
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND is_admin=FALSE", (username, password))
    user = cursor.fetchone()
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
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND is_admin=TRUE", (username, password))
        admin = cursor.fetchone()
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


if __name__ == '__main__':
    # Bulk update amount_pending for existing appointments
    service_prices = {
        'Haircut': 300,
        'Facial': 500,
        'Bridal Makeup': 3000
    }
    cursor.execute("SELECT id, service FROM appointments")
    all_appts = cursor.fetchall()
    for appt in all_appts:
        price = service_prices.get(appt['service'], 0)
        cursor.execute("UPDATE appointments SET total_amount = %s WHERE id = %s", (price, appt['id']))
    conn.commit()
    app.run(debug=True)