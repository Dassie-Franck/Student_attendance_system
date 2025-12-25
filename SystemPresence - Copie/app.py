from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from datetime import date

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'super_cle_secrete'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)


#    MODÈLES (LES TABLES DE LA BASE)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prenom = db.Column(db.String(100), nullable=False) 
    nom = db.Column(db.String(100), nullable=True) # Ajouté pour add_teacher
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='delegue')

class Etudiant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    photo_path = db.Column(db.String(200), nullable=True) 

class Cours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    semestre = db.Column(db.String(20), nullable=False)


#                ROUTES


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant')
        password = request.form.get('password')

        # TEST ADMIN 
        if identifiant == "admin" and password == "admin":
            session['user_id'] = 1
            session['role'] = 'admin'
            session['prenom'] = "Super Admin"
            return redirect(url_for('admin_dashboard'))

        # TEST ENSEIGNANT 
        elif "prof@" in identifiant:
            session['user_id'] = 2
            session['role'] = 'enseignant'
            return redirect(url_for('dashboard_enseignant'))

        # TEST DÉLÉGUÉ 
        elif identifiant.startswith('25GI'):
            session['user_id'] = 3
            session['role'] = 'delegue'
            return redirect(url_for('dashboard_delegue'))

    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/etudiants')
def manage_students():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('manage_students.html', students=Etudiant.query.all())

@app.route('/mon-espace-prof')
def manage_teachers():
    if 'user_id' not in session: return redirect(url_for('login'))

    # On filtre par 'enseignant' pour correspondre à add_teacher
    teachers = User.query.filter_by(role='enseignant').all()
    return render_template('manage_teachers.html', teachers=teachers)

@app.route('/ajouter-enseignant', methods=['GET', 'POST'])
def add_teacher():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        u = User(
            nom=request.form['nom'],
            prenom=request.form['prenom'],
            email=request.form['email'],
            mot_de_passe=request.form['password'],
            role='enseignant'
        )
        db.session.add(u)
        db.session.commit()
        return redirect(url_for('manage_teachers'))
    return render_template('add_teacher.html')

@app.route('/cours')
def manage_cours():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('manage_cours.html', courses=Cours.query.all())

@app.route('/ajouter-cours', methods=['GET', 'POST'])
def add_cours():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        c = Cours(
            nom=request.form['nom'],
            semestre=request.form['semestre'],
            user_id=request.form['user_id']
        )
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('manage_cours'))
    profs = User.query.filter_by(role='enseignant').all()
    return render_template('add_cours.html', profs=profs)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        file = request.files['photo']
        filename = None
        if file:
            filename = secure_filename(f"{nom}_{prenom}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_student = Etudiant(nom=nom, prenom=prenom, photo_path=filename)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('manage_students'))
    return render_template('add_student.html')

@app.route('/manage_delegates')
def manage_delegates():
    if 'user_id' not in session: return redirect(url_for('login'))
    delegues = User.query.filter_by(role='delegue').all()
    return render_template('manage_delegates.html', delegues=delegues)

@app.route('/add_delegate', methods=['GET', 'POST'])
def add_delegate():
    if request.method == 'POST':
        user_exist = User.query.filter_by(email=request.form['email']).first()
        if user_exist:
            return "Email déjà utilisé"
        new_del = User(
            prenom=request.form['prenom'], 
            email=request.form['email'], 
            mot_de_passe=request.form['password'], 
            role='delegue'
        )
        db.session.add(new_del)
        db.session.commit()
        return redirect(url_for('manage_delegates'))
    return render_template('add_delegate.html')

@app.route('/enseignant')
def dashboard_enseignant():
    if session.get('role') != 'enseignant': return redirect(url_for('login'))
    return render_template('dashboard_enseignant.html')

@app.route('/delegue')
def dashboard_delegue():
    if session.get('role') != 'delegue': return redirect(url_for('login'))
    return render_template('dashboard_delegue.html')

@app.route('/faire-appel')
def mark_attendance():
    if session.get('role') not in ['enseignant', 'delegue']: return redirect(url_for('login'))
    return render_template('mark_attendance.html')

@app.route('/view_attendance')
def view_attendance():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('view_attendance.html')

@app.route('/bilan_absences')
def bilan_absences():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('bilan_absences.html')

@app.route('/attendance_details')
def attendance_details():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('attendance_details.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)