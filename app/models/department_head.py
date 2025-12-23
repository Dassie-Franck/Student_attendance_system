
from .enum import UserRole
from .user import Users

class DepartmentHead(Users):
    def __init__(self, id_user , nom ,prenom , email,password , filiere):
        super().__init__(id_user,nom,prenom,email,password,filiere,UserRole.HEAD)

    def afficher(self):
        print("affichage department head\n ",self.id_user,self.nom,self.prenom,self.email,self.password,self.filiere,UserRole.HEAD.value)

    def ConsulterListe(self):
        print()

    def ConsulterAbsenceMensuelles(self):
        print()

    def ExporRapport(self):
        print()

    def AjouterUser(self):
        print()

    def SuppressionUser(self):
        print()

    def ModifierUser(self):
        print()

