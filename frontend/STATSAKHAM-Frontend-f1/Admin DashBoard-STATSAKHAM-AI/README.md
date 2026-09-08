# STATSAKHAM Frontend

Generated multi-page admin frontend for the SIH solution.

## Stack
- HTML5
- CSS3
- Bootstrap 5.3
- Vanilla JavaScript
- Bootstrap Icons
- Chart.js
- Fetch API / JSON

## Pages
login.html
dashboard.html
employees.html
departments.html
competencies.html
competency-framework.html
skill-gaps.html
emerging-skills.html
igot-courses.html
nssta-programs.html
learning-paths.html
training-analytics.html
materials.html
quiz-generator.html
question-bank.html
assessment-analytics.html
workforce-analytics.html
reports.html
notifications.html
settings.html

## Backend hooks
The frontend assumes `API_BASE_URL = "/api"`.

Suggested Spring Boot endpoints:
GET  /api/admin/dashboard
GET  /api/admin/employees
GET  /api/admin/departments
GET  /api/admin/competencies
GET  /api/admin/skill-gaps
GET  /api/admin/training
GET  /api/admin/learning-paths
GET  /api/admin/materials
GET  /api/admin/assessments
GET  /api/admin/emerging-skills
GET  /api/admin/reports

POST /api/auth/login
POST /api/admin/employees
POST /api/admin/competencies
POST /api/admin/materials (multipart upload)
POST /api/ai/skill-gap-analysis
POST /api/ai/generate-quiz
POST /api/ai/generate-mcqs
POST /api/ai/recommend-training
POST /api/ai/generate-learning-path
POST /api/ai/workforce-insights
POST /api/ai/emerging-skills

## Important behavior
- Initial values are zero / empty states.
- No fake AI result is embedded.
- AI buttons call backend AI endpoints and render returned JSON.
- Table search, sorting and CSV export are implemented.
- Bootstrap modals and forms are wired for create/edit/upload flows.
- Loading and success/error toast states are implemented.
- iGOT/NSSTA endpoints are intentionally represented as project integration hooks, not claimed as official endpoint names.
