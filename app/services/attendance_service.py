# app/services/attendance_service.py
from datetime import datetime

from sqlalchemy import func

from app.database.connDB import db
from app.models.attendance import PresenceModel
from app.models.course import CoursModel
from app.models.course_session import CoursSessionModel
from app.models.student import EtudiantModel
from app.models.user import UserModel
from app.repositories.attendance_repository import AttendanceRepository
import csv
import io


class AttendanceService:

    @staticmethod
    def get_today_attendance(user_id):
        """Récupère les listes de présence d'aujourd'hui"""
        try:
            sessions = AttendanceRepository.get_today_sessions_with_presence(user_id)
            print(f"DEBUG: {len(sessions)} sessions trouvées pour user {user_id}")

            attendance_lists = []
            for session in sessions:
                print(f"DEBUG: Traitement session {session.id}, Cours: {session.cours.nom}")

                # Récupérer tous les étudiants de la filière
                filiere = session.cours.filiere
                etudiants = AttendanceRepository.get_etudiants_by_filiere(filiere)

                # Créer un mapping des présences existantes
                presence_map = {p.etudiant_id: p for p in session.presences}
                print(f"DEBUG: {len(presence_map)} présences existantes dans la session")

                # Préparer la liste de présence
                attendance_list = []
                for etudiant in etudiants:
                    presence = presence_map.get(etudiant.id)
                    attendance_list.append({
                        'etudiant_id': etudiant.id,
                        'nom': etudiant.nom,
                        'prenom': etudiant.prenom,
                        'matricule': etudiant.matricule,
                        'filiere': etudiant.filiere,
                        'annee': etudiant.annee,
                        'statut': presence.statut if presence else 'A',
                        'presence_id': presence.id if presence else None,
                        'cours_session_id': session.id
                    })

                print(f"DEBUG: {len(attendance_list)} étudiants dans la liste")

                attendance_lists.append({
                    'session_id': session.id,
                    'session_date': session.date,
                    'session_seance': session.seance,
                    'cours_nom': session.cours.nom,
                    'cours_filiere': session.cours.filiere,
                    'cours_semestre': session.cours.semestre,
                    'attendance_list': attendance_list
                })

            return attendance_lists
        except Exception as e:
            print(f"ERREUR dans get_today_attendance: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_session_attendance(session_id):
        """Récupère la liste de présence d'une session spécifique"""
        try:
            print(f"DEBUG: Récupération session {session_id}")
            session = AttendanceRepository.get_session_with_presence(session_id)

            if not session:
                print(f"DEBUG: Session {session_id} non trouvée")
                return None

            print(f"DEBUG: Session trouvée - Cours: {session.cours.nom}, Filière: {session.cours.filiere}")

            # Récupérer tous les étudiants de la filière
            filiere = session.cours.filiere
            etudiants = AttendanceRepository.get_etudiants_by_filiere(filiere)

            if not etudiants:
                print(f"DEBUG: Aucun étudiant trouvé pour filière {filiere}")
                # Retourner quand même la structure avec liste vide
                return {
                    'session_id': session.id,
                    'session_date': session.date,
                    'session_seance': session.seance,
                    'cours_nom': session.cours.nom,
                    'cours_filiere': session.cours.filiere,
                    'cours_semestre': session.cours.semestre,
                    'attendance_list': []
                }

            # Créer un mapping des présences existantes
            presence_map = {p.etudiant_id: p for p in session.presences}
            print(f"DEBUG: {len(presence_map)} présences trouvées dans la session")

            # Préparer la liste de présence
            attendance_list = []
            for etudiant in etudiants:
                presence = presence_map.get(etudiant.id)
                attendance_list.append({
                    'etudiant_id': etudiant.id,
                    'nom': etudiant.nom,
                    'prenom': etudiant.prenom,
                    'matricule': etudiant.matricule,
                    'filiere': etudiant.filiere,
                    'annee': etudiant.annee,
                    'statut': presence.statut if presence else 'A',
                    'presence_id': presence.id if presence else None,
                    'cours_session_id': session.id
                })

            print(f"DEBUG: {len(attendance_list)} étudiants dans la liste finale")

            return {
                'session_id': session.id,
                'session_date': session.date,
                'session_seance': session.seance,
                'cours_nom': session.cours.nom,
                'cours_filiere': session.cours.filiere,
                'cours_semestre': session.cours.semestre,
                'attendance_list': attendance_list
            }
        except Exception as e:
            print(f"ERREUR dans get_session_attendance: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def update_attendance_status(data):
        """Met à jour le statut de présence d'un étudiant"""
        try:
            print(f"DEBUG: update_attendance_status - Données: {data}")
            etudiant_id = data.get('etudiant_id')
            cours_session_id = data.get('cours_session_id')
            statut = data.get('statut')

            if not all([etudiant_id, cours_session_id, statut]):
                return {'success': False, 'error': 'Données manquantes'}

            if statut not in ['P', 'A']:
                return {'success': False, 'error': 'Statut invalide'}

            presence = AttendanceRepository.create_or_update_presence(
                etudiant_id, cours_session_id, statut
            )

            return {
                'success': True,
                'presence_id': presence.id,
                'statut': presence.statut
            }
        except Exception as e:
            print(f"ERREUR dans update_attendance_status: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def generate_csv_data(session_id):
        """Génère les données CSV pour une session"""
        try:
            session_data = AttendanceService.get_session_attendance(session_id)
            if not session_data:
                return None

            # Créer un buffer pour le CSV
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            # En-tête du CSV
            writer.writerow(['LISTE DE PRESENCE'])
            writer.writerow([])
            writer.writerow([
                f"Cours: {session_data['cours_nom']}",
                f"Filière: {session_data['cours_filiere']}",
                f"Semestre: {session_data['cours_semestre']}"
            ])
            writer.writerow([
                f"Date: {session_data['session_date'].strftime('%d/%m/%Y')}",
                f"Séance: {session_data['session_seance']}"
            ])
            writer.writerow([])

            # En-tête des colonnes
            writer.writerow([
                'Matricule', 'Nom', 'Prénom', 'Filière', 'Année', 'Statut'
            ])

            # Données des étudiants
            for attendance in session_data['attendance_list']:
                statut = 'Présent' if attendance['statut'] == 'P' else 'Absent'
                writer.writerow([
                    attendance['matricule'],
                    attendance['nom'],
                    attendance['prenom'],
                    attendance['filiere'],
                    attendance['annee'],
                    statut
                ])

            return output.getvalue()
        except Exception as e:
            print(f"ERREUR dans generate_csv_data: {e}")
            return None

    @staticmethod
    def get_presences_filtrees(filiere=None, cours_id=None, etudiant_id=None,
                               date_debut=None, date_fin=None, statut=None):
        """
        Récupère les présences avec filtres
        """
        try:
            query = PresenceModel.query \
                .join(EtudiantModel, PresenceModel.etudiant_id == EtudiantModel.id) \
                .join(CoursSessionModel, PresenceModel.cours_session_id == CoursSessionModel.id) \
                .join(CoursModel, CoursSessionModel.cours_id == CoursModel.id) \
                .join(UserModel, CoursModel.user_id == UserModel.id)

            # Appliquer les filtres
            if filiere:
                query = query.filter(EtudiantModel.filiere == filiere)

            if cours_id:
                query = query.filter(CoursSessionModel.cours_id == cours_id)

            if etudiant_id:
                query = query.filter(PresenceModel.etudiant_id == etudiant_id)

            if date_debut and date_fin:
                query = query.filter(CoursSessionModel.date.between(date_debut, date_fin))
            elif date_debut:
                query = query.filter(CoursSessionModel.date >= date_debut)
            elif date_fin:
                query = query.filter(CoursSessionModel.date <= date_fin)

            if statut:
                query = query.filter(PresenceModel.statut == statut)

            # Trier par date (plus récent en premier)
            query = query.order_by(CoursSessionModel.date.desc(),
                                   CoursSessionModel.seance.desc())

            return query.all()

        except Exception as e:
            print(f"[ERROR] Erreur get_presences_filtrees: {str(e)}")
            return []

    @staticmethod
    def calculer_bilan_trimestriel(filiere=None, date_debut=None, date_fin=None):
        """
        Calcule le bilan trimestriel pour tous les étudiants
        Règle: 1 absence = 2h
        """
        try:
            # Base query pour les étudiants
            query = EtudiantModel.query

            if filiere:
                query = query.filter(EtudiantModel.filiere == filiere)

            etudiants = query.all()
            bilan_data = []

            for etudiant in etudiants:
                # Récupérer toutes les absences de l'étudiant
                absences = PresenceModel.query \
                    .join(CoursSessionModel, PresenceModel.cours_session_id == CoursSessionModel.id) \
                    .filter(
                    PresenceModel.etudiant_id == etudiant.id,
                    PresenceModel.statut == 'A'  # A = absent
                )

                if date_debut and date_fin:
                    absences = absences.filter(
                        CoursSessionModel.date.between(date_debut, date_fin)
                    )

                absences = absences.all()

                # Calculer les heures d'absence
                heures_absence = len(absences) * 2  # 2h par absence

                # Calculer le pourcentage de présence
                total_seances = PresenceModel.query \
                    .join(CoursSessionModel, PresenceModel.cours_session_id == CoursSessionModel.id) \
                    .filter(PresenceModel.etudiant_id == etudiant.id)

                if date_debut and date_fin:
                    total_seances = total_seances.filter(
                        CoursSessionModel.date.between(date_debut, date_fin)
                    )

                total_seances_count = total_seances.count()
                pourcentage_presence = 0
                if total_seances_count > 0:
                    pourcentage_presence = ((total_seances_count - len(absences)) / total_seances_count) * 100

                # Récupérer les cours concernés
                cours_absences = {}
                for absence in absences:
                    cours_nom = absence.session.cours.nom if absence.session and absence.session.cours else "Inconnu"
                    if cours_nom not in cours_absences:
                        cours_absences[cours_nom] = 0
                    cours_absences[cours_nom] += 2  # 2h par cours

                bilan_data.append({
                    'etudiant': etudiant,
                    'heures_absence': heures_absence,
                    'nombre_absences': len(absences),
                    'pourcentage_presence': round(pourcentage_presence, 2),
                    'cours_absences': cours_absences,
                    'absences_detail': absences[:10]  # 10 premières pour le détail
                })

            # Trier par nombre d'absences (décroissant)
            bilan_data.sort(key=lambda x: x['heures_absence'], reverse=True)

            return bilan_data

        except Exception as e:
            print(f"[ERROR] Erreur calcul bilan trimestriel: {str(e)}")
            return []

    @staticmethod
    def calculer_bilan_detaille_etudiant(etudiant_id, date_debut=None, date_fin=None):
        """
        Bilan détaillé pour un étudiant spécifique
        """
        try:
            etudiant = EtudiantModel.query.get(etudiant_id)
            if not etudiant:
                return None

            # Récupérer toutes les présences de l'étudiant
            presences = PresenceModel.query \
                .join(CoursSessionModel, PresenceModel.cours_session_id == CoursSessionModel.id) \
                .join(CoursModel, CoursSessionModel.cours_id == CoursModel.id) \
                .filter(PresenceModel.etudiant_id == etudiant_id)

            if date_debut and date_fin:
                presences = presences.filter(
                    CoursSessionModel.date.between(date_debut, date_fin)
                )

            presences = presences.order_by(CoursSessionModel.date.desc()).all()

            # Statistiques par cours
            stats_par_cours = {}
            for presence in presences:
                cours_nom = presence.session.cours.nom
                if cours_nom not in stats_par_cours:
                    stats_par_cours[cours_nom] = {
                        'total': 0,
                        'present': 0,
                        'absent': 0,
                        'heures_absence': 0,
                        'professeur': presence.session.cours.user
                    }

                stats_par_cours[cours_nom]['total'] += 1
                if presence.statut == 'P':
                    stats_par_cours[cours_nom]['present'] += 1
                else:
                    stats_par_cours[cours_nom]['absent'] += 1
                    stats_par_cours[cours_nom]['heures_absence'] += 2  # 2h par absence

            # Calculer les totaux
            total_presences = len(presences)
            total_absences = sum(1 for p in presences if p.statut == 'A')
            total_heures_absence = total_absences * 2

            # Pourcentage de présence
            pourcentage_presence = 0
            if total_presences > 0:
                pourcentage_presence = ((total_presences - total_absences) / total_presences) * 100

            # Organiser les présences par mois
            presences_par_mois = {}
            for presence in presences:
                mois_key = presence.session.date.strftime('%Y-%m')
                if mois_key not in presences_par_mois:
                    presences_par_mois[mois_key] = []
                presences_par_mois[mois_key].append(presence)

            return {
                'etudiant': etudiant,
                'presences': presences,
                'stats_par_cours': stats_par_cours,
                'total_presences': total_presences,
                'total_absences': total_absences,
                'total_heures_absence': total_heures_absence,
                'pourcentage_presence': round(pourcentage_presence, 2),
                'presences_par_mois': presences_par_mois,
                'date_debut': date_debut,
                'date_fin': date_fin
            }

        except Exception as e:
            print(f"[ERROR] Erreur calcul bilan détaillé: {str(e)}")
            return None

    @staticmethod
    def get_filieres_disponibles():
        """Récupère toutes les filières disponibles"""
        try:
            filieres = db.session.query(EtudiantModel.filiere) \
                .distinct() \
                .order_by(EtudiantModel.filiere) \
                .all()
            return [f[0] for f in filieres if f[0]]
        except:
            return []

    @staticmethod
    def get_statistiques_globales():
        """Récupère les statistiques globales"""
        try:
            # Nombre total d'étudiants
            total_etudiants = EtudiantModel.query.count()

            # Nombre total de présences enregistrées
            total_presences = PresenceModel.query.count()

            # Nombre total d'absences
            total_absences = PresenceModel.query.filter_by(statut='A').count()

            # Heures d'absence totales
            total_heures_absence = total_absences * 2

            # Pourcentage de présence global
            pourcentage_presence = 0
            if total_presences > 0:
                pourcentage_presence = ((total_presences - total_absences) / total_presences) * 100

            # Distribution par filière
            filieres = AttendanceService.get_filieres_disponibles()
            stats_filieres = []

            for filiere in filieres:
                etudiants_filiere = EtudiantModel.query.filter_by(filiere=filiere).count()
                presences_filiere = PresenceModel.query \
                    .join(EtudiantModel) \
                    .filter(EtudiantModel.filiere == filiere) \
                    .count()
                absences_filiere = PresenceModel.query \
                    .join(EtudiantModel) \
                    .filter(EtudiantModel.filiere == filiere, PresenceModel.statut == 'A') \
                    .count()

                pourcentage_filiere = 0
                if presences_filiere > 0:
                    pourcentage_filiere = ((presences_filiere - absences_filiere) / presences_filiere) * 100

                stats_filieres.append({
                    'filiere': filiere,
                    'etudiants': etudiants_filiere,
                    'pourcentage_presence': round(pourcentage_filiere, 1)
                })

            return {
                'total_etudiants': total_etudiants,
                'total_presences': total_presences,
                'total_absences': total_absences,
                'total_heures_absence': total_heures_absence,
                'pourcentage_presence': round(pourcentage_presence, 2),
                'stats_filieres': stats_filieres,
                'date_mise_a_jour': datetime.now().strftime('%d/%m/%Y %H:%M')
            }

        except Exception as e:
            print(f"[ERROR] Erreur statistiques globales: {str(e)}")
            return {}

    @staticmethod
    def get_dernieres_presences(limit=10):
        """Récupère les dernières présences enregistrées"""
        try:
            return PresenceModel.query \
                .join(EtudiantModel) \
                .join(CoursSessionModel) \
                .join(CoursModel) \
                .order_by(PresenceModel.date_enregistrement.desc()) \
                .limit(limit) \
                .all()
        except:
            return []

    @staticmethod
    def get_etudiants_plus_absents(limit=5):
        """Récupère les étudiants avec le plus d'absences"""
        try:
            # Requête pour compter les absences par étudiant
            result = db.session.query(
                EtudiantModel,
                func.count(PresenceModel.id).label('nb_absences')
            ) \
                .join(PresenceModel, EtudiantModel.id == PresenceModel.etudiant_id) \
                .filter(PresenceModel.statut == 'A') \
                .group_by(EtudiantModel.id) \
                .order_by(func.count(PresenceModel.id).desc()) \
                .limit(limit) \
                .all()

            return [{
                'etudiant': r[0],
                'nb_absences': r[1],
                'heures_absence': r[1] * 2
            } for r in result]
        except Exception as e:
            print(f"[ERROR] Erreur étudiants plus absents: {str(e)}")
            return []