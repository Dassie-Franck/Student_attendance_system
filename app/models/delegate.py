from .enum import UserRole
from .user import Users


class Delegate(Users):
    def __init__(self, id_user , nom ,prenom , email,password , filiere):
        super().__init__(id_user , nom , prenom , email, password,filiere,UserRole.DELEGUE)




