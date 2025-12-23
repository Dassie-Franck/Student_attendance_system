from app.models.enum import Presence

class Attendance:
    def __init__(self,id_presence,id_etud ,id_course_session , statut:Presence):
        self.id_presence = id_presence
        self.id_etud = id_etud
        self.id_course_session = id_course_session
        self.statut = statut