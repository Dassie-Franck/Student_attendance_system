from flask import Flask
from sqlalchemy import text
from app.database.connDB import db
from app.services.user_service import UserService
from app.services.student_service import EtudiantService
from app.models.user import UserRole

# ----------------------- Initialisation Flask & DB -----------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/SystemPresence"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.app_context().push()  # nécessaire pour utiliser db hors routes

# ----------------------- Nettoyage tables pour test -----------------------
# db.session.execute(text("DELETE FROM cours"))
# db.session.execute(text("DELETE FROM etudiant"))
# db.session.execute(text("DELETE FROM users"))
# db.session.commit()
# print("Tables vidées \n")

# ----------------------- 1. Créer un Responsable -----------------------
responsable = UserService.create_user(
    nom="KAZE",
    prenom="talk",
    email="kaze@gmail.com",
    password="qwerty123456",
    role=UserRole.HEAD.value,
    filiere="telecom"
)
print(f"Responsable créé : {responsable.nom} ({responsable.role})")

# # ----------------------- 2. Créer un Enseignant via Responsable -----------------------
# enseignant = None
# if UserService.can_crud_user(responsable):
#     enseignant = UserService.create_user(
#         nom="gerad",
#         prenom="lionnel",
#         email="lionnel@gmail.com",
#         password="lionnel",
#         role=UserRole.ENSEIGNANT.value,
#         filiere="ucac",
#     )
#     print(f"Enseignant créé par Responsable : {enseignant.nom} ({enseignant.role})")

# ----------------------- 3. Créer un Délégué via Responsable -----------------------
# delegue = None
# if UserService.can_crud_user(responsable):
#     delegue = UserService.create_user(
#         nom="gfried",
#         prenom="victoire",
#         email="gfreid@gmail.com",
#         password="gfreid",
#         role=UserRole.DELEGUE.value,
#         filiere="ing5",
#     )
#     print(f"Délégué créé par Responsable : {delegue.nom} ({delegue.role})")

# ----------------------- 4. Création Étudiants via Responsable -----------------------
# if UserService.can_crud_user(responsable):
#     etudiant1 = EtudiantService.add_student("julio", "yvan", "julio@gmail.com", "ingG","2032-2041")
#     etudiant2 = EtudiantService.add_student("brother", "daves", "daves@gmail.com", "sciences","2020-2051")
#     print(f"Étudiants créés : {etudiant1.nom}, {etudiant2.nom}")

# ----------------------- 5. Tester login -----------------------
try:
    user = UserService.login("talk@gmail.com", "qwerty123456")
    print(f"Login réussi : {user.nom} ({user.role}, {user.mot_de_passe})")
except Exception as e:
    print("Login échoué :", e)

# ----------------------- 6. Vérifier droits -----------------------
print("\n--- Vérification des droits ---")
print("Responsable peut CRUD user :", UserService.can_crud_user(responsable))
# print("Enseignant peut CRUD user :", UserService.can_crud_user(enseignant) if enseignant else False)
# print("Délégué peut CRUD user :", UserService.can_crud_user(delegue) if delegue else False)
# print("Enseignant peut créer cours :", UserService.can_create_course(enseignant) if enseignant else False)
# print("Délégué peut lancer scan :", UserService.can_take_attendance(delegue) if delegue else False)
# print("Responsable peut lancer scan :", UserService.can_take_attendance(responsable))


# ----------------------- 7. Lister tous les étudiants -----------------------
all_etudiants = EtudiantService.get_all_students()
print("Étudiants dans la DB :", [e.matricule for e in all_etudiants])

print("\n Test complet terminé !")
