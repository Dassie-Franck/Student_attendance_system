from app import app, db, User

with app.app_context():
    # Crée les tables (si tu viens de supprimer le fichier .db)
    db.create_all()

    # On vérifie si l'admin existe déjà (par email maintenant)
    admin = User.query.filter_by(email='admin@3il.com').first()

    if not admin:
        # On crée l'admin avec les NOUVEAUX champs (prenom, email, mot_de_passe)
        new_admin = User(
            prenom='Super Admin',
            email='admin@3il.com',          # <--- Ce sera ton LOGIN
            mot_de_passe='admin123',        # <--- Ce sera ton MOT DE PASSE
            role='respoFiliere'             # <--- Le rôle exact que tu as mis dans ta route login
        )
        
        db.session.add(new_admin)
        db.session.commit()
        print("✅ Admin créé avec succès !")
        print("👉 Login : admin@3il.com")
        print("👉 Passe : admin123")
    else:
        print("⚠️ L'admin existe déjà.")