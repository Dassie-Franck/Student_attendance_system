from app.models.user import Users
from app.models.department_head import DepartmentHead
from app.models.enum import UserRole
head=DepartmentHead("1","dassie","franck","dassie@gmail.com","qwerty","INFORMATIQUE")

print(head.afficher())