import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, redirect, session
import matplotlib.pyplot as plt
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ✅ DB PATH
def get_db_path():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(BASE_DIR, 'database.db')

# ✅ INIT DB
def init_db():
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  roll_no TEXT,
                  name TEXT,
                  math INTEGER,
                  science INTEGER,
                  english INTEGER,
                  avg REAL,
                  performance TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  password TEXT)''')

    conn.commit()
    conn.close()

init_db()

# ✅ LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = sqlite3.connect(get_db_path())
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()

        conn.close()

        if user:
            session['user'] = username
            return redirect('/home')
        else:
            return "Invalid Login"

    return render_template('login.html')


# ✅ HOME (Search Student)
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')
    return render_template('index.html')


# ✅ SEARCH EXISTING STUDENT
@app.route('/search', methods=['POST'])
def search():
    roll_no = request.form['roll_no']
    name = request.form['name']

    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    c.execute("SELECT * FROM students WHERE roll_no=? AND name=?", (roll_no, name))
    student = c.fetchone()

    conn.close()

    if student:
        math = student[3]
        science = student[4]
        english = student[5]

        marks = [math, science, english]
        subjects = ['Math', 'Science', 'English']

        # charts
        plt.figure()
        plt.bar(subjects, marks)
        plt.savefig('static/bar.png')
        plt.close()

        plt.figure()
        plt.pie(marks, labels=subjects, autopct='%1.1f%%')
        plt.savefig('static/pie.png')
        plt.close()

        return render_template('result.html',
                               name=student[2],
                               avg=student[6],
                               highest=max(marks),
                               weakest=subjects[marks.index(min(marks))],
                               performance=student[7],
                               suggestion="Based on saved data",
                               insight="Showing stored result",
                               top_subject=subjects[marks.index(max(marks))])
    else:
        return "Student not found ❌"


# ✅ ANALYZE + SAVE
@app.route('/analyze', methods=['POST'])
def analyze():
    roll_no = request.form['roll_no']
    name = request.form['name']
    math = int(request.form['math'])
    science = int(request.form['science'])
    english = int(request.form['english'])

    marks = [math, science, english]
    subjects = ['Math', 'Science', 'English']

    avg = round(sum(marks) / 3, 2)
    highest = max(marks)
    weakest = subjects[marks.index(min(marks))]

    # performance
    if avg >= 75:
        performance = "Excellent"
    elif avg >= 50:
        performance = "Average"
    else:
        performance = "Needs Improvement"

    # suggestion
    if weakest == "Math":
        suggestion = "Focus more on Math practice."
    elif weakest == "Science":
        suggestion = "Revise concepts in Science."
    else:
        suggestion = "Improve English skills."

    # DB (UPDATE or INSERT)
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    c.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,))
    existing = c.fetchone()

    if existing:
        c.execute("""
            UPDATE students
            SET name=?, math=?, science=?, english=?, avg=?, performance=?
            WHERE roll_no=?
        """, (name, math, science, english, avg, performance, roll_no))
    else:
        c.execute("""
            INSERT INTO students (roll_no, name, math, science, english, avg, performance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (roll_no, name, math, science, english, avg, performance))

    conn.commit()
    conn.close()

    # charts
    plt.figure()
    plt.bar(subjects, marks)
    plt.savefig('static/bar.png')
    plt.close()

    plt.figure()
    plt.pie(marks, labels=subjects, autopct='%1.1f%%')
    plt.savefig('static/pie.png')
    plt.close()

    # insights
    top_subject = subjects[marks.index(max(marks))]

    if avg >= 75:
        insight = "Overall performance is strong."
    elif avg >= 50:
        insight = "You can improve more."
    else:
        insight = "Focus on basics."

    return render_template('result.html',
                           name=name,
                           avg=avg,
                           highest=highest,
                           weakest=weakest,
                           performance=performance,
                           suggestion=suggestion,
                           insight=insight,
                           top_subject=top_subject)


# ✅ HISTORY
@app.route('/history')
def history():
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    c.execute("SELECT * FROM students")
    data = c.fetchall()

    conn.close()

    return render_template('history.html', data=data)


# ✅ DELETE
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    c.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/history')


# ✅ LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')
#show result
@app.route('/show_result')
def show_result():
    return render_template('show_result.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    # total students
    c.execute("SELECT COUNT(*) FROM students")
    total = c.fetchone()[0]

    # overall average
    c.execute("SELECT AVG(avg) FROM students")
    avg = c.fetchone()[0]

    # top student
    c.execute("SELECT name, avg FROM students ORDER BY avg DESC LIMIT 1")
    top = c.fetchone()

    conn.close()

    return render_template('dashboard.html',
                           total=total,
                           avg=round(avg,2) if avg else 0,
                           top=top)

if __name__ == '__main__':
    app.run(debug=True)