(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const API_BASE_URL = '/api';
  const STORAGE_KEY = 'statskshamEmployee.v2';
  const BRAND = 'STATSAKHAM-AI';

  // API-ready identifiers. Keep these stable when wiring Spring Boot/iGOT APIs.
  const COMPETENCY_TAGS = [
    { id: 'STAT-SURVEY-DESIGN', domain: 'Statistical', name: 'Survey Design', targetLevel: 3 },
    { id: 'STAT-SAMPLING', domain: 'Statistical', name: 'Sampling', targetLevel: 3 },
    { id: 'STAT-DATA-QUALITY', domain: 'Statistical', name: 'Data Quality', targetLevel: 3 },
    { id: 'TECH-PYTHON', domain: 'Technical', name: 'Python', targetLevel: 3 },
    { id: 'TECH-SQL', domain: 'Technical', name: 'SQL', targetLevel: 3 },
    { id: 'TECH-AI-ML', domain: 'Technical', name: 'AI/ML', targetLevel: 2 },
    { id: 'DG-CYBERSECURITY', domain: 'Digital Governance', name: 'Cybersecurity', targetLevel: 3 },
    { id: 'DG-DATA-PRIVACY', domain: 'Digital Governance', name: 'Data Privacy', targetLevel: 3 },
    { id: 'BEH-COMMUNICATION', domain: 'Behavioural', name: 'Communication', targetLevel: 3 }
  ];

  const COURSE_CATALOG = [
    { id: 'IGOT-AI-FOUNDATIONS', title: 'AI Foundations for Government', provider: 'iGOT Karmayogi', providerKey: 'IGOT', type: 'IGOT_COURSE', skillId: 'TECH-AI-ML', skill: 'AI/ML', level: 'Intermediate', durationHours: 6, icon: 'bi-stars', description: 'Build practical understanding of AI, responsible AI and government use cases.', modules: ['AI fundamentals', 'Responsible AI', 'Government use cases', 'Mini assessment'] },
    { id: 'NSSTA-SURVEY-SAMPLING', title: 'Survey Design & Sampling Methods', provider: 'NSSTA / TPAC', providerKey: 'NSSTA_TPAC', type: 'NSSTA_TPAC_PROGRAM', skillId: 'STAT-SAMPLING', skill: 'Sampling', level: 'Intermediate', durationHours: 8, icon: 'bi-bar-chart', description: 'Strengthen survey design, sampling frames, estimation and quality considerations.', modules: ['Survey objectives', 'Sampling designs', 'Estimation', 'Quality checks'] },
    { id: 'IGOT-PYTHON-DATA', title: 'Python for Data Analysis', provider: 'iGOT Karmayogi', providerKey: 'IGOT', type: 'IGOT_COURSE', skillId: 'TECH-PYTHON', skill: 'Python', level: 'Beginner', durationHours: 10, icon: 'bi-code-slash', description: 'Learn Python workflows for cleaning, analysis and reproducible statistical work.', modules: ['Python basics', 'Pandas', 'Data cleaning', 'Analysis practice'] },
    { id: 'IGOT-SQL-DATA', title: 'SQL & Data Management', provider: 'iGOT Karmayogi', providerKey: 'IGOT', type: 'IGOT_COURSE', skillId: 'TECH-SQL', skill: 'SQL', level: 'Intermediate', durationHours: 7, icon: 'bi-database', description: 'Query, join and manage structured datasets for analytical reporting.', modules: ['SELECT & filters', 'Joins', 'Aggregation', 'Practical queries'] },
    { id: 'NSSTA-DATA-QUALITY', title: 'Data Quality & Official Statistics', provider: 'NSSTA / TPAC', providerKey: 'NSSTA_TPAC', type: 'NSSTA_TPAC_PROGRAM', skillId: 'STAT-DATA-QUALITY', skill: 'Data Quality', level: 'Intermediate', durationHours: 5, icon: 'bi-check2-circle', description: 'Apply quality dimensions and quality frameworks to official statistical outputs.', modules: ['Quality dimensions', 'Validation', 'Metadata', 'Quality reporting'] },
    { id: 'IGOT-CYBER-PRIVACY', title: 'Cybersecurity & Data Privacy', provider: 'iGOT Karmayogi', providerKey: 'IGOT', type: 'IGOT_COURSE', skillId: 'DG-CYBERSECURITY', skill: 'Cybersecurity', level: 'Beginner', durationHours: 4, icon: 'bi-shield-lock', description: 'Improve secure digital practices and privacy awareness in government work.', modules: ['Threats', 'Account security', 'Privacy basics', 'Incident awareness'] }
  ];

  const QUESTIONS = [
    { id: 'Q-001', domain: 'Technical', skillId: 'TECH-PYTHON', skill: 'Python', question: 'Which Python structure is most suitable for storing key-value pairs?', options: ['List', 'Tuple', 'Dictionary', 'Set'], answer: 2 },
    { id: 'Q-002', domain: 'Statistical', skillId: 'STAT-SAMPLING', skill: 'Sampling', question: 'What is the main purpose of stratified sampling?', options: ['Increase file size', 'Ensure representation of important subgroups', 'Remove all bias automatically', 'Avoid collecting data'], answer: 1 },
    { id: 'Q-003', domain: 'Technical', skillId: 'TECH-SQL', skill: 'SQL', question: 'Which SQL clause filters rows before grouping?', options: ['ORDER BY', 'WHERE', 'HAVING', 'LIMIT'], answer: 1 },
    { id: 'Q-004', domain: 'Statistical', skillId: 'STAT-DATA-QUALITY', skill: 'Data Quality', question: 'Which is a core data-quality dimension?', options: ['Accuracy', 'Screen brightness', 'CPU speed', 'Font size'], answer: 0 },
    { id: 'Q-005', domain: 'Digital Governance', skillId: 'DG-CYBERSECURITY', skill: 'Cybersecurity', question: 'What is the safest approach for a sensitive government account?', options: ['Reuse one password', 'Share credentials', 'Use MFA and unique credentials', 'Disable logging'], answer: 2 },
    { id: 'Q-006', domain: 'Technical', skillId: 'TECH-DATA-VIZ', skill: 'Data Visualization', question: 'Which chart is generally suitable for showing a trend over time?', options: ['Line chart', 'Pie chart only', 'Radar chart only', 'Scatter-free table'], answer: 0 },
    { id: 'Q-007', domain: 'Statistical', skillId: 'STAT-SURVEY-DESIGN', skill: 'Survey Design', question: 'A questionnaire should primarily be designed to:', options: ['Maximize ambiguity', 'Collect valid information aligned to objectives', 'Increase page count', 'Avoid testing'], answer: 1 },
    { id: 'Q-008', domain: 'Digital Governance', skillId: 'DG-DATA-PRIVACY', skill: 'Data Privacy', question: 'Data minimization means:', options: ['Collecting everything', 'Collecting only what is necessary for the purpose', 'Deleting all data immediately', 'Publishing personal data'], answer: 1 },
    { id: 'Q-009', domain: 'Behavioural', skillId: 'BEH-COMMUNICATION', skill: 'Communication', question: 'An effective official briefing should be:', options: ['Unstructured', 'Clear, evidence-based and audience-aware', 'Only technical jargon', 'Without conclusions'], answer: 1 },
    { id: 'Q-010', domain: 'Technical', skillId: 'TECH-AI-ML', skill: 'AI/ML', question: 'What is a validation set commonly used for?', options: ['Tuning model choices before final testing', 'Replacing training data', 'Storing passwords', 'Formatting reports'], answer: 0 }
  ];

  function emptySkills() {
    return COMPETENCY_TAGS.map((s) => ({ ...s, currentLevel: 0 }));
  }

  function defaultState() {
    return {
      schemaVersion: 2,
      loggedIn: false,
      rememberMe: false,
      employee: {
        name: '', id: '', email: '', department: '', designation: '', location: '',
        education: '', experience: '', assignment: '', training: ''
      },
      skills: emptySkills(),
      diagnosticAnswers: Array(QUESTIONS.length).fill(null),
      diagnosticResult: null,
      currentQuestion: 0,
      courses: {},
      lastQuiz: { score: 0, percentage: 0, topic: '', attempted: false },
      notifications: [],
      context: {}
    };
  }

  function normalizeState(raw) {
    const base = defaultState();
    if (!raw || raw.schemaVersion !== 2) return base;
    const merged = { ...base, ...raw, employee: { ...base.employee, ...(raw.employee || {}) }, lastQuiz: { ...base.lastQuiz, ...(raw.lastQuiz || {}) } };
    merged.skills = COMPETENCY_TAGS.map((tag) => {
      const old = (raw.skills || []).find((s) => s.id === tag.id || s[0] === tag.domain && s[1] === tag.name);
      return { ...tag, currentLevel: Number(old?.currentLevel ?? old?.[2] ?? 0) || 0 };
    });
    merged.diagnosticAnswers = Array.isArray(raw.diagnosticAnswers) && raw.diagnosticAnswers.length === QUESTIONS.length ? raw.diagnosticAnswers : Array(QUESTIONS.length).fill(null);
    merged.currentQuestion = Math.max(0, Math.min(QUESTIONS.length - 1, Number(raw.currentQuestion) || 0));
    merged.courses = raw.courses && typeof raw.courses === 'object' ? raw.courses : {};
    merged.notifications = Array.isArray(raw.notifications) ? raw.notifications : [];
    return merged;
  }

  function loadState() {
    try { return normalizeState(JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')); }
    catch (e) { return defaultState(); }
  }

  let state = loadState();
  let visibleAll = true;

  function saveState() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  function initials(name) { return String(name || 'E').trim().split(/\s+/).filter(Boolean).slice(0, 2).map((x) => x[0]).join('').toUpperCase() || 'E'; }
  function esc(value) { return String(value ?? '').replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m])); }
  function levelName(value) { return ['Foundation', 'Beginner', 'Intermediate', 'Advanced'][Math.max(0, Math.min(3, Number(value) || 0))]; }
  function toast(message) { const root = $('toastRoot'); if (!root) return; root.innerHTML = `<div class="toast">${esc(message)}</div>`; setTimeout(() => { root.innerHTML = ''; }, 2200); }

  function showAuth() {
    $('loadingPage').classList.add('hidden');
    $('dashboardPage').classList.add('hidden');
    $('authPage').classList.remove('hidden');
    closeProfileMenu();
  }

  function showDashboard() {
    $('loadingPage').classList.add('hidden');
    $('authPage').classList.add('hidden');
    $('dashboardPage').classList.remove('hidden');
    renderAll();
    const requested = (location.hash || '#home').slice(1);
    showPage(PAGES.includes(requested) ? requested : 'home', false);
  }

  const PAGES = ['home', 'profile', 'skills', 'diagnostic', 'recommendations', 'learning', 'quiz', 'competency'];
  const TITLES = { home: 'Dashboard', profile: 'My Profile', skills: 'Skills & Competency', diagnostic: 'Diagnostic Assessment', recommendations: 'AI Recommendations', learning: 'My Learning Path', quiz: 'AI Quiz & Practice', competency: 'Competency Growth' };

  function showPage(page, push = true) {
    if (!PAGES.includes(page)) page = 'home';
    PAGES.forEach((p) => $(p + 'Page').classList.toggle('hidden', p !== page));
    document.querySelectorAll('.nav-btn[data-page]').forEach((b) => b.classList.toggle('active', b.dataset.page === page));
    $('topbarTitle').textContent = TITLES[page];
    if (push) history.replaceState(null, '', '#' + page);
    closeProfileMenu();
    if (page === 'profile') renderProfile();
    if (page === 'skills') renderSkills();
    if (page === 'diagnostic') renderDiagnostic();
    if (page === 'recommendations') renderRecommendations();
    if (page === 'learning') renderLearning();
    if (page === 'quiz') renderQuizLanding();
    if (page === 'competency') renderCompetency();
    if (window.innerWidth <= 720) $('sidebar')?.classList.remove('mobile-open');
  }

  function setAuthTab(tab) {
    $('loginPanel').classList.toggle('hidden', tab !== 'login');
    $('signupPanel').classList.toggle('hidden', tab !== 'signup');
    document.querySelectorAll('.auth-tab').forEach((b) => b.classList.toggle('active', b.dataset.authTab === tab));
  }

  function renderIdentity() {
    const e = state.employee;
    const name = e.name || 'Employee';
    $('miniName').textContent = name;
    $('miniAvatar').textContent = initials(name);
    $('profileAvatar').textContent = initials(name);
    $('welcomeName').textContent = name.split(/\s+/)[0];
  }

  function renderProfile() {
    const e = state.employee;
    renderIdentity();
    $('profileName').textContent = e.name || 'Employee';
    $('profileRole').textContent = [e.designation, e.department].filter(Boolean).join(' • ') || 'Employee';
    $('profileId').textContent = e.id || 'Not connected';
    $('profileFields').innerHTML = [
      ['Department', e.department], ['Designation', e.designation], ['Email', e.email], ['Location', e.location],
      ['Education', e.education], ['Experience', e.experience], ['Current Assignment', e.assignment], ['Previous Training', e.training]
    ].map(([label, value]) => `<div class="info-box"><small>${esc(label)}</small><b>${esc(value || 'Not provided')}</b></div>`).join('');
    $('profileEducation').value = e.education || '';
    $('profileExperience').value = e.experience || '';
    $('profileAssignment').value = e.assignment || '';
    $('profileTraining').value = e.training || '';
  }

  function renderSkills() {
    const tb = $('skillsTable');
    tb.innerHTML = state.skills.map((s) => {
      const gap = Math.max(0, s.targetLevel - s.currentLevel);
      const cls = gap >= 2 ? 'gap-high' : gap === 1 ? 'gap-medium' : 'gap-low';
      return `<tr data-skill-id="${esc(s.id)}" data-domain="${esc(s.domain)}" data-skill="${esc(s.name)}">
        <td>${esc(s.domain)}</td><td><b>${esc(s.name)}</b></td>
        <td><select class="level-select" data-skill-current="${esc(s.id)}" aria-label="Current level for ${esc(s.name)}">${[0,1,2,3].map(v => `<option value="${v}" ${v === s.currentLevel ? 'selected' : ''}>${levelName(v)}</option>`).join('')}</select></td>
        <td><span class="tag backend-tag" data-competency-id="${esc(s.id)}" data-domain="${esc(s.domain)}" data-skill="${esc(s.name)}">${esc(levelName(s.targetLevel))}</span></td>
        <td><span class="gap-chip ${cls}" data-gap-for="${esc(s.id)}">${gap ? gap + ' level gap' : 'Ready'}</span></td>
      </tr>`;
    }).join('');
    tb.querySelectorAll('[data-skill-current]').forEach((el) => el.addEventListener('change', () => {
      const skill = state.skills.find((s) => s.id === el.dataset.skillCurrent);
      if (!skill) return;
      skill.currentLevel = Number(el.value) || 0;
      saveState(); renderSkills(); renderDashboard(); renderCompetency();
      toast('Competency profile updated');
    }));
  }

  function courseState(id) {
    if (!state.courses[id]) state.courses[id] = { status: 'Not Started', progress: 0, completedModules: [] };
    const s = state.courses[id];
    s.progress = Math.max(0, Math.min(100, Number(s.progress) || 0));
    if (!Array.isArray(s.completedModules)) s.completedModules = [];
    return s;
  }

  function overallProgress() {
    return Math.round(COURSE_CATALOG.reduce((sum, c) => sum + courseState(c.id).progress, 0) / COURSE_CATALOG.length);
  }

  function recommendedCourses() {
    // Until the recommendation API is connected, return the catalog without claiming fake AI scores.
    return COURSE_CATALOG.slice();
  }

  function renderDashboard() {
    const result = state.diagnosticResult;
    const gaps = state.skills.filter((s) => s.targetLevel > s.currentLevel).length;
    $('dashSkillLevel').textContent = result ? result.level : 'Not Assessed';
    $('dashGaps').textContent = gaps;
    $('dashCourses').textContent = recommendedCourses().length;
    $('dashProgress').textContent = overallProgress() + '%';
    $('skillBars').innerHTML = state.skills.slice(0, 6).map((s) => `<div class="skill-row"><div class="skill-label"><span>${esc(s.name)}</span><b>${levelName(s.currentLevel)} / ${levelName(s.targetLevel)}</b></div><div class="bar-bg"><div class="bar-fill" style="width:${Math.round(s.currentLevel / 3 * 100)}%"></div></div></div>`).join('');
    const gap = state.skills.find((s) => s.targetLevel - s.currentLevel >= 2) || state.skills.find((s) => s.targetLevel > s.currentLevel);
    $('nextAction').innerHTML = gap
      ? `<span class="action-tag">SKILL GAP</span><b class="d-block mt-2">Build ${esc(gap.name)}</b><p>Connect the recommendation API to load the highest-priority training for this competency.</p><button class="btn-primary-custom" data-page="recommendations">View Training</button>`
      : `<span class="action-tag">API READY</span><b class="d-block mt-2">Connect your competency data</b><p>Your current competency values are initialized to zero so backend assessment data can populate them.</p>`;
    renderContinue(); renderNotifications();
    $('nextAction').querySelector('[data-page]')?.addEventListener('click', () => showPage('recommendations'));
  }

  function renderContinue() {
    const active = COURSE_CATALOG.filter((c) => courseState(c.id).status !== 'Not Started').slice(0, 3);
    const list = active.length ? active : recommendedCourses().slice(0, 2);
    $('continueList').innerHTML = list.map((c) => {
      const s = courseState(c.id);
      return `<div class="list-item"><div class="list-main"><b>${esc(c.title)}</b><small>${s.status === 'Not Started' ? 'Available' : s.progress + '% complete'}</small></div><button class="btn-outline-custom" data-course-id="${esc(c.id)}">${s.status === 'Not Started' ? 'View' : 'Continue'}</button></div>`;
    }).join('');
    $('continueList').querySelectorAll('[data-course-id]').forEach((b) => b.addEventListener('click', () => openCourse(b.dataset.courseId)));
  }

  function renderNotifications() {
    const items = state.notifications.length ? state.notifications.slice(0, 3) : [{ title: 'No new notifications', time: 'All caught up' }];
    $('notificationList').innerHTML = items.map((n) => `<div class="notification"><i class="bi bi-bell"></i><div><b>${esc(n.title)}</b><span>${esc(n.time)}</span></div></div>`).join('');
  }

  function renderDiagnostic() {
    const i = Math.min(QUESTIONS.length - 1, Math.max(0, state.currentQuestion));
    const q = QUESTIONS[i];
    $('questionNumber').textContent = `Question ${i + 1} of ${QUESTIONS.length}`;
    $('questionDomain').textContent = q.domain + ' • ' + q.skill;
    $('questionText').textContent = q.question;
    $('testProgress').style.width = ((i + 1) / QUESTIONS.length * 100) + '%';
    $('nextQuestion').textContent = i === QUESTIONS.length - 1 ? 'Submit Assessment' : 'Next →';
    $('prevQuestion').disabled = i === 0;
    $('diagnosticStatus').textContent = state.diagnosticResult ? 'Completed' : 'In Progress';
    $('questionValidation').innerHTML = '';
    $('questionOptions').innerHTML = q.options.map((o, j) => `<label class="option ${state.diagnosticAnswers[i] === j ? 'selected' : ''}"><input type="radio" name="diag" value="${j}" ${state.diagnosticAnswers[i] === j ? 'checked' : ''}>${esc(o)}</label>`).join('');
    $('questionOptions').querySelectorAll('.option').forEach((el) => el.addEventListener('click', () => { state.diagnosticAnswers[i] = Number(el.querySelector('input').value); saveState(); renderDiagnostic(); }));
    if (state.diagnosticResult) {
      $('resultCard').classList.remove('hidden');
      $('resultCard').innerHTML = `<div class="panel-head"><div><h3>Assessment completed</h3><p>Result stored locally for this frontend demo and ready to be replaced by the assessment API.</p></div><span class="status-pill">${state.diagnosticResult.percentage}% • ${esc(state.diagnosticResult.level)}</span></div><div class="grid-2"><div class="metric-card"><div><b>${state.diagnosticResult.percentage}%</b><small>Diagnostic score</small></div></div><button class="btn-primary-custom" data-page="recommendations">View AI Recommendations →</button></div>`;
      $('resultCard').querySelector('[data-page]').addEventListener('click', () => showPage('recommendations'));
    } else $('resultCard').classList.add('hidden');
  }

  function calculateDiagnostic() {
    let score = 0;
    state.diagnosticAnswers.forEach((answer, i) => { if (answer === QUESTIONS[i].answer) score += 1; });
    const percentage = Math.round(score / QUESTIONS.length * 100);
    const level = percentage >= 80 ? 'Advanced' : percentage >= 60 ? 'Intermediate' : percentage >= 35 ? 'Developing' : 'Beginner';
    return { score, percentage, level, attemptedAt: new Date().toISOString() };
  }

  function renderRecommendations() {
    $('recommendSub').textContent = state.diagnosticResult ? `Assessment result: ${state.diagnosticResult.percentage}%. Course progress starts at 0% and is ready for API updates.` : 'Course catalog is ready. Connect the recommendation API to return personalized training based on competency gaps.';
    $('courseList').innerHTML = (visibleAll ? COURSE_CATALOG : recommendedCourses()).map((c) => {
      const s = courseState(c.id);
      return `<div class="panel course-card" data-course-id="${esc(c.id)}" data-provider-key="${esc(c.providerKey)}" data-course-type="${esc(c.type)}" data-skill-id="${esc(c.skillId)}" data-domain="${esc((COMPETENCY_TAGS.find(x => x.id === c.skillId) || {}).domain || '')}">
        <div class="course-icon"><i class="bi ${esc(c.icon)}"></i></div><div>
        <div class="course-title">${esc(c.title)}</div><div class="course-desc">${esc(c.description)}</div>
        <div class="course-meta"><span class="pill backend-tag" data-provider="${esc(c.providerKey)}">${esc(c.provider)}</span><span class="pill" data-level="${esc(c.level)}">${esc(c.level)}</span><span class="pill" data-duration-hours="${c.durationHours}">${c.durationHours} hrs</span><span class="pill" data-progress="${s.progress}">${s.progress}%</span></div>
        </div><button class="btn-primary-custom" data-course-action="open" data-course-id="${esc(c.id)}">${s.status === 'Not Started' ? 'View & Start' : s.status === 'In Progress' ? 'Continue' : 'Review'}</button></div>`;
    }).join('');
    $('courseList').querySelectorAll('[data-course-action="open"]').forEach((b) => b.addEventListener('click', () => openCourse(b.dataset.courseId)));
  }

  function renderLearning() {
    const vals = COURSE_CATALOG.map((c) => courseState(c.id));
    $('learningProgress').textContent = overallProgress() + '%';
    $('completedCount').textContent = vals.filter((s) => s.status === 'Completed').length;
    $('inProgressCount').textContent = vals.filter((s) => s.status === 'In Progress').length;
    $('notStartedCount').textContent = vals.filter((s) => s.status === 'Not Started').length;
    $('journeyList').innerHTML = COURSE_CATALOG.map((c) => {
      const s = courseState(c.id);
      return `<div class="journey-item" data-course-id="${esc(c.id)}" data-provider-key="${esc(c.providerKey)}" data-course-type="${esc(c.type)}" data-skill-id="${esc(c.skillId)}">
        <div class="journey-head"><div><b>${esc(c.title)}</b><div class="muted" style="text-align:left;margin:3px 0 0;font-size:9px">${esc(c.provider)} • ${c.durationHours} hrs</div></div><span class="status ${s.status === 'Completed' ? 'done' : s.status === 'In Progress' ? 'in' : 'not'}">${esc(s.status)}</span></div>
        <div class="progress-label" style="font-size:9px;color:#667085">${s.progress}% complete</div><div class="progress-track"><div class="progress-fill" style="width:${s.progress}%"></div></div>
        <button class="btn-outline-custom" data-course-action="open" data-course-id="${esc(c.id)}">${s.status === 'Not Started' ? 'Start Course' : s.status === 'Completed' ? 'Review' : 'Continue Course'}</button>
      </div>`;
    }).join('');
    $('journeyList').querySelectorAll('[data-course-action="open"]').forEach((b) => b.addEventListener('click', () => openCourse(b.dataset.courseId)));
  }

  function openCourse(id) {
    const c = COURSE_CATALOG.find((x) => x.id === id);
    if (!c) return toast('Course not found');
    const s = courseState(id);
    const modules = c.modules.map((m, i) => `<div class="list-item"><div class="list-main"><b>Module ${i + 1} — ${esc(m)}</b><small>${s.completedModules.includes(i) ? 'Completed' : 'Ready to complete'}</small></div><button class="btn-outline-custom" data-module="${i}" ${s.completedModules.includes(i) ? 'disabled' : ''}>${s.completedModules.includes(i) ? 'Done' : 'Complete'}</button></div>`).join('');
    openModal(c.title, `<p class="muted" style="text-align:left">${esc(c.description)}</p><div class="course-meta"><span class="pill backend-tag">${esc(c.provider)}</span><span class="pill">${esc(c.type)}</span><span class="pill">${esc(c.level)}</span><span class="pill">${c.durationHours} hrs</span><span class="pill">Progress ${s.progress}%</span></div><h5 style="font-size:13px;margin-top:18px">Modules</h5><div id="modules">${modules}</div><div class="progress-track"><div class="progress-fill" style="width:${s.progress}%"></div></div><small>${s.progress}% complete</small>`, 'Close');
    $('modalRoot').querySelectorAll('[data-module]').forEach((b) => b.addEventListener('click', () => {
      const i = Number(b.dataset.module); const st = courseState(id);
      if (!st.completedModules.includes(i)) st.completedModules.push(i);
      st.progress = Math.round(st.completedModules.length / c.modules.length * 100);
      st.status = st.progress >= 100 ? 'Completed' : 'In Progress';
      saveState(); closeModal(); renderAll(); toast(st.status === 'Completed' ? 'Course completed' : 'Module completed');
      if (location.hash === '#learning') renderLearning();
      if (location.hash === '#recommendations') renderRecommendations();
    }));
  }

  function renderQuizLanding() {
    $('quizArea').classList.add('hidden');
    $('quizArea').innerHTML = '';
  }

  function generateQuiz() {
    const topic = $('quizTopic').value;
    const count = Number($('quizCount').value) || 5;
    const difficulty = $('quizDifficulty').value;
    const normalized = topic.toLowerCase();
    let bank = QUESTIONS.slice();
    if (normalized.includes('python')) bank = QUESTIONS.filter(q => q.skillId === 'TECH-PYTHON').concat(QUESTIONS.filter(q => q.domain === 'Technical'));
    if (normalized.includes('sampling')) bank = QUESTIONS.filter(q => q.skillId === 'STAT-SAMPLING' || q.skillId === 'STAT-SURVEY-DESIGN');
    if (normalized.includes('sql')) bank = QUESTIONS.filter(q => q.skillId === 'TECH-SQL').concat(QUESTIONS.filter(q => q.domain === 'Technical'));
    if (normalized.includes('visual')) bank = QUESTIONS.filter(q => q.skill === 'Data Visualization').concat(QUESTIONS);
    if (normalized.includes('ai')) bank = QUESTIONS.filter(q => q.skillId === 'TECH-AI-ML').concat(QUESTIONS);
    const qs = bank.slice(0, Math.min(count, bank.length));
    $('quizArea').classList.remove('hidden');
    $('quizArea').dataset.done = '1';
    $('quizArea').innerHTML = `<div class="panel-head"><div><h3>${esc(topic)} — ${esc(difficulty)} Practice Quiz</h3><p>Frontend demo quiz. Initial stored score is 0 until an assessment is attempted.</p></div><span class="status-pill" data-quiz-score="0">Score: 0%</span></div><div id="quizQuestions">${qs.map((q, i) => `<div class="quiz-question" data-question-id="${esc(q.id)}"><b>${i + 1}. ${esc(q.question)}</b>${q.options.map((o, j) => `<label><input type="radio" name="quiz${i}" value="${j}"> ${esc(o)}</label>`).join('')}</div>`).join('')}</div><button class="btn-primary-custom" id="submitQuiz">Submit Quiz</button><div id="quizResult" style="margin-top:12px"></div>`;
    $('submitQuiz').addEventListener('click', () => {
      let score = 0;
      qs.forEach((q, i) => { const selected = document.querySelector(`input[name="quiz${i}"]:checked`); if (selected && Number(selected.value) === q.answer) score += 1; });
      const percentage = qs.length ? Math.round(score / qs.length * 100) : 0;
      state.lastQuiz = { score, percentage, topic, attempted: true, attemptedAt: new Date().toISOString() };
      saveState();
      $('quizArea').querySelector('[data-quiz-score]').textContent = `Score: ${percentage}%`;
      $('quizResult').innerHTML = `<div class="success-msg">Score: <b>${percentage}%</b>. Result is stored locally and can be replaced with the assessment API response.</div>`;
      state.notifications.unshift({ title: `${topic} practice quiz completed — ${percentage}%`, time: 'Just now' });
      saveState(); renderNotifications(); toast('Quiz submitted successfully');
    });
  }

  function renderCompetency() {
    $('growthBars').innerHTML = state.skills.slice(0, 7).map((s) => `<div class="growth-row"><div class="growth-label"><span>${esc(s.name)}</span><b>${levelName(s.currentLevel)}</b></div><div class="bar-bg"><div class="bar-fill before" style="width:0%"></div></div><div class="bar-bg"><div class="bar-fill current" style="width:${Math.round(s.currentLevel / 3 * 100)}%"></div></div></div>`).join('');
    const completed = COURSE_CATALOG.filter((c) => courseState(c.id).status === 'Completed').length;
    $('growthInsight').innerHTML = completed ? `Completed courses: <b>${completed}</b>. Re-run the diagnostic assessment to measure competency improvement.` : `Current competency scores are initialized to <b>0</b> for API integration. Complete learning and assessments after the backend is connected to populate growth data.`;
    $('futureSkills').innerHTML = ['Advanced Data Visualization', 'Applied AI/ML', 'Cloud Computing', 'APIs & Open Data', 'Metadata Standards', 'Project Management'].map((x) => `<span class="tag backend-tag" data-skill-recommendation="${esc(x)}">${esc(x)}</span>`).join('');
  }

  function openModal(title, body, closeText = 'Close') {
    closeModal();
    $('modalRoot').innerHTML = `<div class="modal-backdrop" id="modalBackdrop"><div class="modal-box"><div class="modal-head"><b>${esc(title)}</b><button class="modal-close" id="modalClose" aria-label="Close">×</button></div><div class="modal-body">${body}</div><div class="modal-actions"><button class="btn-outline-custom" id="modalClose2">${esc(closeText)}</button></div></div></div>`;
    $('modalClose').onclick = closeModal;
    $('modalClose2').onclick = closeModal;
    $('modalBackdrop').onclick = (e) => { if (e.target.id === 'modalBackdrop') closeModal(); };
  }
  function closeModal() { $('modalRoot').innerHTML = ''; }

  function editProfile() {
    const e = state.employee;
    openModal('Edit Profile', `<form id="editProfileForm" class="form-grid"><div><label>Full Name</label><input id="edName" value="${esc(e.name)}"></div><div class="two-col"><div><label>Department</label><input id="edDept" value="${esc(e.department)}"></div><div><label>Designation</label><input id="edDes" value="${esc(e.designation)}"></div></div><div class="two-col"><div><label>Email</label><input id="edEmail" value="${esc(e.email)}"></div><div><label>Location</label><input id="edLoc" value="${esc(e.location)}"></div></div><div id="editMsg"></div></form>`, 'Save Changes');
    $('modalRoot').querySelector('#modalClose2').onclick = () => {
      const name = $('edName').value.trim(), department = $('edDept').value.trim(), designation = $('edDes').value.trim(), email = $('edEmail').value.trim(), location = $('edLoc').value.trim();
      if (!name || !department || !designation || !location || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { $('editMsg').innerHTML = '<div class="error-msg">Please complete all fields with a valid email.</div>'; return; }
      state.employee = { ...state.employee, name, department, designation, email, location };
      saveState(); renderAll(); closeModal(); toast('Profile updated successfully');
    };
  }

  function openNotifications() {
    const items = state.notifications.length ? state.notifications : [{ title: 'No new notifications', time: 'All caught up' }];
    openModal('Notifications', items.map((n) => `<div class="notification"><i class="bi bi-bell"></i><div><b>${esc(n.title)}</b><span>${esc(n.time)}</span></div></div>`).join(''));
  }

  function openSettings() {
    openModal('Portal Settings', `<div class="form-grid"><label class="check"><input id="settingRemember" type="checkbox" ${state.rememberMe ? 'checked' : ''}> Keep me signed in on this browser</label><div class="info-box"><small>API base URL</small><b>${esc(API_BASE_URL)}</b></div><div class="info-box"><small>Integration status</small><b>Frontend ready — backend not connected</b></div></div>`, 'Save Settings');
    $('modalRoot').querySelector('#modalClose2').onclick = () => { state.rememberMe = $('settingRemember').checked; saveState(); closeModal(); toast('Settings saved'); };
  }

  function closeProfileMenu() { $('profileMenu')?.classList.add('hidden'); $('profileChip')?.setAttribute('aria-expanded', 'false'); }
  function toggleProfileMenu(e) { e?.stopPropagation(); const menu = $('profileMenu'); const chip = $('profileChip'); if (!menu) return; const opening = menu.classList.contains('hidden'); menu.classList.toggle('hidden', !opening); chip?.setAttribute('aria-expanded', String(opening)); }

  function loginWithIdentity(identity) {
    const existing = state.employee.id && (state.employee.id.toLowerCase() === identity.toLowerCase() || state.employee.email.toLowerCase() === identity.toLowerCase());
    if (!existing) {
      state.employee = { name: '', id: identity, email: identity.includes('@') ? identity : '', department: '', designation: '', location: '', education: '', experience: '', assignment: '', training: '' };
      state.skills = emptySkills(); state.diagnosticAnswers = Array(QUESTIONS.length).fill(null); state.diagnosticResult = null; state.courses = {}; state.lastQuiz = { score: 0, percentage: 0, topic: '', attempted: false };
    }
    state.loggedIn = true;
    state.rememberMe = $('rememberMe').checked;
    saveState(); showDashboard(); toast(`Welcome to ${BRAND}`);
  }

  function renderAll() { renderIdentity(); renderProfile(); renderSkills(); renderDashboard(); renderLearning(); renderCompetency(); }

  function init() {
    setTimeout(() => state.loggedIn && state.rememberMe ? showDashboard() : showAuth(), 350);

    document.querySelectorAll('[data-auth-tab]').forEach((b) => b.addEventListener('click', () => setAuthTab(b.dataset.authTab)));
    $('[data-switch-signup]')?.addEventListener('click', () => setAuthTab('signup'));
    $('[data-switch-login]')?.addEventListener('click', () => setAuthTab('login'));
    document.querySelectorAll('[data-toggle-pass]').forEach((b) => b.addEventListener('click', () => { const input = $(b.dataset.togglePass); input.type = input.type === 'password' ? 'text' : 'password'; }));

    // Event delegation keeps navigation working for buttons rendered later.
    document.addEventListener('click', (e) => {
      const pageButton = e.target.closest('[data-page]');
      if (pageButton) { e.preventDefault(); showPage(pageButton.dataset.page); }
    });

    $('loginForm').onsubmit = (e) => {
      e.preventDefault();
      const id = $('loginIdentity').value.trim(); const pw = $('loginPassword').value;
      if (!id || !pw) { $('loginMessage').innerHTML = '<div class="error-msg">Enter your Employee ID/email and password.</div>'; return; }
      loginWithIdentity(id);
    };

    $('employeeIdBtn').onclick = () => { $('loginIdentity').value = 'EMP00123'; $('loginPassword').value = '123456'; toast('Demo credentials filled. Login to continue.'); };
    $('forgotBtn').onclick = () => { openModal('Reset Password', '<div><label>Employee ID / Email</label><input id="resetId" placeholder="Employee ID or email"></div><div id="resetMsg" style="margin-top:10px"></div>', 'Generate Instructions'); $('modalRoot').querySelector('#modalClose2').onclick = () => { if (!$('resetId').value.trim()) { $('resetMsg').innerHTML = '<div class="error-msg">Enter your Employee ID or email.</div>'; return; } $('resetMsg').innerHTML = '<div class="success-msg">Demo reset instructions generated. Connect your authentication API to send the real reset message.</div>'; }; };

    $('signupForm').onsubmit = (e) => {
      e.preventDefault();
      const name = $('suName').value.trim(), id = $('suId').value.trim(), email = $('suEmail').value.trim(), department = $('suDept').value.trim(), designation = $('suDesignation').value.trim(), pass = $('suPass').value;
      if (!name || !id || !email || !department || !designation || pass.length < 6 || pass !== $('suConfirm').value) { $('signupMessage').innerHTML = '<div class="error-msg">Please complete all fields and use matching passwords (6+ characters).</div>'; return; }
      state = defaultState(); state.employee = { ...state.employee, name, id, email, department, designation }; state.loggedIn = true; state.rememberMe = true; saveState(); showDashboard(); toast('Account created');
    };

    $('editProfileBtn').onclick = editProfile;
    $('saveContext').onclick = () => { state.employee.education = $('profileEducation').value.trim(); state.employee.experience = $('profileExperience').value.trim(); state.employee.assignment = $('profileAssignment').value.trim(); state.employee.training = $('profileTraining').value.trim(); saveState(); renderProfile(); toast('Professional context saved'); };
    $('analyzeSkillsBtn').onclick = () => { const gaps = state.skills.filter((s) => s.targetLevel > s.currentLevel); $('skillAnalysis').classList.remove('hidden'); $('skillAnalysis').innerHTML = `<div class="panel-head"><div><h3>AI skill-gap analysis</h3><p>Frontend-only preview. Backend AI endpoint can replace this result.</p></div><span class="status-pill">${gaps.length} gaps</span></div><p style="font-size:11px;color:#475467">Backend-ready competency IDs: <b>${gaps.slice(0, 4).map((s) => esc(s.id)).join(', ') || 'NONE'}</b>.</p>`; toast('Skill-gap analysis preview ready'); };
    $('prevQuestion').onclick = () => { if (state.currentQuestion > 0) { state.currentQuestion -= 1; saveState(); renderDiagnostic(); } };
    $('nextQuestion').onclick = () => { const i = state.currentQuestion; if (state.diagnosticAnswers[i] == null) { $('questionValidation').innerHTML = '<div class="error-msg">Please select an answer before continuing.</div>'; return; } if (i < QUESTIONS.length - 1) { state.currentQuestion += 1; saveState(); renderDiagnostic(); } else { state.diagnosticResult = calculateDiagnostic(); state.currentQuestion = 0; saveState(); renderAll(); showPage('diagnostic'); toast('Diagnostic assessment completed'); } };
    $('refreshRecommendations').onclick = () => { renderRecommendations(); toast('Recommendation catalog refreshed'); };
    $('generateQuizBtn').onclick = generateQuiz;
    $('reassessBtn').onclick = () => { state.diagnosticResult = null; state.diagnosticAnswers = Array(QUESTIONS.length).fill(null); state.currentQuestion = 0; saveState(); showPage('diagnostic'); toast('New diagnostic assessment started'); };
    $('notifyBtn').onclick = openNotifications;
    $('notifySide').onclick = openNotifications;
    $('viewNotifications').onclick = openNotifications;
    $('profileChip').onclick = toggleProfileMenu;
    $('profileMenuProfile').onclick = () => showPage('profile');
    $('profileMenuSettings').onclick = openSettings;
    $('profileMenuLogout').onclick = () => { state.loggedIn = false; state.rememberMe = false; saveState(); showAuth(); setAuthTab('login'); toast('Logged out successfully'); };
    $('logoutBtn').onclick = () => { state.loggedIn = false; state.rememberMe = false; saveState(); showAuth(); setAuthTab('login'); toast('Logged out successfully'); };
    $('resetBtn').onclick = () => { state = defaultState(); saveState(); showAuth(); setAuthTab('login'); $('loginMessage').innerHTML = ''; toast('Frontend demo data reset'); };
    $('mobileToggle').onclick = () => $('sidebar').classList.toggle('mobile-open');
    document.addEventListener('click', (e) => { if (!e.target.closest('#profileArea')) closeProfileMenu(); });
    window.onpopstate = () => { if (state.loggedIn) showPage((location.hash || '#home').slice(1), false); };
  }

  init();
})();
