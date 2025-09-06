/* =========================================================
   PM Internship Allocation – Full MySQL Schema + Seed Data
   (rank -> ranked, no IF NOT EXISTS)
   ========================================================= */

-- 0) DATABASE
DROP DATABASE IF EXISTS pm_intern_alloc;
CREATE DATABASE pm_intern_alloc
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE pm_intern_alloc;

-- 1) REFERENCE TABLES
CREATE TABLE category (
  category_code VARCHAR(16) PRIMARY KEY,
  name          VARCHAR(64) NOT NULL
) ENGINE=InnoDB;

INSERT INTO category (category_code, name) VALUES
('GEN','General'),('SC','Scheduled Caste'),('ST','Scheduled Tribe'),
('OBC','Other Backward Class'),('EWS','Economically Weaker Section');

CREATE TABLE disability_type (
  code VARCHAR(16) PRIMARY KEY,
  name VARCHAR(64) NOT NULL
) ENGINE=InnoDB;

INSERT INTO disability_type (code, name) VALUES
('NONE','None'),('PWD','Persons with Disability');

CREATE TABLE organization (
  org_id       BIGINT PRIMARY KEY AUTO_INCREMENT,
  org_name     VARCHAR(200) NOT NULL,
  org_email    VARCHAR(200) NULL,
  org_website  VARCHAR(300) NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE UNIQUE INDEX ux_org_name ON organization(org_name);

-- 2) SKILL REFS
CREATE TABLE skill_ref (
  skill_code  VARCHAR(32) PRIMARY KEY,
  name        VARCHAR(200) NOT NULL,
  nsqf_level  TINYINT NULL
) ENGINE=InnoDB;

-- 3) STUDENTS
CREATE TABLE student (
  student_id       BIGINT PRIMARY KEY AUTO_INCREMENT,
  ext_id           VARCHAR(64) NULL,
  name             VARCHAR(150) NOT NULL,
  email            VARCHAR(200) NOT NULL,
  phone            VARCHAR(32)  NULL,

  degree           VARCHAR(80)  NULL,
  cgpa             DECIMAL(4,2) NULL,
  grad_year        YEAR NULL,

  highest_qualification ENUM('10','12','ITI','Diploma','UG','PG') NULL,
  tenth_percent    DECIMAL(5,2) NULL,
  twelfth_percent  DECIMAL(5,2) NULL,

  location_pref    VARCHAR(120) NULL,
  pincode          VARCHAR(6)   NULL,
  willing_radius_km INT NULL DEFAULT 20,
  category_code    VARCHAR(16) NOT NULL,
  disability_code  VARCHAR(16) NOT NULL DEFAULT 'NONE',

  languages_json   JSON NULL,
  skills_text      TEXT NULL,
  resume_url       VARCHAR(500) NULL,
  resume_summary   TEXT NULL,

  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_student_category    FOREIGN KEY (category_code)  REFERENCES category(category_code),
  CONSTRAINT fk_student_disability  FOREIGN KEY (disability_code) REFERENCES disability_type(code)
) ENGINE=InnoDB;

CREATE UNIQUE INDEX ux_student_email ON student(email);
CREATE INDEX ix_student_category   ON student(category_code);
CREATE INDEX ix_student_cgpa       ON student(cgpa);
CREATE INDEX ix_student_grad_year  ON student(grad_year);
CREATE INDEX ix_student_pincode    ON student(pincode);

-- 3a) Student skills
CREATE TABLE student_skill (
  student_id     BIGINT NOT NULL,
  skill_code     VARCHAR(32) NOT NULL,
  proficiency    TINYINT NULL,
  evidence       ENUM('RPL','ITI','CERT','EXP','NONE') DEFAULT 'NONE',
  evidence_score TINYINT NULL,
  PRIMARY KEY (student_id, skill_code),
  CONSTRAINT fk_ss_student   FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
  CONSTRAINT fk_ss_skill_ref FOREIGN KEY (skill_code) REFERENCES skill_ref(skill_code) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 3b) Availability
CREATE TABLE student_availability (
  student_id   BIGINT PRIMARY KEY,
  can_shift    ENUM('DAY','NIGHT','BOTH') DEFAULT 'DAY',
  days_json    JSON NULL,
  phone_access ENUM('SMARTPHONE','FEATURE','NONE') DEFAULT 'FEATURE',
  CONSTRAINT fk_savail_student FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4) INTERNSHIPS
CREATE TABLE internship (
  internship_id      BIGINT PRIMARY KEY AUTO_INCREMENT,
  org_id             BIGINT NULL,
  org_name           VARCHAR(200) NULL,
  title              VARCHAR(200) NOT NULL,
  description        TEXT NULL,
  req_skills_text    TEXT NULL,
  min_cgpa           DECIMAL(4,2) NOT NULL DEFAULT 0.00,
  location           VARCHAR(120) NULL,
  pincode            VARCHAR(6)   NULL,
  capacity           INT NOT NULL DEFAULT 1,

  job_role_code      VARCHAR(32) NULL,
  nsqf_required_level TINYINT NULL,

  min_age            TINYINT NULL,
  genders_allowed    JSON NULL,
  languages_required_json JSON NULL,
  is_shift_night     TINYINT(1) NOT NULL DEFAULT 0,
  wage_min           INT NULL,
  wage_max           INT NULL,

  category_quota_json JSON NULL,

  is_active          TINYINT(1) NOT NULL DEFAULT 1,
  created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_internship_org FOREIGN KEY (org_id) REFERENCES organization(org_id)
) ENGINE=InnoDB;

CREATE INDEX ix_internship_org       ON internship(org_id);
CREATE INDEX ix_internship_location  ON internship(location);
CREATE INDEX ix_internship_pincode   ON internship(pincode);
CREATE INDEX ix_internship_active    ON internship(is_active);

-- 4a) Internship skills
CREATE TABLE job_skill_required (
  internship_id BIGINT NOT NULL,
  skill_code    VARCHAR(32) NOT NULL,
  weight        DECIMAL(4,2) NOT NULL DEFAULT 1.00,
  PRIMARY KEY (internship_id, skill_code),
  CONSTRAINT fk_jsr_internship FOREIGN KEY (internship_id) REFERENCES internship(internship_id) ON DELETE CASCADE,
  CONSTRAINT fk_jsr_skill_ref  FOREIGN KEY (skill_code)    REFERENCES skill_ref(skill_code) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5) PREFERENCES (rank -> ranked)
CREATE TABLE preference (
  preference_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  student_id    BIGINT NOT NULL,
  internship_id BIGINT NOT NULL,
  ranked        INT NOT NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pref_student    FOREIGN KEY (student_id)    REFERENCES student(student_id)    ON DELETE CASCADE,
  CONSTRAINT fk_pref_internship FOREIGN KEY (internship_id) REFERENCES internship(internship_id) ON DELETE CASCADE,
  CONSTRAINT ux_pref_unique UNIQUE (student_id, internship_id)
) ENGINE=InnoDB;

CREATE INDEX ix_pref_student    ON preference(student_id);
CREATE INDEX ix_pref_internship ON preference(internship_id);
CREATE INDEX ix_pref_ranked     ON preference(ranked);

-- 6) RUNS
CREATE TABLE alloc_run (
  run_id        BIGINT PRIMARY KEY AUTO_INCREMENT,
  status        ENUM('QUEUED','RUNNING','SUCCESS','FAILED') NOT NULL DEFAULT 'SUCCESS',
  params_json   JSON NULL,
  metrics_json  JSON NULL,
  error_message TEXT NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE INDEX ix_run_status  ON alloc_run(status);
CREATE INDEX ix_run_created ON alloc_run(created_at);

-- 7) MATCH RESULTS
CREATE TABLE match_result (
  match_id        BIGINT PRIMARY KEY AUTO_INCREMENT,
  run_id          BIGINT NOT NULL,
  student_id      BIGINT NOT NULL,
  internship_id   BIGINT NOT NULL,
  allocated_slot  INT NOT NULL DEFAULT 1,
  final_score     DECIMAL(6,4) NOT NULL,
  component_json  JSON NULL,
  explanation     TEXT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_match_run        FOREIGN KEY (run_id)        REFERENCES alloc_run(run_id)        ON DELETE CASCADE,
  CONSTRAINT fk_match_student    FOREIGN KEY (student_id)    REFERENCES student(student_id),
  CONSTRAINT fk_match_internship FOREIGN KEY (internship_id) REFERENCES internship(internship_id),

  CONSTRAINT ux_run_student UNIQUE (run_id, student_id)
) ENGINE=InnoDB;

CREATE INDEX ix_match_run         ON match_result(run_id);
CREATE INDEX ix_match_internship  ON match_result(internship_id);
CREATE INDEX ix_match_student     ON match_result(student_id);

-- 8) AUDIT LOGS
CREATE TABLE audit_log (
  audit_id     BIGINT PRIMARY KEY AUTO_INCREMENT,
  run_id       BIGINT NULL,
  level        ENUM('INFO','WARN','ERROR') NOT NULL DEFAULT 'INFO',
  message      VARCHAR(500) NOT NULL,
  payload_json JSON NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_run FOREIGN KEY (run_id) REFERENCES alloc_run(run_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX ix_audit_run   ON audit_log(run_id);
CREATE INDEX ix_audit_level ON audit_log(level);

-- 9) VIEWS
CREATE OR REPLACE VIEW v_latest_run AS
SELECT run_id
FROM alloc_run
WHERE status = 'SUCCESS'
ORDER BY created_at DESC
LIMIT 1;

CREATE OR REPLACE VIEW v_latest_matches AS
SELECT
  mr.run_id, mr.student_id, s.name AS student_name, s.email,
  mr.internship_id, i.title AS internship_title, COALESCE(i.org_name, o.org_name) AS org_name,
  i.location, i.pincode, mr.final_score, mr.component_json, mr.created_at
FROM match_result mr
JOIN student s       ON s.student_id = mr.student_id
JOIN internship i    ON i.internship_id = mr.internship_id
LEFT JOIN organization o ON o.org_id = i.org_id
WHERE mr.run_id = (SELECT run_id FROM v_latest_run);

-- =========================================================
-- SEED DATA
-- =========================================================

-- Organizations
INSERT INTO organization (org_name, org_email) VALUES
('Shakti Utilities','hr@shaktiutils.example'),
('JalSewa Services','talent@jalsewa.example'),
('Rashtra Records','ops@rrecords.example'),
('TechNirmaan Pvt Ltd','careers@technirmaan.example'),
('DataVista Analytics','hr@datavista.example');

-- Skills
INSERT INTO skill_ref (skill_code, name, nsqf_level) VALUES
('ELE-BASE','Basic Electrical Safety',3),
('ELE-WIRE','Wire Harnessing',3),
('PLUMB-BASIC','Basic Plumbing',3),
('PLUMB-PIPE','Pipe Fitting',3),
('DEO-TYPING','Data Entry Typing (30+ wpm)',3),
('DEO-COMPUTER','Basic Computer Operations',3),
('IT-DEV-PY','Python Programming',5),
('DA-NOS-SQL','SQL Basics',4),
('DS-ML','Machine Learning Foundations',6),
('IT-DEV-REACT','React Development',5),
('IT-DEV-JS','JavaScript Programming',5);

-- Non-degree jobs
INSERT INTO internship (org_id, org_name, title, description, req_skills_text, min_cgpa, location, pincode, capacity,
 job_role_code, nsqf_required_level, min_age, genders_allowed, languages_required_json, is_shift_night,
 wage_min, wage_max, category_quota_json, is_active) VALUES
((SELECT org_id FROM organization WHERE org_name='Shakti Utilities'),
 'Shakti Utilities','Electrician Helper',
 'Assist senior electrician with wiring, maintenance, and safety checks.',
 'Electrical basics, wiring, safety',0.0,'Ahmedabad','380001',2,
 'ELE-ROLE-HELP',3,18,JSON_ARRAY('ANY'),JSON_ARRAY('hi','gu','en'),0,14000,18000,NULL,1),
((SELECT org_id FROM organization WHERE org_name='JalSewa Services'),
 'JalSewa Services','Plumbing Assistant',
 'Support installation/repair of pipelines, fittings, and fixtures.',
 'Basic plumbing, pipe fitting',0.0,'Surat','395003',5,
 'PLUMB-ROLE-ASSIST',3,18,JSON_ARRAY('ANY'),JSON_ARRAY('hi','gu'),0,13000,17000,NULL,1),
((SELECT org_id FROM organization WHERE org_name='Rashtra Records'),
 'Rashtra Records','Data Entry Operator',
 'Digitize forms; maintain simple spreadsheets and records.',
 'Typing and basic computer',0.0,'Jaipur','302001',1,
 'DEO-ROLE',3,18,JSON_ARRAY('ANY'),JSON_ARRAY('hi','en'),0,12000,16000,NULL,1);

-- Graduate jobs
INSERT INTO internship (org_id, org_name, title, description, req_skills_text, min_cgpa, location, pincode, capacity,
 job_role_code, nsqf_required_level, min_age, genders_allowed, languages_required_json, is_shift_night,
 wage_min, wage_max, category_quota_json, is_active) VALUES
((SELECT org_id FROM organization WHERE org_name='TechNirmaan Pvt Ltd'),
 'TechNirmaan Pvt Ltd','Software Engineer Trainee',
 'Work on Python-based services and basic web APIs.',
 'Python, SQL, basics of JS',7.0,'Bengaluru','560001',2,
 'SWE-TRAINEE',5,18,JSON_ARRAY('ANY'),JSON_ARRAY('en'),0,25000,35000,NULL,1),
((SELECT org_id FROM organization WHERE org_name='DataVista Analytics'),
 'DataVista Analytics','Data Analyst Trainee',
 'Build dashboards; analyze datasets; SQL, Python, basic ML.',
 'SQL, Python, ML',7.5,'Delhi','110001',2,
 'DA-TRAINEE',5,18,JSON_ARRAY('ANY'),JSON_ARRAY('en','hi'),0,28000,38000,NULL,1),
((SELECT org_id FROM organization WHERE org_name='TechNirmaan Pvt Ltd'),
 'TechNirmaan Pvt Ltd','Backend Developer Intern',
 'Assist in building backend services; Python and SQL preferred.',
 'Python, SQL',7.0,'Pune','411001',1,
 'BACKEND-INT',5,18,JSON_ARRAY('ANY'),JSON_ARRAY('en'),0,26000,36000,NULL,1);

-- Job skills
INSERT INTO job_skill_required (internship_id, skill_code, weight) VALUES
((SELECT internship_id FROM internship WHERE title='Electrician Helper'),'ELE-BASE',1.0),
((SELECT internship_id FROM internship WHERE title='Electrician Helper'),'ELE-WIRE',1.0),
((SELECT internship_id FROM internship WHERE title='Plumbing Assistant'),'PLUMB-BASIC',1.0),
((SELECT internship_id FROM internship WHERE title='Plumbing Assistant'),'PLUMB-PIPE',1.0),
((SELECT internship_id FROM internship WHERE title='Data Entry Operator'),'DEO-TYPING',1.0),
((SELECT internship_id FROM internship WHERE title='Data Entry Operator'),'DEO-COMPUTER',1.0),
((SELECT internship_id FROM internship WHERE title='Software Engineer Trainee'),'IT-DEV-PY',1.0),
((SELECT internship_id FROM internship WHERE title='Software Engineer Trainee'),'DA-NOS-SQL',0.8),
((SELECT internship_id FROM internship WHERE title='Data Analyst Trainee'),'DA-NOS-SQL',1.0),
((SELECT internship_id FROM internship WHERE title='Data Analyst Trainee'),'IT-DEV-PY',0.8),
((SELECT internship_id FROM internship WHERE title='Data Analyst Trainee'),'DS-ML',0.6),
((SELECT internship_id FROM internship WHERE title='Backend Developer Intern'),'IT-DEV-PY',1.0),
((SELECT internship_id FROM internship WHERE title='Backend Developer Intern'),'DA-NOS-SQL',1.0);

-- Students (10th/12th/ITI)
INSERT INTO student (ext_id,name,email,phone,degree,cgpa,grad_year,highest_qualification,tenth_percent,twelfth_percent,
 location_pref,pincode,willing_radius_km,category_code,disability_code,languages_json,skills_text) VALUES
('R001','Sunil Patel','sunil.patel@example.com','9000000001',NULL,NULL,NULL,'10',68.0,NULL,'Ahmedabad','380002',15,'OBC','NONE',JSON_ARRAY('hi','gu'),'Electrical basics, wiring'),
('R002','Rupa Shah','rupa.shah@example.com','9000000002',NULL,NULL,NULL,'12',74.5,70.0,'Ahmedabad','380003',20,'GEN','NONE',JSON_ARRAY('hi','gu','en'),'Wiring, safety, basic electrical tools'),
('R003','Arjun Solanki','arjun.solanki@example.com','9000000003','ITI - Electrician',NULL,NULL,'ITI',NULL,NULL,'Ahmedabad','380004',25,'SC','NONE',JSON_ARRAY('hi','gu'),'Electrician trade, wire harnessing'),
('R004','Meera Yadav','meera.yadav@example.com','9000000004',NULL,NULL,NULL,'10',66.0,NULL,'Surat','395002',10,'GEN','NONE',JSON_ARRAY('hi','gu'),'Basic plumbing'),
('R005','Shyam Desai','shyam.desai@example.com','9000000005','ITI - Plumber',NULL,NULL,'ITI',NULL,NULL,'Surat','395004',15,'OBC','NONE',JSON_ARRAY('hi','gu'),'Pipe fitting, basic plumbing'),
('R006','Farhan Shaikh','farhan.shaikh@example.com','9000000006',NULL,NULL,NULL,'12',72.0,68.0,'Surat','395005',15,'EWS','NONE',JSON_ARRAY('hi'),'Plumbing helper, pipe cutting'),
('R007','Kavita Singh','kavita.singh@example.com','9000000007',NULL,NULL,NULL,'12',78.0,75.0,'Jaipur','302002',12,'GEN','NONE',JSON_ARRAY('hi','en'),'Typing 35 wpm, basic computer'),
('R008','Nilesh Kumar','nilesh.kumar@example.com','9000000008',NULL,NULL,NULL,'10',64.0,NULL,'Jaipur','302003',10,'OBC','NONE',JSON_ARRAY('hi'),'Typing 25 wpm'),
('R009','Priya Chauhan','priya.chauhan@example.com','9000000009',NULL,NULL,NULL,'12',70.0,69.0,'Ahmedabad','380005',12,'GEN','NONE',JSON_ARRAY('hi','gu'),'Basic hand tools'),
('R010','Manoj Parmar','manoj.parmar@example.com','9000000010','ITI - Electrician',NULL,NULL,'ITI',NULL,NULL,'Ahmedabad','380006',20,'ST','NONE',JSON_ARRAY('hi','gu'),'Electrical safety, basic wiring');

-- Graduate students (CGPA + IT skills)
INSERT INTO student (ext_id,name,email,phone,degree,cgpa,grad_year,highest_qualification,tenth_percent,twelfth_percent,
 location_pref,pincode,willing_radius_km,category_code,disability_code,languages_json,skills_text) VALUES
('G001','Ankit Verma','ankit.verma@example.com','9111111111','BTech CSE',8.20,2025,'UG',88.0,90.0,'Bengaluru','560002',20,'GEN','NONE',JSON_ARRAY('en','hi'),'Python, SQL, Pandas, APIs'),
('G002','Sneha Iyer','sneha.iyer@example.com','9222222222','BSc Data Science',8.90,2024,'UG',92.0,91.0,'Delhi','110003',15,'GEN','NONE',JSON_ARRAY('en','hi'),'SQL, Python, ML, Excel'),
('G003','Rohit Nair','rohit.nair@example.com','9333333333','MSc Statistics',9.10,2024,'PG',90.0,93.0,'Delhi','110004',15,'OBC','NONE',JSON_ARRAY('en'),'Python, SQL, Statistics, ML'),
('G004','Ayesha Khan','ayesha.khan@example.com','9444444444','BTech IT',7.40,2025,'UG',86.0,87.0,'Pune','411002',15,'EWS','NONE',JSON_ARRAY('en','hi'),'Python, SQL, basic JS'),
('G005','Varun Gupta','varun.gupta@example.com','9555555555','BTech CSE',7.10,2025,'UG',85.0,86.0,'Bengaluru','560003',15,'GEN','NONE',JSON_ARRAY('en'),'Python, SQL, Git');

-- Student structured skills (non-degree)
INSERT INTO student_skill (student_id, skill_code, proficiency, evidence, evidence_score) VALUES
((SELECT student_id FROM student WHERE email='sunil.patel@example.com'),'ELE-BASE',3,'RPL',60),
((SELECT student_id FROM student WHERE email='sunil.patel@example.com'),'ELE-WIRE',2,'RPL',50),
((SELECT student_id FROM student WHERE email='rupa.shah@example.com'),'ELE-BASE',4,'CERT',75),
((SELECT student_id FROM student WHERE email='rupa.shah@example.com'),'ELE-WIRE',3,'CERT',70),
((SELECT student_id FROM student WHERE email='arjun.solanki@example.com'),'ELE-BASE',5,'ITI',85),
((SELECT student_id FROM student WHERE email='arjun.solanki@example.com'),'ELE-WIRE',5,'ITI',85),
((SELECT student_id FROM student WHERE email='manoj.parmar@example.com'),'ELE-BASE',4,'ITI',80),
((SELECT student_id FROM student WHERE email='manoj.parmar@example.com'),'ELE-WIRE',3,'RPL',65),
((SELECT student_id FROM student WHERE email='meera.yadav@example.com'),'PLUMB-BASIC',3,'RPL',55),
((SELECT student_id FROM student WHERE email='shyam.desai@example.com'),'PLUMB-BASIC',5,'ITI',90),
((SELECT student_id FROM student WHERE email='shyam.desai@example.com'),'PLUMB-PIPE',5,'ITI',90),
((SELECT student_id FROM student WHERE email='farhan.shaikh@example.com'),'PLUMB-BASIC',4,'CERT',70),
((SELECT student_id FROM student WHERE email='farhan.shaikh@example.com'),'PLUMB-PIPE',3,'RPL',60),
((SELECT student_id FROM student WHERE email='kavita.singh@example.com'),'DEO-TYPING',4,'CERT',80),
((SELECT student_id FROM student WHERE email='kavita.singh@example.com'),'DEO-COMPUTER',4,'CERT',78),
((SELECT student_id FROM student WHERE email='nilesh.kumar@example.com'),'DEO-TYPING',3,'NONE',0),
((SELECT student_id FROM student WHERE email='nilesh.kumar@example.com'),'DEO-COMPUTER',2,'NONE',0),
((SELECT student_id FROM student WHERE email='priya.chauhan@example.com'),'ELE-BASE',2,'NONE',0);

-- Student structured skills (graduates)
INSERT INTO student_skill (student_id, skill_code, proficiency, evidence, evidence_score) VALUES
((SELECT student_id FROM student WHERE email='ankit.verma@example.com'),'IT-DEV-PY',5,'CERT',85),
((SELECT student_id FROM student WHERE email='ankit.verma@example.com'),'DA-NOS-SQL',4,'CERT',80),
((SELECT student_id FROM student WHERE email='sneha.iyer@example.com'),'DA-NOS-SQL',5,'CERT',90),
((SELECT student_id FROM student WHERE email='sneha.iyer@example.com'),'IT-DEV-PY',4,'CERT',82),
((SELECT student_id FROM student WHERE email='sneha.iyer@example.com'),'DS-ML',3,'CERT',75),
((SELECT student_id FROM student WHERE email='rohit.nair@example.com'),'DA-NOS-SQL',5,'CERT',92),
((SELECT student_id FROM student WHERE email='rohit.nair@example.com'),'IT-DEV-PY',5,'CERT',90),
((SELECT student_id FROM student WHERE email='rohit.nair@example.com'),'DS-ML',4,'CERT',88),
((SELECT student_id FROM student WHERE email='ayesha.khan@example.com'),'IT-DEV-PY',4,'CERT',78),
((SELECT student_id FROM student WHERE email='ayesha.khan@example.com'),'DA-NOS-SQL',4,'CERT',76),
((SELECT student_id FROM student WHERE email='varun.gupta@example.com'),'IT-DEV-PY',4,'CERT',76),
((SELECT student_id FROM student WHERE email='varun.gupta@example.com'),'DA-NOS-SQL',4,'CERT',74);

-- Availability
INSERT INTO student_availability (student_id, can_shift, days_json, phone_access) VALUES
((SELECT student_id FROM student WHERE email='sunil.patel@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'FEATURE'),
((SELECT student_id FROM student WHERE email='rupa.shah@example.com'),'BOTH',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri','Sat'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='arjun.solanki@example.com'),'BOTH',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='meera.yadav@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'FEATURE'),
((SELECT student_id FROM student WHERE email='shyam.desai@example.com'),'BOTH',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='farhan.shaikh@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'FEATURE'),
((SELECT student_id FROM student WHERE email='kavita.singh@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='nilesh.kumar@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'FEATURE'),
((SELECT student_id FROM student WHERE email='priya.chauhan@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'FEATURE'),
((SELECT student_id FROM student WHERE email='manoj.parmar@example.com'),'BOTH',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='ankit.verma@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='sneha.iyer@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='rohit.nair@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='ayesha.khan@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE'),
((SELECT student_id FROM student WHERE email='varun.gupta@example.com'),'DAY',JSON_ARRAY('Mon','Tue','Wed','Thu','Fri'),'SMARTPHONE');

-- Preferences (uses ranked)
INSERT INTO preference (student_id, internship_id, ranked) VALUES
-- non-degree
((SELECT student_id FROM student WHERE email='sunil.patel@example.com'),
 (SELECT internship_id FROM internship WHERE title='Electrician Helper' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='rupa.shah@example.com'),
 (SELECT internship_id FROM internship WHERE title='Electrician Helper' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='arjun.solanki@example.com'),
 (SELECT internship_id FROM internship WHERE title='Electrician Helper' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='meera.yadav@example.com'),
 (SELECT internship_id FROM internship WHERE title='Plumbing Assistant' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='shyam.desai@example.com'),
 (SELECT internship_id FROM internship WHERE title='Plumbing Assistant' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='farhan.shaikh@example.com'),
 (SELECT internship_id FROM internship WHERE title='Plumbing Assistant' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='kavita.singh@example.com'),
 (SELECT internship_id FROM internship WHERE title='Data Entry Operator' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='nilesh.kumar@example.com'),
 (SELECT internship_id FROM internship WHERE title='Data Entry Operator' LIMIT 1), 2),
-- graduates
((SELECT student_id FROM student WHERE email='ankit.verma@example.com'),
 (SELECT internship_id FROM internship WHERE title='Software Engineer Trainee' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='sneha.iyer@example.com'),
 (SELECT internship_id FROM internship WHERE title='Data Analyst Trainee' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='rohit.nair@example.com'),
 (SELECT internship_id FROM internship WHERE title='Data Analyst Trainee' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='ayesha.khan@example.com'),
 (SELECT internship_id FROM internship WHERE title='Backend Developer Intern' LIMIT 1), 1),
((SELECT student_id FROM student WHERE email='varun.gupta@example.com'),
 (SELECT internship_id FROM internship WHERE title='Software Engineer Trainee' LIMIT 1), 1);

-- Seed a dummy successful run (UI can render before engine integration)
INSERT INTO alloc_run (status, params_json, metrics_json)
VALUES ('SUCCESS',
        JSON_OBJECT('weights', JSON_OBJECT('exact',0.45,'rpl',0.20,'sem',0.15,'dist',0.10,'lang',0.05,'avail',0.05,'cgpa',0.10)),
        NULL);

-- Done.