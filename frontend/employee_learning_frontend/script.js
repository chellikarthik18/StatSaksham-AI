(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const API_BASE_URL = 'http://127.0.0.1:8000/api';
  const TOKEN_KEY = 'statsksham_employee_token';
  const BRAND = 'STATSAKHAM-AI';

  function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
  function setToken(t) { localStorage.setItem(TOKEN_KEY, t); }
  function clearToken() { localStorage.removeItem(TOKEN_KEY); }

  async function api(path, options = {}) {
    const isFormData = options.body instanceof FormData;
    const headers = Object.assign(
      isFormData ? {} : { 'Content-Type': 'application/json' },
      getToken() ? { 'Authorization': 'Bearer ' + getToken() } : {},
      options.headers || {}
    );
    const res = await fetch(API_BASE_URL + path, { ...options, headers });
    if (res.status === 401) {
      clearToken();
      showAuth();
      throw new Error('Session expired. Please sign in again.');
    }
    if (!res.ok) {
      let detail = `Request failed (${res.status})`;
      try { const body = await res.json(); if (body && body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail); } catch (e) { /* ignore */ }
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  }
  const apiGet = (path) => api(path);
  const apiPost = (path, data) => api(path, { method: 'POST', body: JSON.stringify(data || {}) });
  const apiPut = (path, data) => api(path, { method: 'PUT', body: JSON.stringify(data || {}) });

  // ---- Client-side view state (populated from the backend after login) ----
  let COURSE_CATALOG = [];
  let QUESTIONS = [];

  function defaultState() {
    return {
      loggedIn: false,
      rememberMe: false,
      employee: { name: '', id: '', email: '', department: '', designation: '', location: '', education: '', experience: '', assignment: '', training: '' },
      skills: [],
      diagnosticAnswers: [],
      diagnosticResult: null,
      currentQuestion: 0,
      courses: {},
      lastQuiz: { score: 0, percentage: 0, topic: '', attempted: false },
      currentQuiz: null,
      notifications: []
    };
  }

  let state = defaultState();
  let visibleAll = true;

  function initials(name) { return String(name || 'E').trim().split(/\s+/).filter(Boolean).slice(0, 2).map((x) => x[0]).join('').toUpperCase() || 'E'; }
  function esc(value) { return String(value ?? '').replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m])); }
  function levelName(value) { return ['Foundation', 'Beginner', 'Intermediate', 'Advanced'][Math.max(0, Math.min(3, Number(value) || 0))]; }
  function toast(message) { const root = $('toastRoot'); if (!root) return; root.innerHTML = `<div class="toast">${esc(message)}</div>`; setTimeout(() => { root.innerHTML = ''; }, 2200); }
  function timeAgo(iso) { if (!iso) return ''; const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleString(); }

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
      ['Department', e.department], ['Designation', e.designation], ['Email', e.email], ['Phone', e.location],
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
    tb.querySelectorAll('[data-skill-current]').forEach((el) => el.addEventListener('change', async () => {
      const skill = state.skills.find((s) => s.id === el.dataset.skillCurrent);
      if (!skill) return;
      const newLevel = Number(el.value) || 0;
      try {
        await apiPut('/employee/skills', { updates: [{ skill_id: skill.id, current_level: newLevel }] });
        skill.currentLevel = newLevel;
        renderSkills(); renderDashboard(); renderCompetency();
        toast('Competency profile updated');
      } catch (err) { toast(err.message || 'Could not update competency'); el.value = skill.currentLevel; }
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
    if (!COURSE_CATALOG.length) return 0;
    return Math.round(COURSE_CATALOG.reduce((sum, c) => sum + courseState(c.id).progress, 0) / COURSE_CATALOG.length);
  }

  function recommendedCourses() { return COURSE_CATALOG.slice(); }

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
      ? `<span class="action-tag">SKILL GAP</span><b class="d-block mt-2">Build ${esc(gap.name)}</b><p>AI-recommended courses for this competency are ready in your recommendations.</p><button class="btn-primary-custom" data-page="recommendations">View Training</button>`
      : `<span class="action-tag">ON TRACK</span><b class="d-block mt-2">Great work</b><p>You're meeting the required level across your assessed competencies.</p>`;
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
    if (!QUESTIONS.length) {
      $('questionNumber').textContent = 'No questions available';
      $('questionOptions').innerHTML = '';
      return;
    }
    const i = Math.min(QUESTIONS.length - 1, Math.max(0, state.currentQuestion));
    const q = QUESTIONS[i];
    $('questionNumber').textContent = `Question ${i + 1} of ${QUESTIONS.length}`;
    $('questionDomain').textContent = q.domain + ' • ' + (q.skill || '');
    $('questionText').textContent = q.question;
    $('testProgress').style.width = ((i + 1) / QUESTIONS.length * 100) + '%';
    $('nextQuestion').textContent = i === QUESTIONS.length - 1 ? 'Submit Assessment' : 'Next →';
    $('prevQuestion').disabled = i === 0;
    $('diagnosticStatus').textContent = state.diagnosticResult ? 'Completed' : 'In Progress';
    $('questionValidation').innerHTML = '';
    $('questionOptions').innerHTML = q.options.map((o, j) => `<label class="option ${state.diagnosticAnswers[i] === j ? 'selected' : ''}"><input type="radio" name="diag" value="${j}" ${state.diagnosticAnswers[i] === j ? 'checked' : ''}>${esc(o)}</label>`).join('');
    $('questionOptions').querySelectorAll('.option').forEach((el) => el.addEventListener('click', () => { state.diagnosticAnswers[i] = Number(el.querySelector('input').value); renderDiagnostic(); }));
    if (state.diagnosticResult) {
      $('resultCard').classList.remove('hidden');
      $('resultCard').innerHTML = `<div class="panel-head"><div><h3>Assessment completed</h3><p>Result computed and stored by the AI assessment service.</p></div><span class="status-pill">${state.diagnosticResult.percentage}% • ${esc(state.diagnosticResult.level)}</span></div><div class="grid-2"><div class="metric-card"><div><b>${state.diagnosticResult.percentage}%</b><small>Diagnostic score</small></div></div><button class="btn-primary-custom" data-page="recommendations">View AI Recommendations →</button></div>`;
      $('resultCard').querySelector('[data-page]').addEventListener('click', () => showPage('recommendations'));
    } else $('resultCard').classList.add('hidden');
  }

  function renderRecommendations() {
    $('recommendSub').textContent = state.diagnosticResult ? `Assessment result: ${state.diagnosticResult.percentage}%. Courses below are prioritised against your open skill gaps.` : 'Complete the diagnostic assessment for personalised, gap-driven recommendations. Showing the general catalogue for now.';
    $('courseList').innerHTML = (visibleAll ? COURSE_CATALOG : recommendedCourses()).map((c) => {
      const s = courseState(c.id);
      return `<div class="panel course-card" data-course-id="${esc(c.id)}" data-provider-key="${esc(c.providerKey)}" data-course-type="${esc(c.type)}" data-skill-id="${esc(c.skillId)}">
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
    $('modalRoot').querySelectorAll('[data-module]').forEach((b) => b.addEventListener('click', async () => {
      const i = Number(b.dataset.module);
      try {
        if (courseState(id).status === 'Not Started') await apiPost(`/employee/learning-path/enroll/${id}`, {});
        const result = await apiPut(`/employee/learning-path/${id}/complete-module`, { module_index: i });
        const st = courseState(id);
        if (!st.completedModules.includes(i)) st.completedModules.push(i);
        st.progress = result.progress; st.status = result.status;
        closeModal(); renderAll(); toast(st.status === 'Completed' ? 'Course completed' : 'Module completed');
        if (location.hash === '#learning') renderLearning();
        if (location.hash === '#recommendations') renderRecommendations();
      } catch (err) { toast(err.message || 'Could not update progress'); }
    }));
  }

  function renderQuizLanding() {
    $('quizArea').classList.add('hidden');
    $('quizArea').innerHTML = '';
  }

  async function generateQuiz() {
    const topic = $('quizTopic').value || 'General Skills';
    const count = Number($('quizCount').value) || 5;
    const difficulty = $('quizDifficulty').value;
    let quiz;
    try {
      quiz = await apiPost('/employee/quiz/generate', { topic, count, difficulty });
    } catch (err) { toast(err.message || 'Could not generate quiz'); return; }
    state.currentQuiz = quiz;
    const qs = quiz.questions;
    $('quizArea').classList.remove('hidden');
    $('quizArea').dataset.done = '1';
    $('quizArea').innerHTML = `<div class="panel-head"><div><h3>${esc(topic)} — ${esc(difficulty)} Practice Quiz</h3><p>AI-generated from the platform's question engine.</p></div><span class="status-pill" data-quiz-score="0">Score: —</span></div><div id="quizQuestions">${qs.map((q, i) => `<div class="quiz-question" data-question-id="${esc(q.id)}"><b>${i + 1}. ${esc(q.question)}</b>${q.options.map((o, j) => `<label><input type="radio" name="quiz${i}" value="${j}"> ${esc(o)}</label>`).join('')}</div>`).join('')}</div><button class="btn-primary-custom" id="submitQuiz">Submit Quiz</button><div id="quizResult" style="margin-top:12px"></div>`;
    $('submitQuiz').addEventListener('click', async () => {
      const answers = qs.map((q, i) => { const selected = document.querySelector(`input[name="quiz${i}"]:checked`); return selected ? Number(selected.value) : null; });
      try {
        const result = await apiPost('/employee/quiz/submit', { quiz_id: quiz.quizId, answers });
        state.lastQuiz = { score: result.score, percentage: result.percentage, topic, attempted: true, attemptedAt: new Date().toISOString() };
        $('quizArea').querySelector('[data-quiz-score]').textContent = `Score: ${result.percentage}%`;
        $('quizResult').innerHTML = `<div class="success-msg">Score: <b>${result.percentage}%</b> (${result.score}/${result.total}).</div>`;
        await refreshNotifications();
        toast('Quiz submitted successfully');
      } catch (err) { toast(err.message || 'Could not submit quiz'); }
    });
  }

  function renderCompetency() {
    $('growthBars').innerHTML = state.skills.slice(0, 7).map((s) => `<div class="growth-row"><div class="growth-label"><span>${esc(s.name)}</span><b>${levelName(s.currentLevel)}</b></div><div class="bar-bg"><div class="bar-fill before" style="width:0%"></div></div><div class="bar-bg"><div class="bar-fill current" style="width:${Math.round(s.currentLevel / 3 * 100)}%"></div></div></div>`).join('');
    const completed = COURSE_CATALOG.filter((c) => courseState(c.id).status === 'Completed').length;
    $('growthInsight').innerHTML = completed ? `Completed courses: <b>${completed}</b>. Re-run the diagnostic assessment to measure competency improvement.` : `Complete learning and assessments to build your competency growth history.`;
    apiGet('/employee/competency-growth').then((g) => {
      $('futureSkills').innerHTML = (g.futureSkills || []).map((x) => `<span class="tag backend-tag" data-skill-recommendation="${esc(x)}">${esc(x)}</span>`).join('') || '<span class="muted">No emerging-skill data yet.</span>';
    }).catch(() => {});
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
    openModal('Edit Profile', `<form id="editProfileForm" class="form-grid"><div><label>Full Name</label><input id="edName" value="${esc(e.name)}"></div><div class="two-col"><div><label>Department</label><input id="edDept" value="${esc(e.department)}"></div><div><label>Designation</label><input id="edDes" value="${esc(e.designation)}"></div></div><div class="two-col"><div><label>Email</label><input id="edEmail" value="${esc(e.email)}"></div><div><label>Phone</label><input id="edLoc" value="${esc(e.location)}"></div></div><div id="editMsg"></div></form>`, 'Save Changes');
    $('modalRoot').querySelector('#modalClose2').onclick = async () => {
      const name = $('edName').value.trim(), department = $('edDept').value.trim(), designation = $('edDes').value.trim(), email = $('edEmail').value.trim(), phone = $('edLoc').value.trim();
      if (!name || !department || !designation || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { $('editMsg').innerHTML = '<div class="error-msg">Please complete all fields with a valid email.</div>'; return; }
      try {
        await apiPut('/employee/profile', { name, department, designation, email, phone });
        state.employee = { ...state.employee, name, department, designation, email, location: phone };
        renderAll(); closeModal(); toast('Profile updated successfully');
      } catch (err) { $('editMsg').innerHTML = `<div class="error-msg">${esc(err.message || 'Could not save profile')}</div>`; }
    };
  }

  function openNotifications() {
    const items = state.notifications.length ? state.notifications : [{ title: 'No new notifications', time: 'All caught up' }];
    openModal('Notifications', items.map((n) => `<div class="notification"><i class="bi bi-bell"></i><div><b>${esc(n.title)}</b><span>${esc(n.time)}</span></div></div>`).join(''));
  }

  function openSettings() {
    openModal('Portal Settings', `<div class="form-grid"><label class="check"><input id="settingRemember" type="checkbox" ${state.rememberMe ? 'checked' : ''}> Keep me signed in on this browser</label><div class="info-box"><small>API base URL</small><b>${esc(API_BASE_URL)}</b></div><div class="info-box"><small>Integration status</small><b>Connected to STATSAKHAM AI backend</b></div></div>`, 'Save Settings');
    $('modalRoot').querySelector('#modalClose2').onclick = () => { state.rememberMe = $('settingRemember').checked; closeModal(); toast('Settings saved'); };
  }

  function closeProfileMenu() { $('profileMenu')?.classList.add('hidden'); $('profileChip')?.setAttribute('aria-expanded', 'false'); }
  function toggleProfileMenu(e) { e?.stopPropagation(); const menu = $('profileMenu'); const chip = $('profileChip'); if (!menu) return; const opening = menu.classList.contains('hidden'); menu.classList.toggle('hidden', !opening); chip?.setAttribute('aria-expanded', String(opening)); }

  async function refreshNotifications() {
    try {
      const rows = await apiGet('/employee/notifications');
      state.notifications = rows.map((n) => ({ title: n.title, time: timeAgo(n.createdAt) }));
      renderNotifications();
    } catch (e) { /* non-fatal */ }
  }

  function mapCourse(c) {
    return {
      id: String(c.id), title: c.title, provider: c.provider, providerKey: 'IGOT', type: c.type || 'IGOT_COURSE',
      skillId: c.skillId, skill: '', level: c.level, durationHours: c.durationHours, icon: 'bi-mortarboard-fill',
      description: c.description || '', modules: c.modules && c.modules.length ? c.modules : ['Module 1'],
      _progress: c.progress || 0, _status: c.status || 'Not Started', _completedModules: c.completedModules || [],
    };
  }

  async function loadServerData() {
    const [profile, skills, diagResult, recs, notes] = await Promise.all([
      apiGet('/employee/profile'),
      apiGet('/employee/skills'),
      apiGet('/employee/diagnostic/result').catch(() => null),
      apiGet('/employee/recommendations'),
      apiGet('/employee/notifications').catch(() => []),
    ]);

    state.employee = {
      name: profile.name || '', id: profile.employeeId || '', email: profile.email || '',
      department: profile.department || '', designation: profile.designation || '', location: profile.phone || '',
      education: profile.education || '', experience: profile.experienceYears || '',
      assignment: profile.currentAssignment || '', training: profile.previousTraining || '',
    };
    state.skills = (skills || []).map((s) => ({ id: s.skillId, domain: s.domain, name: s.name, currentLevel: s.currentLevel, targetLevel: s.requiredLevel }));
    state.diagnosticResult = diagResult;

    const courses = (recs.courses || []).map(mapCourse);
    COURSE_CATALOG = courses;
    state.courses = {};
    courses.forEach((c) => { state.courses[c.id] = { status: c._status, progress: c._progress, completedModules: c._completedModules || [] }; });

    state.notifications = (notes || []).map((n) => ({ title: n.title, time: timeAgo(n.createdAt) }));

    try {
      const qs = await apiGet('/employee/diagnostic/questions');
      QUESTIONS = qs.map((q) => ({ id: String(q.id), domain: q.domain, skill: q.skill, question: q.question, options: q.options }));
      state.diagnosticAnswers = Array(QUESTIONS.length).fill(null);
    } catch (e) { QUESTIONS = []; }
  }

  async function loginWithCredentials(username, password) {
    const r = await apiPost('/auth/login', { username, password });
    if (r.user.role !== 'employee') throw new Error('This portal is for employee accounts. Admins/trainers should use the Admin Dashboard.');
    setToken(r.token);
    await loadServerData();
    state.loggedIn = true;
    state.rememberMe = $('rememberMe').checked;
    showDashboard(); toast(`Welcome to ${BRAND}`);
  }

  function renderAll() { renderIdentity(); renderProfile(); renderSkills(); renderDashboard(); renderLearning(); renderCompetency(); }

  function init() {
    setTimeout(async () => {
      if (getToken()) {
        try { await loadServerData(); state.loggedIn = true; showDashboard(); return; }
        catch (e) { clearToken(); }
      }
      showAuth();
    }, 350);

    document.querySelectorAll('[data-auth-tab]').forEach((b) => b.addEventListener('click', () => setAuthTab(b.dataset.authTab)));
    document.querySelectorAll('[data-toggle-pass]').forEach((b) => b.addEventListener('click', () => { const input = $(b.dataset.togglePass); input.type = input.type === 'password' ? 'text' : 'password'; }));

    document.addEventListener('click', (e) => {
      const pageButton = e.target.closest('[data-page]');
      if (pageButton) { e.preventDefault(); showPage(pageButton.dataset.page); }
    });

    $('loginForm').onsubmit = async (e) => {
      e.preventDefault();
      const id = $('loginIdentity').value.trim(); const pw = $('loginPassword').value;
      if (!id || !pw) { $('loginMessage').innerHTML = '<div class="error-msg">Enter your Employee ID/email and password.</div>'; return; }
      try { await loginWithCredentials(id, pw); }
      catch (err) { $('loginMessage').innerHTML = `<div class="error-msg">${esc(err.message || 'Invalid credentials')}</div>`; }
    };

    $('employeeIdBtn').onclick = () => { $('loginIdentity').value = 'employee@statsaksham.gov.in'; $('loginPassword').value = 'Employee@123'; toast('Demo credentials filled. Login to continue.'); };
    $('forgotBtn').onclick = () => { openModal('Reset Password', '<div><label>Employee ID / Email</label><input id="resetId" placeholder="Employee ID or email"></div><div id="resetMsg" style="margin-top:10px"></div>', 'Generate Instructions'); $('modalRoot').querySelector('#modalClose2').onclick = () => { if (!$('resetId').value.trim()) { $('resetMsg').innerHTML = '<div class="error-msg">Enter your Employee ID or email.</div>'; return; } $('resetMsg').innerHTML = '<div class="success-msg">Password resets must be requested from your platform administrator.</div>'; }; };

    $('signupForm').onsubmit = async (e) => {
      e.preventDefault();
      const name = $('suName').value.trim(), id = $('suId').value.trim(), email = $('suEmail').value.trim(), department = $('suDept').value.trim(), designation = $('suDesignation').value.trim(), pass = $('suPass').value;
      if (!name || !id || !email || !department || !designation || pass.length < 6 || pass !== $('suConfirm').value) { $('signupMessage').innerHTML = '<div class="error-msg">Please complete all fields and use matching passwords (6+ characters).</div>'; return; }
      try {
        const r = await apiPost('/auth/signup', { name, employee_id: id, email, department, designation, password: pass });
        setToken(r.token);
        await loadServerData();
        state.loggedIn = true; state.rememberMe = true;
        showDashboard(); toast('Account created');
      } catch (err) { $('signupMessage').innerHTML = `<div class="error-msg">${esc(err.message || 'Could not create account')}</div>`; }
    };

    $('editProfileBtn').onclick = editProfile;
    $('saveContext').onclick = async () => {
      const education = $('profileEducation').value.trim(), experience_years = Number($('profileExperience').value) || 0,
            current_assignment = $('profileAssignment').value.trim(), previous_training = $('profileTraining').value.trim();
      try {
        await apiPut('/employee/profile', { education, experience_years, current_assignment, previous_training });
        state.employee.education = education; state.employee.experience = experience_years;
        state.employee.assignment = current_assignment; state.employee.training = previous_training;
        renderProfile(); toast('Professional context saved');
      } catch (err) { toast(err.message || 'Could not save context'); }
    };
    $('analyzeSkillsBtn').onclick = async () => {
      try {
        const result = await apiPost('/employee/skills/analyze', {});
        $('skillAnalysis').classList.remove('hidden');
        $('skillAnalysis').innerHTML = `<div class="panel-head"><div><h3>AI skill-gap analysis</h3><p>Computed from your current competency profile.</p></div><span class="status-pill">${result.gapsIdentified} gaps</span></div><p style="font-size:11px;color:#475467">${(result.items || []).slice(0, 4).map((i) => `${esc(i.skill)} (${esc(i.priority)})`).join(', ') || 'No gaps identified'}</p>`;
        toast('Skill-gap analysis complete');
      } catch (err) { toast(err.message || 'Analysis failed'); }
    };
    $('prevQuestion').onclick = () => { if (state.currentQuestion > 0) { state.currentQuestion -= 1; renderDiagnostic(); } };
    $('nextQuestion').onclick = async () => {
      const i = state.currentQuestion;
      if (state.diagnosticAnswers[i] == null) { $('questionValidation').innerHTML = '<div class="error-msg">Please select an answer before continuing.</div>'; return; }
      if (i < QUESTIONS.length - 1) { state.currentQuestion += 1; renderDiagnostic(); return; }
      try {
        const result = await apiPost('/employee/diagnostic/submit', { answers: state.diagnosticAnswers });
        state.diagnosticResult = result;
        state.currentQuestion = 0;
        const skills = await apiGet('/employee/skills');
        state.skills = skills.map((s) => ({ id: s.skillId, domain: s.domain, name: s.name, currentLevel: s.currentLevel, targetLevel: s.requiredLevel }));
        renderAll(); showPage('diagnostic'); toast('Diagnostic assessment completed');
      } catch (err) { toast(err.message || 'Could not submit assessment'); }
    };
    $('refreshRecommendations').onclick = async () => {
      try { const recs = await apiGet('/employee/recommendations'); COURSE_CATALOG = (recs.courses || []).map(mapCourse); renderRecommendations(); toast('Recommendation catalogue refreshed'); }
      catch (err) { toast(err.message || 'Could not refresh'); }
    };
    $('generateQuizBtn').onclick = generateQuiz;
    $('reassessBtn').onclick = () => { state.diagnosticResult = null; state.diagnosticAnswers = Array(QUESTIONS.length).fill(null); state.currentQuestion = 0; showPage('diagnostic'); toast('New diagnostic assessment started'); };
    $('notifyBtn').onclick = openNotifications;
    $('notifySide').onclick = openNotifications;
    $('viewNotifications').onclick = openNotifications;
    $('profileChip').onclick = toggleProfileMenu;
    $('profileMenuProfile').onclick = () => showPage('profile');
    $('profileMenuSettings').onclick = openSettings;
    const doLogout = () => { clearToken(); state = defaultState(); showAuth(); setAuthTab('login'); toast('Logged out successfully'); };
    $('profileMenuLogout').onclick = doLogout;
    $('logoutBtn').onclick = doLogout;
    $('resetBtn').onclick = doLogout;
    $('mobileToggle').onclick = () => $('sidebar').classList.toggle('mobile-open');
    document.addEventListener('click', (e) => { if (!e.target.closest('#profileArea')) closeProfileMenu(); });
    window.onpopstate = () => { if (state.loggedIn) showPage((location.hash || '#home').slice(1), false); };
  }

  init();
})();
