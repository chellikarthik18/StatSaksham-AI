"""
Seed script for StatSaksham AI.

Creates all tables (if not present) and populates:
  - Roles (3)
  - Skills (22, across 4 categories)
  - Role -> competency requirements
  - iGOT Karmayogi + NSSTA/TPAC course catalogue (via karmayogi_service)
  - Diagnostic quizzes (one per skill) with auto-generated MCQs
  - Final assessment quizzes (one per course) with auto-generated MCQs
  - Demo users: employee, trainer, admin
  - A fully filled-in demo employee profile with a few skills pre-rated

Run with:
    python seed.py
"""
from database import SessionLocal, engine, Base
import models
from auth_utils import hash_password
from services.karmayogi_service import sync_igot_catalogue
from services.quiz_generator_service import generate_mcqs

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ---------------------------------------------------------------------------
# 1. Roles
# ---------------------------------------------------------------------------
ROLES = [
    {"name": "Statistical Investigator", "level_order": 1,
     "description": "Entry-level field officer responsible for data collection and basic survey operations."},
    {"name": "Statistical Officer", "level_order": 2,
     "description": "Mid-level officer responsible for data processing, supervision, and report preparation."},
    {"name": "Senior Statistical Officer", "level_order": 3,
     "description": "Senior officer responsible for survey design, team leadership, and policy analysis inputs."},
]

role_map = {}
for r in ROLES:
    role = db.query(models.Role).filter(models.Role.name == r["name"]).first()
    if not role:
        role = models.Role(name=r["name"], description=r["description"], level_order=r["level_order"])
        db.add(role)
        db.flush()
    role_map[r["name"]] = role
db.commit()
print(f"Seeded {len(role_map)} roles.")

# ---------------------------------------------------------------------------
# 2. Skills (name -> (category, description))
# ---------------------------------------------------------------------------
SKILLS = {
    # ---- Statistical ----
    "Statistical Literacy": ("statistical",
        "Statistical literacy is the ability to read, interpret, and critically evaluate statistical "
        "information used in official reports. Officials with strong statistical literacy can understand "
        "measures of central tendency, variability, and basic probability concepts. This skill underpins "
        "all data collection and reporting activities in the statistical system. Weak statistical literacy "
        "often leads to misinterpretation of survey findings. The National Statistical System places high "
        "importance on statistical literacy training for all new recruits."),
    "Survey Methodology": ("statistical",
        "Survey methodology covers the design and execution of large-scale data collection exercises. "
        "It includes questionnaire design, field organisation, and respondent selection procedures. "
        "A well-designed survey methodology reduces non-sampling errors and improves data quality. "
        "Officials trained in survey methodology can plan pilot surveys before full-scale rollout. "
        "The National Sample Survey Office relies heavily on robust survey methodology for its rounds."),
    "Sampling Techniques": ("statistical",
        "Sampling techniques involve selecting a representative subset of a population for study. "
        "Common methods include simple random sampling, stratified sampling, and cluster sampling. "
        "Choosing the right sampling technique affects the accuracy and cost of a statistical survey. "
        "Officials must understand sampling frames and sampling error to apply these techniques correctly. "
        "Advanced sampling techniques are used in complex multi-stage national surveys."),
    "Statistical Analysis": ("statistical",
        "Statistical analysis is the process of collecting and interpreting data to uncover patterns and trends. "
        "It includes hypothesis testing, regression analysis, and time-series modelling. "
        "Officials use statistical analysis to validate survey results before publication. "
        "Strong statistical analysis skills allow officers to detect anomalies in large datasets. "
        "Modern statistical analysis increasingly relies on software tools such as R and Python."),
    "National Accounts": ("statistical",
        "National accounts statistics measure the overall economic activity of a country through GDP and related aggregates. "
        "Compiling national accounts requires combining data from multiple sectors including agriculture, industry, and services. "
        "Officials working on national accounts must understand value addition and double counting issues. "
        "Accurate national accounts are essential for economic policy formulation and international comparison. "
        "The Central Statistics Office periodically revises the base year for national accounts."),
    "Economic Indicators": ("statistical",
        "Economic indicators are statistics that provide a snapshot of a country's economic performance. "
        "Common economic indicators include inflation rate, unemployment rate, and industrial production index. "
        "Officials monitor economic indicators to advise policymakers on emerging trends. "
        "Timely release of economic indicators builds public trust in the statistical system. "
        "Understanding economic indicators requires knowledge of both statistical methods and economic theory."),
    "Index Numbers": ("statistical",
        "Index numbers measure relative changes in a variable such as prices or production over time. "
        "The Consumer Price Index and Index of Industrial Production are widely used official index numbers. "
        "Constructing accurate index numbers requires careful selection of base year and weighting scheme. "
        "Officials must periodically revise index numbers to reflect changing consumption patterns. "
        "Index numbers are a key input for inflation targeting and monetary policy decisions."),
    "Data Collection": ("statistical",
        "Data collection is the systematic process of gathering information from respondents or administrative sources. "
        "Field officers use structured questionnaires and computer-assisted personal interviewing tools for data collection. "
        "Quality data collection requires proper training of enumerators and strong supervision in the field. "
        "Errors introduced during data collection are difficult to correct at later processing stages. "
        "Digital data collection tools have significantly improved the speed and accuracy of official surveys."),

    # ---- Technical ----
    "Data Analysis": ("technical",
        "Data analysis involves cleaning, transforming, and modelling data to extract useful insights. "
        "Officials use data analysis techniques to identify patterns and outliers in survey datasets. "
        "Proficiency in data analysis tools helps reduce manual processing time significantly. "
        "Good data analysis practices include documenting every transformation step for reproducibility. "
        "Government departments increasingly expect officers to be comfortable with basic data analysis."),
    "MS Excel Proficiency": ("technical",
        "MS Excel proficiency covers formulas, pivot tables, and basic charting used in day-to-day statistical work. "
        "Officials use spreadsheets to consolidate district-level data before submission to headquarters. "
        "Advanced Excel proficiency includes using lookup functions and conditional formatting for data validation. "
        "Excel proficiency remains one of the most requested digital skills across government offices. "
        "Training programmes on Excel proficiency help reduce errors in manual data compilation."),
    "Programming Fundamentals": ("technical",
        "Programming fundamentals include variables, loops, conditionals, and functions used to automate repetitive tasks. "
        "Officials with programming fundamentals can write simple scripts to clean and validate large datasets. "
        "Python and R are the most commonly taught languages for programming fundamentals in statistical training. "
        "Understanding programming fundamentals reduces dependency on manual, error-prone data processing. "
        "Programming fundamentals also form the basis for more advanced statistical computing courses."),
    "Data Visualization": ("technical",
        "Data visualization is the graphical representation of data to communicate findings clearly. "
        "Effective data visualization uses appropriate chart types such as bar charts, line charts, and maps. "
        "Officials use data visualization dashboards to present district-wise performance to senior management. "
        "Poor data visualization choices can mislead readers even when the underlying data is correct. "
        "Modern data visualization tools allow interactive exploration of large statistical datasets."),

    # ---- Digital Governance ----
    "Digital Governance": ("digital_governance",
        "Digital governance refers to the use of digital technologies to improve public service delivery. "
        "Officials must understand digital governance frameworks such as DigiLocker and UMANG. "
        "Digital governance training helps officers transition from paper-based to online workflows. "
        "Effective digital governance reduces delays and increases transparency in government processes. "
        "The National e-Governance Plan lays out the roadmap for digital governance across departments."),
    "e-Office Proficiency": ("digital_governance",
        "e-Office proficiency covers the use of digital file management systems for approvals and correspondence. "
        "Officials use e-Office to track file movement and reduce paper-based delays. "
        "Proficiency in e-Office includes drafting notes, attaching documents, and managing digital signatures. "
        "e-Office proficiency is now a mandatory requirement for most central government postings. "
        "Regular refresher training keeps officials updated on new e-Office features and modules."),
    "Cyber Security Awareness": ("digital_governance",
        "Cyber security awareness covers safe data handling, password hygiene, and phishing recognition. "
        "Officials handling sensitive statistical data must follow strict cyber security awareness protocols. "
        "A single cyber security lapse can compromise confidential respondent information collected during surveys. "
        "Cyber security awareness training is mandatory before officials are granted access to data systems. "
        "Government departments conduct periodic cyber security awareness drills to test employee readiness."),

    # ---- Behavioural / Managerial ----
    "Communication Skills": ("behavioural",
        "Communication skills enable officials to convey statistical findings clearly to both technical and non-technical audiences. "
        "Strong communication skills are essential when presenting survey results to senior officials or the public. "
        "Written communication skills are tested through official notes, reports, and press releases. "
        "Officials with good communication skills can simplify complex statistical concepts for policymakers. "
        "Communication skills training includes both verbal presentation and structured report writing."),
    "Report Writing": ("behavioural",
        "Report writing is the skill of structuring findings, methodology, and conclusions into a clear official document. "
        "A well-written report includes an executive summary, detailed analysis, and actionable recommendations. "
        "Officials must follow standard formatting guidelines when preparing statistical reports for publication. "
        "Poor report writing can obscure important findings even when the underlying analysis is sound. "
        "Report writing skills are evaluated during probation and promotion assessments."),
    "Leadership": ("behavioural",
        "Leadership involves guiding and motivating teams to achieve organisational goals effectively. "
        "Senior officials use leadership skills to manage field teams during large-scale survey operations. "
        "Good leadership includes delegating tasks appropriately and resolving conflicts within the team. "
        "Leadership training programmes prepare officers for supervisory roles as they move up the hierarchy. "
        "Strong leadership is critical during crisis situations such as natural disaster data collection."),
    "Team Management": ("behavioural",
        "Team management covers planning, coordinating, and monitoring the work of field and office staff. "
        "Officials with strong team management skills can allocate survey workload fairly across enumerators. "
        "Effective team management reduces delays caused by miscommunication or unclear responsibilities. "
        "Team management training includes conflict resolution and performance feedback techniques. "
        "Supervisory officers are expected to demonstrate team management skills before promotion."),
    "Project Management": ("behavioural",
        "Project management involves planning, budgeting, and monitoring statistical projects from start to finish. "
        "Officials use project management techniques to track survey timelines and resource allocation. "
        "Good project management ensures that large statistical exercises are completed within budget and schedule. "
        "Risk identification and mitigation are core components of effective project management. "
        "Project management skills become increasingly important as officers take on larger survey responsibilities."),
    "Policy Analysis": ("behavioural",
        "Policy analysis is the use of statistical evidence to evaluate and inform government policy decisions. "
        "Officials engaged in policy analysis must be able to translate data findings into actionable recommendations. "
        "Strong policy analysis skills require both statistical competence and understanding of the policy context. "
        "Senior officers routinely support policy analysis inputs for ministries and planning bodies. "
        "Training in policy analysis helps bridge the gap between raw data and effective governance."),
    "Governance Ethics": ("behavioural",
        "Governance ethics covers integrity, confidentiality, and conduct rules applicable to government officials. "
        "Officials handling respondent data must uphold strict governance ethics regarding confidentiality. "
        "Understanding governance ethics helps officers navigate conflicts of interest appropriately. "
        "Violations of governance ethics can result in disciplinary action under government service rules. "
        "Regular training reinforces governance ethics as a core value of the official statistical system."),
}

skill_map = {}
for name, (category, description) in SKILLS.items():
    skill = db.query(models.Skill).filter(models.Skill.name == name).first()
    if not skill:
        skill = models.Skill(name=name, category=models.SkillCategory(category), description=description)
        db.add(skill)
        db.flush()
    skill_map[name] = skill
db.commit()
print(f"Seeded {len(skill_map)} skills.")

# Also create a Competency row per skill (passing_score = 70)
for name, skill in skill_map.items():
    comp = db.query(models.Competency).filter(models.Competency.skill_id == skill.id).first()
    if not comp:
        db.add(models.Competency(
            skill_id=skill.id, name=f"{name} Competency",
            description=f"Demonstrated proficiency in {name}.", passing_score=70,
        ))
db.commit()

# ---------------------------------------------------------------------------
# 3. Role -> Competency Requirements
# ---------------------------------------------------------------------------
ROLE_REQUIREMENTS = {
    "Statistical Investigator": [
        ("Statistical Literacy", 60, True),
        ("Data Collection", 65, True),
        ("Survey Methodology", 55, True),
        ("MS Excel Proficiency", 50, True),
        ("Communication Skills", 50, False),
        ("Governance Ethics", 60, True),
        ("Cyber Security Awareness", 50, True),
    ],
    "Statistical Officer": [
        ("Statistical Literacy", 70, True),
        ("Survey Methodology", 70, True),
        ("Sampling Techniques", 65, True),
        ("Data Analysis", 65, True),
        ("MS Excel Proficiency", 65, True),
        ("Report Writing", 60, True),
        ("Digital Governance", 55, False),
        ("e-Office Proficiency", 60, True),
        ("Team Management", 55, False),
    ],
    "Senior Statistical Officer": [
        ("Statistical Analysis", 80, True),
        ("Sampling Techniques", 80, True),
        ("National Accounts", 70, False),
        ("Index Numbers", 70, False),
        ("Data Visualization", 70, True),
        ("Programming Fundamentals", 65, False),
        ("Policy Analysis", 75, True),
        ("Leadership", 75, True),
        ("Project Management", 70, True),
        ("Governance Ethics", 75, True),
    ],
}

req_count = 0
for role_name, reqs in ROLE_REQUIREMENTS.items():
    role = role_map[role_name]
    for skill_name, level, mandatory in reqs:
        skill = skill_map[skill_name]
        existing = db.query(models.RoleCompetencyRequirement).filter(
            models.RoleCompetencyRequirement.role_id == role.id,
            models.RoleCompetencyRequirement.skill_id == skill.id,
        ).first()
        if not existing:
            db.add(models.RoleCompetencyRequirement(
                role_id=role.id, skill_id=skill.id,
                required_level=level, is_mandatory=mandatory,
            ))
            req_count += 1
db.commit()
print(f"Seeded {req_count} role competency requirements.")

# ---------------------------------------------------------------------------
# 4. Course catalogue (iGOT Karmayogi + NSSTA/TPAC)
# ---------------------------------------------------------------------------
course_count = sync_igot_catalogue(db)
print(f"Synced {course_count} courses (iGOT Karmayogi + NSSTA/TPAC).")

# ---------------------------------------------------------------------------
# 5. Diagnostic quizzes - one per skill, auto-generated from skill description
# ---------------------------------------------------------------------------
diag_quiz_count = 0
for name, skill in skill_map.items():
    existing_quiz = db.query(models.Quiz).filter(
        models.Quiz.skill_id == skill.id, models.Quiz.quiz_type == "diagnostic"
    ).first()
    if existing_quiz:
        continue

    generated = generate_mcqs(skill.description or name, topic_hint=name, num_questions=5)
    if not generated:
        continue

    quiz = models.Quiz(
        skill_id=skill.id,
        title=f"Diagnostic Assessment: {name}",
        quiz_type="diagnostic",
        created_by=None,
        is_published=True,
    )
    db.add(quiz)
    db.flush()

    for q in generated:
        db.add(models.QuizQuestion(
            quiz_id=quiz.id,
            question_text=q["question_text"],
            option_a=q["option_a"], option_b=q["option_b"],
            option_c=q["option_c"], option_d=q["option_d"],
            correct_option=q["correct_option"],
            explanation=q.get("explanation", ""),
            topic=q.get("topic", name),
            difficulty=models.DifficultyLevel(q.get("difficulty", "medium")),
        ))
    diag_quiz_count += 1

db.commit()
print(f"Seeded {diag_quiz_count} diagnostic quizzes.")

# ---------------------------------------------------------------------------
# 6. Final assessment quizzes - one per course, based on course description
#    plus its mapped skill's description (for richer question pool)
# ---------------------------------------------------------------------------
final_quiz_count = 0
courses = db.query(models.Course).all()
for course in courses:
    existing_quiz = db.query(models.Quiz).filter(
        models.Quiz.course_id == course.id, models.Quiz.quiz_type == "final"
    ).first()
    if existing_quiz:
        continue

    mapped_skill = course.skill_mappings[0].skill if course.skill_mappings else None
    source_text = (course.description or "") + " " + (mapped_skill.description if mapped_skill else "")
    generated = generate_mcqs(source_text, topic_hint=course.title, num_questions=5)
    if not generated:
        continue

    quiz = models.Quiz(
        course_id=course.id,
        skill_id=mapped_skill.id if mapped_skill else None,
        title=f"Final Assessment: {course.title}",
        quiz_type="final",
        created_by=None,
        is_published=True,
    )
    db.add(quiz)
    db.flush()

    for q in generated:
        db.add(models.QuizQuestion(
            quiz_id=quiz.id,
            question_text=q["question_text"],
            option_a=q["option_a"], option_b=q["option_b"],
            option_c=q["option_c"], option_d=q["option_d"],
            correct_option=q["correct_option"],
            explanation=q.get("explanation", ""),
            topic=q.get("topic", course.title),
            difficulty=models.DifficultyLevel(q.get("difficulty", "medium")),
        ))
    final_quiz_count += 1

db.commit()
print(f"Seeded {final_quiz_count} final assessment quizzes.")

# ---------------------------------------------------------------------------
# 7. Demo users
# ---------------------------------------------------------------------------
def get_or_create_user(email, full_name, password, role):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            email=email, full_name=full_name,
            hashed_password=hash_password(password),
            role=models.UserRole(role),
        )
        db.add(user)
        db.flush()
    return user

demo_employee = get_or_create_user(
    "employee@statsaksham.gov.in", "Anita Sharma", "Employee@123", "employee"
)
demo_trainer = get_or_create_user(
    "trainer@statsaksham.gov.in", "Rajesh Kumar", "Trainer@123", "trainer"
)
demo_admin = get_or_create_user(
    "admin@statsaksham.gov.in", "Priya Nair", "Admin@123", "admin"
)
db.commit()
print("Seeded demo users: employee@statsaksham.gov.in / Employee@123 | "
      "trainer@statsaksham.gov.in / Trainer@123 | admin@statsaksham.gov.in / Admin@123")

# ---------------------------------------------------------------------------
# 8. Demo employee profile with a few pre-rated skills
# ---------------------------------------------------------------------------
profile = db.query(models.EmployeeProfile).filter(
    models.EmployeeProfile.user_id == demo_employee.id
).first()

if not profile:
    profile = models.EmployeeProfile(
        user_id=demo_employee.id,
        employee_code="SI-2024-0451",
        department="Field Operations Division",
        organisation="National Sample Survey Office",
        designation="Statistical Investigator Grade II",
        current_role_id=role_map["Statistical Investigator"].id,
        target_role_id=role_map["Statistical Officer"].id,
        grade="Grade II",
        experience_years=3.5,
        qualification="M.Sc. Statistics",
        specialization="Survey Statistics",
        previous_training="Basic Statistics Training Programme (2022)",
        preferred_language="English",
        weekly_learning_hours=5,
        self_assessed_level=models.SelfLevel.intermediate,
    )
    db.add(profile)
    db.flush()

    # Pre-seed a few skills with self-ratings and starting scores so the
    # skill-gap report / dashboards have some data immediately after login.
    starter_skills = [
        ("Statistical Literacy", 62),
        ("Data Collection", 68),
        ("Survey Methodology", 45),
        ("MS Excel Proficiency", 55),
        ("Communication Skills", 40),
        ("Sampling Techniques", 30),
        ("Data Analysis", 20),
    ]
    for skill_name, score in starter_skills:
        skill = skill_map[skill_name]
        db.add(models.EmployeeSkill(
            profile_id=profile.id, skill_id=skill.id,
            self_rating=models.SelfLevel.intermediate,
            diagnostic_score=score, current_score=score,
            competency_achieved=score >= 85,
        ))
    db.commit()
    print("Seeded demo employee profile (Anita Sharma) with starter skill scores.")
else:
    print("Demo employee profile already exists - skipped.")

db.close()
print("\nSeeding complete. StatSaksham AI is ready to run.")
