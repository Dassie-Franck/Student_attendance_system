
from enum import Enum

class UserRole(Enum):
    ENSEIGNANT="ensg"
    HEAD="respoFiliere"
    DELEGUE="délégué"

class CourSession(Enum):
    SEANCE1 = "1"
    SEANCE2 = "2"

    @property
    def label(self):
        return {
            "1": "08h00 - 09h50",
            "2": "10h10 - 12h00"
        }[self.value]

class Presence(Enum):
    PRESENT="present"
    ABSENT="absent"