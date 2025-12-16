CREATE DATABASE IF NOT EXISTS SystemPresence
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE SystemPresence;

-- TABLE USER
CREATE TABLE `user` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL,
    role ENUM('ensg','délégué','respoFiliere') NOT NULL,
    filiere VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- TABLE ETUDIANT
CREATE TABLE etudiant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    matricule VARCHAR(20) NOT NULL UNIQUE,
    filiere VARCHAR(100) NOT NULL,
    annee VARCHAR(20) NOT NULL
) ENGINE=InnoDB;

-- TABLE COURS
CREATE TABLE cours (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    filiere VARCHAR(100) NOT NULL,
    semestre VARCHAR(20) NOT NULL,
    CONSTRAINT fk_cours_user
        FOREIGN KEY (user_id) REFERENCES `user`(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- TABLE SUIVIE_COURS
CREATE TABLE suivie_cours (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    cours_id INT NOT NULL,
    CONSTRAINT fk_suivie_etudiant
        FOREIGN KEY (etudiant_id) REFERENCES etudiant(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_suivie_cours
        FOREIGN KEY (cours_id) REFERENCES cours(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- TABLE COURS_SESSION
CREATE TABLE cours_session (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cours_id INT NOT NULL,
    `date` DATE NOT NULL,
    seance ENUM('1','2') NOT NULL, -- 1 = 08h-09h50, 2 = 10h10-12h00
    CONSTRAINT fk_session_cours
        FOREIGN KEY (cours_id) REFERENCES cours(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- TABLE PRESENCE
CREATE TABLE presence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    cours_session_id INT NOT NULL,
    statut ENUM('P','A') NOT NULL, -- P = présent, A = absent
    CONSTRAINT fk_presence_etudiant
        FOREIGN KEY (etudiant_id) REFERENCES etudiant(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_presence_session
        FOREIGN KEY (cours_session_id) REFERENCES cours_session(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- TABLE PROFIL
CREATE TABLE profil (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    photo_avant VARCHAR(255) NOT NULL,
    photo_gauche VARCHAR(255) NOT NULL,
    photo_droite VARCHAR(255) NOT NULL,
    CONSTRAINT fk_profil_etudiant
        FOREIGN KEY (etudiant_id) REFERENCES etudiant(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;


USE SystemPresence;

-- TABLE USER
INSERT INTO `user` (nom, prenom, email, mot_de_passe, role, filiere) VALUES
('Kouassi',   'Jean',    'jean.kouassi@example.com',   'hash_mdp_jean',   'ensg',        'Informatique'),
('Traore',    'Aminata', 'aminata.traore@example.com','hash_mdp_amina',  'ensg',        'Réseaux'),
('Nguyen',    'Paul',    'paul.nguyen@example.com',    'hash_mdp_paul',   'délégué',     'Informatique'),
('Diallo',    'Fatou',   'fatou.diallo@example.com',   'hash_mdp_fatou',  'respoFiliere','Informatique'),
('Mensah',    'Eric',    'eric.mensah@example.com',    'hash_mdp_eric',   'délégué',     'Réseaux');

-- TABLE ETUDIANT
INSERT INTO etudiant (nom, prenom, matricule, filiere, annee) VALUES
('Kouadio', 'Marie',   'ETU001', 'Informatique', 'L1'),
('Sow',     'Ibrahim', 'ETU002', 'Informatique', 'L2'),
('Tchamba', 'Linda',   'ETU003', 'Réseaux',      'L1'),
('Zongo',   'Arthur',  'ETU004', 'Réseaux',      'L2'),
('Smith',   'Julia',   'ETU005', 'Informatique', 'L3');

-- TABLE COURS
-- On suppose: user_id 1 = enseignant Info, user_id 2 = enseignant Réseaux, user_id 3 = délégué Info
INSERT INTO cours (nom, user_id, filiere, semestre) VALUES
('Programmation Python',      1, 'Informatique', 'S1'),
('Bases de données',          1, 'Informatique', 'S1'),
('Réseaux informatiques',     2, 'Réseaux',      'S1'),
('Systèmes exploitation',  1, 'Informatique', 'S2'),
('Administration réseaux',    2, 'Réseaux',      'S2');

-- TABLE SUIVIE_COURS
-- On suppose que les étudiants ont les IDs 1..5 dans l’ordre d’insertion
-- et les cours ont les IDs 1..5 dans l’ordre d’insertion
INSERT INTO suivie_cours (etudiant_id, cours_id) VALUES
(1, 1),  -- Marie suit Programmation Python
(1, 2),  -- Marie suit Bases de données
(2, 1),  -- Ibrahim suit Programmation Python
(3, 3),  -- Linda suit Réseaux informatiques
(4, 3);  -- Arthur suit Réseaux informatiques

-- TABLE COURS_SESSION
-- On suppose que les cours ont IDs 1..5
INSERT INTO cours_session (cours_id, `date`, seance) VALUES
(1, '2025-12-16', '1'),  -- Prog Python, séance 1
(1, '2025-12-16', '2'),  -- Prog Python, séance 2
(2, '2025-12-17', '1'),  -- Bases de données, séance 1
(3, '2025-12-18', '1'),  -- Réseaux info, séance 1
(3, '2025-12-18', '2');  -- Réseaux info, séance 2

-- TABLE PRESENCE
-- On suppose que cours_session a les IDs 1..5 dans l’ordre d’insertion
INSERT INTO presence (etudiant_id, cours_session_id, statut) VALUES
(1, 1, 'P'),  -- Marie présente à Prog Python séance 1
(1, 2, 'A'),  -- Marie absente à Prog Python séance 2
(2, 1, 'P'),  -- Ibrahim présent à Prog Python séance 1
(3, 4, 'P'),  -- Linda présente à Réseaux info séance 1
(4, 4, 'A');  -- Arthur absent à Réseaux info séance 1

-- TABLE PROFIL
INSERT INTO profil (etudiant_id, photo_avant, photo_gauche, photo_droite) VALUES
(1, 'photos/ETU001_face.jpg', 'photos/ETU001_gauche.jpg', 'photos/ETU001_droite.jpg'),
(2, 'photos/ETU002_face.jpg', 'photos/ETU002_gauche.jpg', 'photos/ETU002_droite.jpg'),
(3, 'photos/ETU003_face.jpg', 'photos/ETU003_gauche.jpg', 'photos/ETU003_droite.jpg'),
(4, 'photos/ETU004_face.jpg', 'photos/ETU004_gauche.jpg', 'photos/ETU004_droite.jpg'),
(5, 'photos/ETU005_face.jpg', 'photos/ETU005_gauche.jpg', 'photos/ETU005_droite.jpg');


