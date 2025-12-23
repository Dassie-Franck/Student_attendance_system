from .enum import UserRole
from .user import UserModel

class Teacher(UserModel):
    def __init__(self,id_user,nom,prenom ,email,password,filiere):
        super().__init__(id_user,nom,prenom,email,password,filiere,UserRole.ENSEIGNANT)

    def DemarrerAppel(self):
        print()

    def CreateCourSession(self):
        print()

    def modifierCourSession(self):
        print()

