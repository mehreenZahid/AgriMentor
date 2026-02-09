from flask import session, redirect, url_for

from flask import Flask, render_template, request
import os
import mysql.connector

app = Flask(__name__, static_folder='static', static_url_path='/static')

app.secret_key = "agrimentor_secret"


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL connection

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",        # agar password hai to daalo
    database="agrimentor",
    port=3307
)


cursor = db.cursor()

@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    image = request.files['image']

    if image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_path)

        query = "INSERT INTO uploads (image_name, status) VALUES (%s, %s)"
        values = (image.filename, "pending")
        cursor.execute(query, values)
        db.commit()

        return "Image uploaded & data saved to database!"

    return "No image uploaded"

@app.route('/requests')
def view_requests():
    cursor.execute("SELECT * FROM uploads")
    data = cursor.fetchall()
    return render_template('requests.html', uploads=data)


@app.route('/verify/<int:id>')
def verify(id):
    query = "UPDATE uploads SET status = 'verified' WHERE id = %s"
    cursor.execute(query, (id,))
    db.commit()
    return "Request verified successfully!"

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    query = "SELECT role FROM users WHERE username=%s AND password=%s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    if user:
        session['role'] = user[0]

        if user[0] == 'user':
            return redirect(url_for('home'))
        elif user[0] == 'sub_admin':
            return redirect(url_for('view_requests'))
        else:
            return "Admin logged in"
    else:
        return "Invalid login"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


if __name__ == '__main__':
    app.run(debug=True)