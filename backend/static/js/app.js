/**
 * Automated Attendance System for Rural Schools
 * Single Page Application Core Architecture
 */

// Application Global State
const state = {
  currentUser: null,
  authToken: null,
  roleInfo: {},
  activeView: 'dashboard',
  classes: [],
  teachers: [],
  settings: {},
  notifications: [],
  unreadNotifications: 0,
  isOnline: navigator.onLine,
  offlineQueue: JSON.parse(localStorage.getItem('rural_attendance_offline_queue') || '[]'),
  attendanceSheet: {
    classId: null,
    date: new Date().toISOString().split('T')[0],
    students: [],
    recordsMap: {}, // studentId -> { status: 'Present'|'Absent'|'Late', remarks: '' }
    originalAttendance: {}
  },
  charts: {}
};

// =========================================================================
// 1. INITIALIZATION & ROUTING
// =========================================================================

document.addEventListener('DOMContentLoaded', async () => {
  initLucide();
  initConnectionListeners();
  checkAuthSession();
});

function initLucide() {
  if (window.lucide) {
    lucide.createIcons();
  }
}

function initConnectionListeners() {
  window.addEventListener('online', () => {
    state.isOnline = true;
    updateConnectionUI();
    showToast('Internet connection restored.', 'success');
    syncOfflineAttendance();
  });
  window.addEventListener('offline', () => {
    state.isOnline = false;
    updateConnectionUI();
    showToast('Offline Mode: Attendance will be saved locally and synced later.', 'warning');
  });
  updateConnectionUI();
}

function updateConnectionUI() {
  const pill = document.getElementById('connection-status-pill');
  const text = document.getElementById('connection-status-text');
  if (!pill || !text) return;

  if (state.isOnline) {
    pill.className = 'hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold';
    text.textContent = state.offlineQueue.length > 0 ? `Online (Syncing ${state.offlineQueue.length})` : 'Online (Sync Active)';
  } else {
    pill.className = 'hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold';
    text.textContent = 'Offline (Local Storage)';
  }
  pill.classList.remove('hidden');
}

function checkAuthSession() {
  const savedToken = localStorage.getItem('rural_att_token') || sessionStorage.getItem('rural_att_token');
  const savedUser = localStorage.getItem('rural_att_user') || sessionStorage.getItem('rural_att_user');
  const savedRoleInfo = localStorage.getItem('rural_att_role_info') || sessionStorage.getItem('rural_att_role_info');

  if (savedToken && savedUser) {
    try {
      state.authToken = savedToken;
      state.currentUser = JSON.parse(savedUser);
      state.roleInfo = savedRoleInfo ? JSON.parse(savedRoleInfo) : {};
      showAppShell();
      loadInitialData();
      return;
    } catch (e) {
      console.error('Failed to parse saved session', e);
    }
  }
  showLoginScreen();
}

// =========================================================================
// 2. AUTHENTICATION & LOGIN MANAGEMENT
// =========================================================================

function showLoginScreen() {
  document.getElementById('login-container').classList.remove('hidden');
  document.getElementById('app-shell').classList.add('hidden');
  initLucide();
}

function showAppShell() {
  document.getElementById('login-container').classList.add('hidden');
  document.getElementById('app-shell').classList.remove('hidden');
  
  // Update Header User Profile
  const nameEl = document.getElementById('header-user-name');
  const roleEl = document.getElementById('header-user-role');
  const avatarEl = document.getElementById('header-user-avatar');
  const emailEl = document.getElementById('dropdown-user-email');

  if (state.currentUser) {
    if (nameEl) nameEl.textContent = state.currentUser.name;
    if (roleEl) roleEl.textContent = state.currentUser.role;
    if (emailEl) emailEl.textContent = state.currentUser.email;
    if (avatarEl) {
      const initials = state.currentUser.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      avatarEl.textContent = initials || 'U';
    }
  }

  renderSidebar();
  navigateTo('dashboard');
  loadNotifications();
  initLucide();
}

async function handleLogin() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value.trim();
  const remember = document.getElementById('login-remember').checked;
  const btn = document.getElementById('btn-login');

  if (!username || !password) {
    showToast('Please enter both username and password.', 'error');
    return;
  }

  const originalBtnContent = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="inline-block animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></span> Authenticating...`;

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (data.success) {
      state.authToken = data.token;
      state.currentUser = data.user;
      state.roleInfo = data.role_info || {};

      const storage = remember ? localStorage : sessionStorage;
      storage.setItem('rural_att_token', data.token);
      storage.setItem('rural_att_user', JSON.stringify(data.user));
      storage.setItem('rural_att_role_info', JSON.stringify(state.roleInfo));

      showToast(`Welcome back, ${data.user.name}!`, 'success');
      showAppShell();
      loadInitialData();
    } else {
      showToast(data.message || 'Login failed. Check your credentials.', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Unable to connect to school server. Please verify network.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalBtnContent;
    initLucide();
  }
}

function fillDemoCredentials(username, password) {
  document.getElementById('login-username').value = username;
  document.getElementById('login-password').value = password;
  handleLogin();
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.innerHTML = '<i data-lucide="eye-off" class="w-4 h-4"></i>';
  } else {
    input.type = 'password';
    btn.innerHTML = '<i data-lucide="eye" class="w-4 h-4"></i>';
  }
  initLucide();
}

function handleLogout() {
  localStorage.removeItem('rural_att_token');
  localStorage.removeItem('rural_att_user');
  localStorage.removeItem('rural_att_role_info');
  sessionStorage.clear();
  state.authToken = null;
  state.currentUser = null;
  state.roleInfo = {};
  showToast('You have been signed out.', 'info');
  showLoginScreen();
}

function openForgotPasswordModal() {
  document.getElementById('modal-forgot-password').classList.remove('hidden');
  initLucide();
}
function closeForgotPasswordModal() {
  document.getElementById('modal-forgot-password').classList.add('hidden');
}

async function handleForgotPassword() {
  const identifier = document.getElementById('forgot-identifier').value.trim();
  if (!identifier) return;

  try {
    const res = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      closeForgotPasswordModal();
    } else {
      showToast(data.message || 'Account not found.', 'error');
    }
  } catch (err) {
    showToast('Failed to connect to server.', 'error');
  }
}

// =========================================================================
// 3. API HELPER & INITIAL DATA LOADING
// =========================================================================

async function apiFetch(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {}),
    ...(options.headers || {})
  };

  try {
    const res = await fetch(endpoint, { ...options, headers });
    if (res.status === 401) {
      showToast('Session expired. Please log in again.', 'warning');
      handleLogout();
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    return null;
  }
}

async function loadInitialData() {
  const [classesRes, teachersRes, settingsRes] = await Promise.all([
    apiFetch('/api/classes'),
    apiFetch('/api/teachers'),
    apiFetch('/api/settings')
  ]);

  if (classesRes && classesRes.success) state.classes = classesRes.classes;
  if (teachersRes && teachersRes.success) state.teachers = teachersRes.teachers;
  if (settingsRes && settingsRes.success) state.settings = settingsRes.settings;

  // Populate class dropdown in student modal
  populateModalDropdowns();
}

function populateModalDropdowns() {
  const classSelect = document.getElementById('student-class-id');
  if (classSelect) {
    classSelect.innerHTML = state.classes.map(c => 
      `<option value="${c.id}">${c.class_name} - Section ${c.section}</option>`
    ).join('');
  }

  const teacherSelect = document.getElementById('class-teacher-id');
  if (teacherSelect) {
    teacherSelect.innerHTML = `<option value="">-- Assign Class Teacher --</option>` + 
      state.teachers.map(t => `<option value="${t.id}">${t.name} (${t.subject || 'General'})</option>`).join('');
  }
}

// =========================================================================
// 4. SIDEBAR NAVIGATION & ROUTER
// =========================================================================

function renderSidebar() {
  const nav = document.getElementById('sidebar-nav-items');
  if (!nav) return;

  const role = state.currentUser ? state.currentUser.role : 'student';

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard', roles: ['admin', 'principal', 'teacher', 'student', 'parent'] },
    { id: 'mark-attendance', label: 'Mark Attendance', icon: 'check-square', roles: ['admin', 'principal', 'teacher'] },
    { id: 'attendance-history', label: 'Attendance History', icon: 'history', roles: ['admin', 'principal', 'teacher', 'student', 'parent'] },
    { id: 'reports', label: 'Reports & Registers', icon: 'file-spreadsheet', roles: ['admin', 'principal', 'teacher'] },
    { id: 'students', label: 'Student Management', icon: 'users', roles: ['admin', 'principal', 'teacher'] },
    { id: 'teachers', label: 'Teacher Management', icon: 'user-check', roles: ['admin', 'principal'] },
    { id: 'classes', label: 'Class Management', icon: 'book-open', roles: ['admin', 'principal'] },
    { id: 'notifications', label: 'SMS & Notifications', icon: 'bell', roles: ['admin', 'principal', 'teacher', 'student', 'parent'] },
    { id: 'settings', label: 'Profile & Settings', icon: 'settings', roles: ['admin', 'principal', 'teacher', 'student', 'parent'] },
  ];

  const filtered = menuItems.filter(item => item.roles.includes(role));

  nav.innerHTML = filtered.map(item => `
    <button onclick="navigateTo('${item.id}')" id="nav-btn-${item.id}" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-xs font-semibold text-slate-600 hover:bg-emerald-50 hover:text-emerald-700 transition">
      <i data-lucide="${item.icon}" class="w-4 h-4"></i>
      <span>${item.label}</span>
    </button>
  `).join('') + `
    <div class="pt-3 border-t border-slate-100 my-2"></div>
    <button onclick="handleLogout()" class="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-xs font-semibold text-rose-600 hover:bg-rose-50 transition">
      <i data-lucide="log-out" class="w-4 h-4 text-rose-500"></i>
      <span>Sign Out</span>
    </button>
  `;

  initLucide();
}

function navigateTo(viewId) {
  state.activeView = viewId;

  // Update active sidebar style
  document.querySelectorAll('#sidebar-nav-items button').forEach(btn => {
    btn.classList.remove('bg-emerald-600', 'text-white', 'hover:bg-emerald-700', 'shadow-md', 'shadow-emerald-600/20');
    btn.classList.add('text-slate-600', 'hover:bg-emerald-50', 'hover:text-emerald-700');
  });

  const activeBtn = document.getElementById(`nav-btn-${viewId}`);
  if (activeBtn) {
    activeBtn.classList.remove('text-slate-600', 'hover:bg-emerald-50', 'hover:text-emerald-700');
    activeBtn.classList.add('bg-emerald-600', 'text-white', 'shadow-md', 'shadow-emerald-600/20');
  }

  // Close mobile sidebar if open
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar && !sidebar.classList.contains('-translate-x-full')) {
    sidebar.classList.add('-translate-x-full');
    overlay.classList.add('hidden');
  }

  // Render view
  const main = document.getElementById('main-content');
  if (!main) return;

  switch (viewId) {
    case 'dashboard':
      renderDashboardView(main);
      break;
    case 'mark-attendance':
      renderMarkAttendanceView(main);
      break;
    case 'attendance-history':
      renderAttendanceHistoryView(main);
      break;
    case 'reports':
      renderReportsView(main);
      break;
    case 'students':
      renderStudentsView(main);
      break;
    case 'teachers':
      renderTeachersView(main);
      break;
    case 'classes':
      renderClassesView(main);
      break;
    case 'notifications':
      renderNotificationsView(main);
      break;
    case 'settings':
      renderSettingsView(main);
      break;
    default:
      main.innerHTML = `<div class="p-8 text-center text-slate-400">View under construction.</div>`;
  }

  initLucide();
}

function toggleSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!sidebar) return;

  if (sidebar.classList.contains('-translate-x-full')) {
    sidebar.classList.remove('-translate-x-full');
    overlay.classList.remove('hidden');
  } else {
    sidebar.classList.add('-translate-x-full');
    overlay.classList.add('hidden');
  }
}

// =========================================================================
// 5. VIEW: DASHBOARDS (ADMIN / TEACHER / STUDENT / PARENT)
// =========================================================================

async function renderDashboardView(container) {
  container.innerHTML = `<div class="p-12 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-600 border-t-transparent"></div><p class="mt-3 text-xs font-semibold">Loading Dashboard Intelligence...</p></div>`;

  const data = await apiFetch('/api/dashboard/stats');
  if (!data || !data.success) {
    container.innerHTML = `<div class="p-8 text-center text-rose-500 bg-white rounded-3xl border border-rose-100">Failed to load dashboard data.</div>`;
    return;
  }

  const role = data.role;

  if (role === 'admin' || role === 'principal') {
    renderAdminDashboard(container, data);
  } else if (role === 'teacher') {
    renderTeacherDashboard(container, data);
  } else if (role === 'student') {
    renderStudentDashboard(container, data);
  } else if (role === 'parent') {
    renderParentDashboard(container, data);
  }
}

function renderAdminDashboard(container, data) {
  const stats = data.stats || {};
  const totalStudents = stats.total_students || 0;
  const todayPresent = stats.today_present || 0;
  const todayAbsent = stats.today_absent || 0;
  const todayLate = stats.today_late || 0;
  const attendanceRate = totalStudents > 0 ? ((todayPresent / totalStudents) * 100).toFixed(1) : 0;

  // Rural school Mid-Day meal calculation
  const midDayMeals = todayPresent;

  container.innerHTML = `
    <div class="space-y-6 animate-fade-in">
      
      <!-- Top Welcome Banner with Quick Actions -->
      <div class="bg-gradient-to-r from-emerald-800 via-emerald-700 to-teal-800 rounded-3xl p-6 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-emerald-200 text-xs font-semibold backdrop-blur-md mb-2">
            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
            <span>Rural Education Governance Dashboard</span>
          </div>
          <h2 class="text-2xl font-black">Welcome back, ${state.currentUser.name}</h2>
          <p class="text-xs text-emerald-100 mt-1 max-w-xl">
            Live attendance overview for ${state.settings.school_name || 'Green Valley Rural School'}. Real-time synchronization active.
          </p>
        </div>
        <div class="flex items-center space-x-2 flex-wrap gap-2">
          <button onclick="navigateTo('mark-attendance')" class="px-4 py-2.5 rounded-xl bg-white text-emerald-800 text-xs font-bold shadow-lg hover:bg-emerald-50 transition flex items-center space-x-1.5">
            <i data-lucide="check-square" class="w-4 h-4"></i>
            <span>Take Attendance</span>
          </button>
          <button onclick="openStudentModal()" class="px-4 py-2.5 rounded-xl bg-emerald-900/60 hover:bg-emerald-900 border border-emerald-400/30 text-white text-xs font-bold transition flex items-center space-x-1.5">
            <i data-lucide="user-plus" class="w-4 h-4"></i>
            <span>Add Student</span>
          </button>
          <a href="/api/export/attendance/csv" class="px-4 py-2.5 rounded-xl bg-emerald-900/60 hover:bg-emerald-900 border border-emerald-400/30 text-white text-xs font-bold transition flex items-center space-x-1.5">
            <i data-lucide="download" class="w-4 h-4"></i>
            <span>Daily CSV</span>
          </a>
        </div>
      </div>

      <!-- Stat Cards Grid -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        
        <!-- Total Students -->
        <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm stat-card">
          <div class="flex items-center justify-between text-slate-500 mb-2">
            <span class="text-xs font-bold uppercase tracking-wider">Total Enrolled</span>
            <div class="w-9 h-9 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <i data-lucide="users" class="w-5 h-5"></i>
            </div>
          </div>
          <div class="text-2xl font-black text-slate-900">${totalStudents}</div>
          <div class="text-[11px] text-slate-400 mt-1 flex items-center space-x-1">
            <span>Across ${stats.total_classes || 6} Classes</span>
          </div>
        </div>

        <!-- Today's Attendance Rate -->
        <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm stat-card">
          <div class="flex items-center justify-between text-slate-500 mb-2">
            <span class="text-xs font-bold uppercase tracking-wider">Today's Attendance</span>
            <div class="w-9 h-9 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <i data-lucide="percent" class="w-5 h-5"></i>
            </div>
          </div>
          <div class="text-2xl font-black text-emerald-600">${attendanceRate}%</div>
          <div class="text-[11px] text-slate-400 mt-1 flex items-center space-x-1">
            <span class="text-emerald-600 font-semibold">${todayPresent} Present</span>
            <span>•</span>
            <span class="text-rose-500 font-semibold">${todayAbsent} Absent</span>
          </div>
        </div>

        <!-- Mid-Day Meal Impact (Rural Education Specific) -->
        <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm stat-card">
          <div class="flex items-center justify-between text-slate-500 mb-2">
            <span class="text-xs font-bold uppercase tracking-wider">Mid-Day Meals</span>
            <div class="w-9 h-9 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <i data-lucide="utensils" class="w-5 h-5"></i>
            </div>
          </div>
          <div class="text-2xl font-black text-amber-600">${midDayMeals} Meals</div>
          <div class="text-[11px] text-slate-400 mt-1">
            <span>Auto-synced with present count</span>
          </div>
        </div>

        <!-- Low Attendance Attention -->
        <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm stat-card">
          <div class="flex items-center justify-between text-slate-500 mb-2">
            <span class="text-xs font-bold uppercase tracking-wider">Low Attendance (&lt;75%)</span>
            <div class="w-9 h-9 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center">
              <i data-lucide="alert-triangle" class="w-5 h-5"></i>
            </div>
          </div>
          <div class="text-2xl font-black text-rose-600">${stats.low_attendance_count || 0} Students</div>
          <div class="text-[11px] text-slate-400 mt-1">
            <button onclick="navigateTo('reports')" class="text-rose-600 font-semibold hover:underline">View Alert List →</button>
          </div>
        </div>

      </div>

      <!-- Charts & Class Breakdown Row -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- 6-Month Trend Chart -->
        <div class="lg:col-span-7 bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-sm font-bold text-slate-900">Attendance Trend (Past 6 Months)</h3>
              <p class="text-xs text-slate-400">Monthly aggregate attendance percentage</p>
            </div>
            <span class="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold">Government Avg: 82%</span>
          </div>
          <div class="relative h-64 w-full">
            <canvas id="monthlyTrendChart"></canvas>
          </div>
        </div>

        <!-- Class-wise Progress Breakdown -->
        <div class="lg:col-span-5 bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-slate-900">Today's Class Attendance</h3>
            <span class="text-xs text-slate-400 font-medium">All Sections</span>
          </div>
          <div class="space-y-3.5 overflow-y-auto max-h-64 pr-1">
            ${(data.class_summary || []).map(c => {
              const cTotal = c.total_students || 0;
              const cPresent = c.present_today || 0;
              const cPct = cTotal > 0 ? Math.round((cPresent / cTotal) * 100) : 0;
              return `
                <div>
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="font-bold text-slate-800">${c.class_name} - ${c.section}</span>
                    <span class="font-semibold ${cPct < 75 ? 'text-rose-600' : 'text-emerald-600'}">${cPresent}/${cTotal} (${cPct}%)</span>
                  </div>
                  <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div class="h-2 rounded-full ${cPct < 75 ? 'bg-rose-500' : 'bg-emerald-500'}" style="width: ${cPct}%"></div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>

      </div>

      <!-- Recent Attendance Submissions Table -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-sm font-bold text-slate-900">Recent Attendance Logs</h3>
            <p class="text-xs text-slate-400">Latest records logged across all classes</p>
          </div>
          <button onclick="navigateTo('attendance-history')" class="text-xs text-emerald-600 font-bold hover:underline">
            View Complete History →
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="bg-slate-50 text-slate-500 uppercase tracking-wider font-bold border-b border-slate-100">
                <th class="py-3 px-4">Student</th>
                <th class="py-3 px-4">Class</th>
                <th class="py-3 px-4">Date & Time</th>
                <th class="py-3 px-4">Status</th>
                <th class="py-3 px-4">Remarks</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${(data.recent_attendance || []).slice(0, 7).map(r => `
                <tr class="hover:bg-slate-50/75 transition">
                  <td class="py-3 px-4 font-semibold text-slate-800">${r.student_name} <span class="text-slate-400 font-normal text-[11px]">(Roll ${r.roll_number})</span></td>
                  <td class="py-3 px-4 text-slate-600">${r.class_name} - ${r.section}</td>
                  <td class="py-3 px-4 text-slate-500">${r.date} <span class="text-[10px] text-slate-400">${r.time || ''}</span></td>
                  <td class="py-3 px-4">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-bold border ${getStatusBadgeClass(r.status)}">
                      ${r.status}
                    </span>
                  </td>
                  <td class="py-3 px-4 text-slate-500">${r.remarks || '—'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `;

  // Initialize Chart.js Trend
  setTimeout(() => {
    initMonthlyTrendChart(data.monthly_stats || []);
    initLucide();
  }, 50);
}

function renderTeacherDashboard(container, data) {
  const stats = data.stats || {};
  const assignedClasses = data.assigned_classes || [];

  container.innerHTML = `
    <div class="space-y-6 animate-fade-in">
      
      <!-- Welcome Header -->
      <div class="bg-gradient-to-r from-emerald-800 to-teal-900 rounded-3xl p-6 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-emerald-200 text-xs font-semibold backdrop-blur-md mb-2">
            <i data-lucide="book-open" class="w-3.5 h-3.5"></i>
            <span>Teacher Portal</span>
          </div>
          <h2 class="text-2xl font-black">Welcome, ${state.currentUser.name}</h2>
          <p class="text-xs text-emerald-100 mt-1">
            Manage your daily classroom attendance, track attendance rates, and notify parents.
          </p>
        </div>
        <button onclick="navigateTo('mark-attendance')" class="px-5 py-3 rounded-2xl bg-white text-emerald-800 text-xs font-black shadow-lg hover:bg-emerald-50 transition flex items-center space-x-2">
          <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600"></i>
          <span>Take Today's Attendance</span>
        </button>
      </div>

      <!-- Quick Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Assigned Classes</span>
          <div class="text-2xl font-black text-slate-900 mt-1">${stats.assigned_classes_count || 1}</div>
          <p class="text-xs text-slate-500 mt-1">Class Teacher Responsibility</p>
        </div>
        <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Students</span>
          <div class="text-2xl font-black text-emerald-600 mt-1">${stats.total_students || 0}</div>
          <p class="text-xs text-slate-500 mt-1">Active class strength</p>
        </div>
        <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Today's Marking Status</span>
          <div class="text-2xl font-black ${stats.today_marked_classes > 0 ? 'text-emerald-600' : 'text-amber-500'} mt-1">
            ${stats.today_marked_classes > 0 ? 'Completed' : 'Pending'}
          </div>
          <p class="text-xs text-slate-500 mt-1">${stats.today_marked_classes || 0} classes recorded today</p>
        </div>
      </div>

      <!-- Assigned Classes Action Grid -->
      <div class="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
        <h3 class="text-sm font-bold text-slate-900 mb-4">My Assigned Classes</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          ${assignedClasses.map(c => `
            <div class="border border-slate-200/80 rounded-2xl p-4 bg-slate-50/50 hover:bg-slate-50 transition flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="px-2.5 py-0.5 rounded-lg bg-emerald-100 text-emerald-800 text-[11px] font-bold">Section ${c.section}</span>
                  <span class="text-xs text-slate-400 font-medium">${c.room_number || 'Room 201'}</span>
                </div>
                <h4 class="text-base font-extrabold text-slate-900">${c.class_name}</h4>
                <p class="text-xs text-slate-500 mt-0.5">${c.student_count || 0} Enrolled Students</p>
              </div>
              <div class="mt-4 pt-3 border-t border-slate-200/60 flex items-center justify-between">
                <button onclick="startMarkingForClass(${c.id})" class="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center space-x-1">
                  <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                  <span>Mark Sheet</span>
                </button>
                <button onclick="viewClassReport(${c.id})" class="text-xs text-emerald-700 font-semibold hover:underline">
                  Register →
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Teacher's Recent Submissions -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-6">
        <h3 class="text-sm font-bold text-slate-900 mb-3">Recently Recorded Students</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="bg-slate-50 text-slate-500 uppercase tracking-wider font-bold border-b border-slate-100">
                <th class="py-3 px-4">Student</th>
                <th class="py-3 px-4">Class</th>
                <th class="py-3 px-4">Date</th>
                <th class="py-3 px-4">Status</th>
                <th class="py-3 px-4">Remarks</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${(data.recent_attendance || []).map(r => `
                <tr class="hover:bg-slate-50/75 transition">
                  <td class="py-3 px-4 font-semibold text-slate-800">${r.student_name} (Roll ${r.roll_number})</td>
                  <td class="py-3 px-4 text-slate-600">${r.class_name} - ${r.section}</td>
                  <td class="py-3 px-4 text-slate-500">${r.date}</td>
                  <td class="py-3 px-4">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-bold border ${getStatusBadgeClass(r.status)}">
                      ${r.status}
                    </span>
                  </td>
                  <td class="py-3 px-4 text-slate-500">${r.remarks || 'Regular'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `;
  initLucide();
}

function renderStudentDashboard(container, data) {
  const profile = data.student_profile || {};
  const stats = data.stats || {};
  const pct = stats.attendance_percentage || 0;
  const isSafe = pct >= 75.0;

  container.innerHTML = `
    <div class="space-y-6 animate-fade-in">
      
      <!-- Student Profile Card -->
      <div class="bg-gradient-to-r from-emerald-800 to-slate-900 rounded-3xl p-6 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div class="flex items-center space-x-4">
          <div class="w-16 h-16 rounded-2xl bg-emerald-600 text-white flex items-center justify-center text-2xl font-black shadow-lg">
            ${(profile.name || 'S').substring(0, 1)}
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <h2 class="text-2xl font-black">${profile.name}</h2>
              <span class="px-2.5 py-0.5 rounded-full bg-emerald-500/30 border border-emerald-400/40 text-emerald-200 text-xs font-bold">Roll ${profile.roll_number}</span>
            </div>
            <p class="text-xs text-emerald-100 mt-1">
              ${profile.class_name} • Section ${profile.section} • Class Teacher: ${profile.class_teacher_name || 'Sunita Devi'}
            </p>
          </div>
        </div>
        <div class="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10 text-right">
          <span class="text-[11px] text-slate-300 font-semibold block">Today's Attendance</span>
          <span class="text-lg font-black ${stats.today_status === 'Present' ? 'text-emerald-400' : (stats.today_status === 'Absent' ? 'text-rose-400' : 'text-amber-300')}">
            ${stats.today_status}
          </span>
          <span class="text-[10px] text-slate-400 block">${stats.today_time ? `Marked at ${stats.today_time}` : ''}</span>
        </div>
      </div>

      <!-- Percentage Gauge & Stats Cards -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Attendance Percentage Card -->
        <div class="lg:col-span-5 bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex flex-col items-center justify-center text-center">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Overall Attendance Score</span>
          <div class="relative w-40 h-40 flex items-center justify-center">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" stroke="#f1f5f9" stroke-width="9" fill="transparent"/>
              <circle cx="50" cy="50" r="40" stroke="${isSafe ? '#10b981' : '#f43f5e'}" stroke-width="9" stroke-linecap="round" fill="transparent" stroke-dasharray="251.2" stroke-dashoffset="${251.2 - (251.2 * pct) / 100}"/>
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-3xl font-black ${isSafe ? 'text-emerald-600' : 'text-rose-600'}">${pct}%</span>
              <span class="text-[10px] font-bold text-slate-400">Total Score</span>
            </div>
          </div>
          <div class="mt-4 px-3.5 py-1.5 rounded-full ${isSafe ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'} text-xs font-bold">
            ${isSafe ? '✓ Above 75% Rural School Standard' : '⚠ Below Minimum Attendance Threshold'}
          </div>
        </div>

        <!-- Breakdown Metric Cards -->
        <div class="lg:col-span-7 grid grid-cols-2 gap-4">
          <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm stat-card">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Working Days</span>
            <div class="text-2xl font-black text-slate-900 mt-2">${stats.total_working_days || 0}</div>
            <p class="text-[11px] text-slate-400 mt-1">Academic Year 2026-27</p>
          </div>
          <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm stat-card">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Present Days</span>
            <div class="text-2xl font-black text-emerald-600 mt-2">${stats.present_days || 0}</div>
            <p class="text-[11px] text-emerald-600 font-semibold mt-1">Regularly attended</p>
          </div>
          <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm stat-card">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Absent Days</span>
            <div class="text-2xl font-black text-rose-600 mt-2">${stats.absent_days || 0}</div>
            <p class="text-[11px] text-slate-400 mt-1">Parent notified</p>
          </div>
          <div class="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm stat-card">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Late Arrivals</span>
            <div class="text-2xl font-black text-amber-600 mt-2">${stats.late_days || 0}</div>
            <p class="text-[11px] text-slate-400 mt-1">Recorded by teacher</p>
          </div>
        </div>

      </div>

      <!-- My Attendance History Table -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-6">
        <h3 class="text-sm font-bold text-slate-900 mb-4">My Attendance Log</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="bg-slate-50 text-slate-500 uppercase tracking-wider font-bold border-b border-slate-100">
                <th class="py-3 px-4">Date</th>
                <th class="py-3 px-4">Time</th>
                <th class="py-3 px-4">Status</th>
                <th class="py-3 px-4">Remarks</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${(data.recent_history || []).map(r => `
                <tr class="hover:bg-slate-50/75 transition">
                  <td class="py-3 px-4 font-semibold text-slate-800">${r.date}</td>
                  <td class="py-3 px-4 text-slate-500">${r.time || '08:30:00'}</td>
                  <td class="py-3 px-4">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-bold border ${getStatusBadgeClass(r.status)}">
                      ${r.status}
                    </span>
                  </td>
                  <td class="py-3 px-4 text-slate-500">${r.remarks || 'Regular'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `;
  initLucide();
}

function renderParentDashboard(container, data) {
  const parent = data.parent_profile || {};
  const children = data.children || [];

  container.innerHTML = `
    <div class="space-y-6 animate-fade-in">
      
      <!-- Welcome Header -->
      <div class="bg-gradient-to-r from-emerald-800 via-slate-800 to-teal-900 rounded-3xl p-6 text-white shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-emerald-200 text-xs font-semibold backdrop-blur-md mb-2">
            <i data-lucide="heart-handshake" class="w-3.5 h-3.5"></i>
            <span>Rural Parent Portal</span>
          </div>
          <h2 class="text-2xl font-black">Hello, ${parent.name}</h2>
          <p class="text-xs text-emerald-100 mt-1">
            Real-time daily attendance updates & SMS notification history for your registered children.
          </p>
        </div>
        <div class="text-xs bg-white/10 px-4 py-2 rounded-2xl border border-white/10 text-emerald-300 font-semibold">
          Registered Mobile: ${parent.phone || '+91 98765 00007'}
        </div>
      </div>

      <!-- Children Attendance Cards -->
      <div class="space-y-6">
        ${children.map((chData, idx) => {
          const ch = chData.child;
          const stats = chData.stats;
          const pct = stats.attendance_percentage;
          const isSafe = pct >= 75.0;

          return `
            <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-6">
              
              <!-- Child Header -->
              <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
                <div class="flex items-center space-x-3">
                  <div class="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-black text-base">
                    ${ch.name.substring(0, 1)}
                  </div>
                  <div>
                    <h3 class="text-lg font-black text-slate-900">${ch.name}</h3>
                    <p class="text-xs text-slate-500">${ch.class_name} - Section ${ch.section} • Roll No: ${ch.roll_number}</p>
                  </div>
                </div>

                <!-- Today's Status Badge -->
                <div class="flex items-center space-x-3">
                  <div class="text-right">
                    <span class="text-[10px] text-slate-400 uppercase font-bold block">Today's Status</span>
                    <span class="text-sm font-black ${stats.today_status === 'Present' ? 'text-emerald-600' : (stats.today_status === 'Absent' ? 'text-rose-600' : 'text-amber-600')}">
                      ${stats.today_status}
                    </span>
                  </div>
                  <div class="w-10 h-10 rounded-xl ${stats.today_status === 'Present' ? 'bg-emerald-50 text-emerald-600' : (stats.today_status === 'Absent' ? 'bg-rose-50 text-rose-600' : 'bg-amber-50 text-amber-600')} flex items-center justify-center font-bold">
                    <i data-lucide="${stats.today_status === 'Present' ? 'check' : (stats.today_status === 'Absent' ? 'x' : 'clock')}" class="w-5 h-5"></i>
                  </div>
                </div>
              </div>

              <!-- Stats & Summary Row -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 my-5">
                <div class="bg-slate-50 p-3.5 rounded-2xl">
                  <span class="text-[10px] font-bold text-slate-400 uppercase">Attendance Rate</span>
                  <div class="text-xl font-black ${isSafe ? 'text-emerald-600' : 'text-rose-600'} mt-1">${pct}%</div>
                  <span class="text-[10px] ${isSafe ? 'text-emerald-600' : 'text-rose-600'} font-semibold">${isSafe ? 'Safe Standing' : 'Needs Attention'}</span>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-2xl">
                  <span class="text-[10px] font-bold text-slate-400 uppercase">Working Days</span>
                  <div class="text-xl font-black text-slate-800 mt-1">${stats.total_working_days}</div>
                  <span class="text-[10px] text-slate-400">Total sessions</span>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-2xl">
                  <span class="text-[10px] font-bold text-slate-400 uppercase">Present</span>
                  <div class="text-xl font-black text-emerald-600 mt-1">${stats.present_days}</div>
                  <span class="text-[10px] text-emerald-600 font-semibold">Attended</span>
                </div>
                <div class="bg-slate-50 p-3.5 rounded-2xl">
                  <span class="text-[10px] font-bold text-slate-400 uppercase">Absent</span>
                  <div class="text-xl font-black text-rose-600 mt-1">${stats.absent_days}</div>
                  <span class="text-[10px] text-rose-500 font-semibold">Missed days</span>
                </div>
              </div>

              <!-- Recent Logs -->
              <div>
                <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Recent Attendance Timeline</h4>
                <div class="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  ${(chData.recent_history || []).slice(0, 5).map(r => `
                    <div class="p-2.5 rounded-xl border border-slate-100 bg-slate-50 text-center">
                      <span class="text-[10px] text-slate-500 font-bold block">${r.date}</span>
                      <span class="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-extrabold border ${getStatusBadgeClass(r.status)}">
                        ${r.status}
                      </span>
                    </div>
                  `).join('')}
                </div>
              </div>

            </div>
          `;
        }).join('')}
      </div>

    </div>
  `;
  initLucide();
}

function initMonthlyTrendChart(monthlyData) {
  const canvas = document.getElementById('monthlyTrendChart');
  if (!canvas) return;

  if (state.charts.trend) {
    state.charts.trend.destroy();
  }

  const labels = monthlyData.map(m => m.month);
  const percentages = monthlyData.map(m => m.percentage);
  const presentCounts = monthlyData.map(m => m.present);

  const ctx = canvas.getContext('2d');
  state.charts.trend = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Attendance Rate (%)',
          data: percentages,
          borderColor: '#059669',
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          borderWidth: 3,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: '#047857',
          pointRadius: 4,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `Attendance: ${item.raw}% (${presentCounts[item.dataIndex]} students)`
          }
        }
      },
      scales: {
        y: {
          min: 50,
          max: 100,
          ticks: {
            callback: (v) => `${v}%`,
            font: { size: 10 }
          },
          grid: { color: '#f1f5f9' }
        },
        x: {
          ticks: { font: { size: 10 } },
          grid: { display: false }
        }
      }
    }
  });
}

// =========================================================================
// 6. VIEW: MARK ATTENDANCE (CLASS -> SECTION -> DATE FLOW)
// =========================================================================

async function renderMarkAttendanceView(container) {
  const defaultClassId = state.classes.length > 0 ? state.classes[0].id : 1;
  const todayStr = new Date().toISOString().split('T')[0];

  container.innerHTML = `
    <div class="space-y-5 animate-fade-in">
      
      <!-- Header Banner -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div>
          <h2 class="text-xl font-black text-slate-900">Mark Classroom Attendance</h2>
          <p class="text-xs text-slate-500">Select Class & Date to record Present, Absent, or Late attendance.</p>
        </div>
        <div class="flex items-center space-x-2">
          <button onclick="syncOfflineAttendance()" class="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center space-x-1.5 transition">
            <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
            <span>Sync Offline Cache</span>
          </button>
        </div>
      </div>

      <!-- Filter Selection Bar: Class -> Section -> Date -->
      <div class="bg-white p-4 rounded-3xl border border-slate-100 shadow-sm grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3 items-end">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Select Class & Section *</label>
          <select id="att-class-select" onchange="loadAttendanceSheet()" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            ${state.classes.map(c => `
              <option value="${c.id}">${c.class_name} - Section ${c.section}</option>
            `).join('')}
          </select>
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Attendance Date *</label>
          <input type="date" id="att-date-input" value="${todayStr}" onchange="loadAttendanceSheet()" class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Search Student Name / Roll</label>
          <div class="relative">
            <input type="text" id="att-search-input" onkeyup="filterAttendanceTable()" placeholder="Quick filter..." class="w-full pl-8 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            <i data-lucide="search" class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-3"></i>
          </div>
        </div>

        <div>
          <button onclick="loadAttendanceSheet()" class="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-1.5 shadow-md shadow-emerald-600/20 transition">
            <i data-lucide="search" class="w-3.5 h-3.5"></i>
            <span>Load Students</span>
          </button>
        </div>
      </div>

      <!-- Bulk Actions & Live Attendance Summary Bar -->
      <div id="att-summary-bar" class="bg-emerald-900 text-white p-4 rounded-3xl shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div class="flex items-center space-x-4 flex-wrap gap-2">
          <span class="text-xs font-extrabold uppercase tracking-wider text-emerald-300">Live Counters:</span>
          <span id="counter-total" class="px-2.5 py-1 rounded-lg bg-white/10 text-xs font-bold">Total: 0</span>
          <span id="counter-present" class="px-2.5 py-1 rounded-lg bg-emerald-500 text-xs font-bold">Present: 0</span>
          <span id="counter-absent" class="px-2.5 py-1 rounded-lg bg-rose-500 text-xs font-bold">Absent: 0</span>
          <span id="counter-late" class="px-2.5 py-1 rounded-lg bg-amber-500 text-xs font-bold">Late: 0</span>
          <span id="counter-percentage" class="px-2.5 py-1 rounded-lg bg-white text-emerald-950 text-xs font-black">Score: 0%</span>
        </div>

        <div class="flex items-center space-x-2 flex-wrap gap-2">
          <button onclick="setAllAttendanceStatus('Present')" class="px-3 py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold border border-emerald-500 transition">
            ✓ Mark All Present
          </button>
          <button onclick="setAllAttendanceStatus('Absent')" class="px-3 py-1.5 rounded-xl bg-rose-700 hover:bg-rose-600 text-white text-xs font-bold border border-rose-500 transition">
            ✗ Mark All Absent
          </button>
          <button onclick="saveAttendanceBatch()" id="btn-save-attendance" class="px-5 py-2 rounded-xl bg-white hover:bg-emerald-50 text-emerald-900 text-xs font-black shadow-lg transition flex items-center space-x-1.5">
            <i data-lucide="save" class="w-4 h-4 text-emerald-600"></i>
            <span>Submit Attendance</span>
          </button>
        </div>
      </div>

      <!-- Student Attendance Roster Sheet -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
        <div id="attendance-sheet-container" class="p-4">
          <!-- Loaded dynamically -->
        </div>
      </div>

    </div>
  `;

  initLucide();
  loadAttendanceSheet();
}

function startMarkingForClass(classId) {
  navigateTo('mark-attendance');
  setTimeout(() => {
    const sel = document.getElementById('att-class-select');
    if (sel) {
      sel.value = classId;
      loadAttendanceSheet();
    }
  }, 100);
}

async function loadAttendanceSheet() {
  const classSelect = document.getElementById('att-class-select');
  const dateInput = document.getElementById('att-date-input');
  const container = document.getElementById('attendance-sheet-container');
  if (!classSelect || !dateInput || !container) return;

  const classId = classSelect.value;
  const dateStr = dateInput.value;

  container.innerHTML = `<div class="p-8 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-6 w-6 border-3 border-emerald-600 border-t-transparent"></div><p class="mt-2 text-xs font-semibold">Loading student roster...</p></div>`;

  const data = await apiFetch(`/api/attendance/sheet?class_id=${classId}&date=${dateStr}`);
  if (!data || !data.success) {
    container.innerHTML = `<div class="p-6 text-center text-rose-500">Failed to load student roster.</div>`;
    return;
  }

  state.attendanceSheet.classId = classId;
  state.attendanceSheet.date = dateStr;
  state.attendanceSheet.students = data.students || [];
  state.attendanceSheet.recordsMap = {};

  // Populate recordsMap
  data.students.forEach(s => {
    state.attendanceSheet.recordsMap[s.student_id] = {
      status: s.status || 'Present', // Default to Present for quick workflow
      remarks: s.remarks || ''
    };
  });

  renderAttendanceTable();
}

function renderAttendanceTable() {
  const container = document.getElementById('attendance-sheet-container');
  if (!container) return;

  const students = state.attendanceSheet.students;

  if (students.length === 0) {
    container.innerHTML = `<div class="p-8 text-center text-slate-400">No active students found enrolled in this class.</div>`;
    updateAttendanceCounters();
    return;
  }

  container.innerHTML = `
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs" id="att-students-table">
        <thead>
          <tr class="bg-slate-50 text-slate-500 uppercase tracking-wider font-bold border-b border-slate-100">
            <th class="py-3 px-4 w-16">Roll</th>
            <th class="py-3 px-4">Student Name</th>
            <th class="py-3 px-4">Gender</th>
            <th class="py-3 px-4 text-center">Attendance Status</th>
            <th class="py-3 px-4">Remarks / Excuse</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${students.map(s => {
            const sid = s.student_id;
            const currentRec = state.attendanceSheet.recordsMap[sid] || { status: 'Present', remarks: '' };
            const status = currentRec.status;

            return `
              <tr class="att-row hover:bg-slate-50/75 transition" data-name="${s.name.toLowerCase()}" data-roll="${s.roll_number}">
                <td class="py-3 px-4 font-black text-slate-900">${s.roll_number}</td>
                <td class="py-3 px-4">
                  <span class="font-bold text-slate-900 block">${s.name}</span>
                  <span class="text-[10px] text-slate-400">ID: ${s.student_code || 'STD-0' + s.student_id}</span>
                </td>
                <td class="py-3 px-4 text-slate-500">${s.gender}</td>
                <td class="py-3 px-4">
                  <div class="flex items-center justify-center space-x-1.5">
                    <button type="button" onclick="setStudentStatus(${sid}, 'Present')" class="btn-present px-3 py-1.5 rounded-xl border text-xs font-bold transition ${status === 'Present' ? 'active' : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-emerald-500'}">
                      ✓ Present
                    </button>
                    <button type="button" onclick="setStudentStatus(${sid}, 'Absent')" class="btn-absent px-3 py-1.5 rounded-xl border text-xs font-bold transition ${status === 'Absent' ? 'active' : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-rose-500'}">
                      ✗ Absent
                    </button>
                    <button type="button" onclick="setStudentStatus(${sid}, 'Late')" class="btn-late px-3 py-1.5 rounded-xl border text-xs font-bold transition ${status === 'Late' ? 'active' : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-amber-500'}">
                      ◷ Late
                    </button>
                  </div>
                </td>
                <td class="py-3 px-4">
                  <input type="text" value="${currentRec.remarks}" onchange="setStudentRemarks(${sid}, this.value)" placeholder="e.g. Fever, Bus delay..." class="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;

  updateAttendanceCounters();
  initLucide();
}

function setStudentStatus(studentId, status) {
  if (!state.attendanceSheet.recordsMap[studentId]) {
    state.attendanceSheet.recordsMap[studentId] = { status: 'Present', remarks: '' };
  }
  state.attendanceSheet.recordsMap[studentId].status = status;
  renderAttendanceTable();
}

function setStudentRemarks(studentId, remarks) {
  if (!state.attendanceSheet.recordsMap[studentId]) {
    state.attendanceSheet.recordsMap[studentId] = { status: 'Present', remarks: '' };
  }
  state.attendanceSheet.recordsMap[studentId].remarks = remarks;
}

function setAllAttendanceStatus(status) {
  state.attendanceSheet.students.forEach(s => {
    if (!state.attendanceSheet.recordsMap[s.student_id]) {
      state.attendanceSheet.recordsMap[s.student_id] = { status: 'Present', remarks: '' };
    }
    state.attendanceSheet.recordsMap[s.student_id].status = status;
  });
  renderAttendanceTable();
  showToast(`All students marked as ${status}.`, 'info');
}

function filterAttendanceTable() {
  const query = (document.getElementById('att-search-input').value || '').toLowerCase().trim();
  const rows = document.querySelectorAll('.att-row');
  rows.forEach(r => {
    const name = r.getAttribute('data-name') || '';
    const roll = r.getAttribute('data-roll') || '';
    if (!query || name.includes(query) || roll.includes(query)) {
      r.style.display = '';
    } else {
      r.style.display = 'none';
    }
  });
}

function updateAttendanceCounters() {
  const students = state.attendanceSheet.students;
  const total = students.length;
  let present = 0, absent = 0, late = 0;

  students.forEach(s => {
    const rec = state.attendanceSheet.recordsMap[s.student_id];
    if (rec) {
      if (rec.status === 'Present') present++;
      else if (rec.status === 'Absent') absent++;
      else if (rec.status === 'Late') late++;
    }
  });

  const pct = total > 0 ? Math.round((present / total) * 100) : 0;

  const cTot = document.getElementById('counter-total');
  const cPre = document.getElementById('counter-present');
  const cAbs = document.getElementById('counter-absent');
  const cLat = document.getElementById('counter-late');
  const cPct = document.getElementById('counter-percentage');

  if (cTot) cTot.textContent = `Total: ${total}`;
  if (cPre) cPre.textContent = `Present: ${present}`;
  if (cAbs) cAbs.textContent = `Absent: ${absent}`;
  if (cLat) cLat.textContent = `Late: ${late}`;
  if (cPct) cPct.textContent = `Rate: ${pct}%`;
}

async function saveAttendanceBatch(override = false) {
  const classId = state.attendanceSheet.classId;
  const dateStr = state.attendanceSheet.date;
  const records = state.attendanceSheet.students.map(s => ({
    student_id: s.student_id,
    status: state.attendanceSheet.recordsMap[s.student_id]?.status || 'Present',
    remarks: state.attendanceSheet.recordsMap[s.student_id]?.remarks || ''
  }));

  if (!classId || records.length === 0) {
    showToast('No student records to save.', 'warning');
    return;
  }

  const btn = document.getElementById('btn-save-attendance');
  const origText = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="inline-block animate-spin rounded-full h-3.5 w-3.5 border-2 border-emerald-800 border-t-transparent mr-1.5"></span> Saving...`;
  }

  // Handle Offline Cache if no network
  if (!state.isOnline) {
    const offlinePayload = { class_id: classId, date: dateStr, records: records, timestamp: new Date().toISOString() };
    state.offlineQueue.push(offlinePayload);
    localStorage.setItem('rural_attendance_offline_queue', JSON.stringify(state.offlineQueue));
    updateConnectionUI();
    showToast('Offline Mode: Attendance saved locally in device storage. It will sync automatically when back online.', 'success');
    if (btn) { btn.disabled = false; btn.innerHTML = origText; }
    return;
  }

  try {
    const res = await apiFetch('/api/attendance/batch', {
      method: 'POST',
      body: JSON.stringify({
        class_id: classId,
        date: dateStr,
        records: records,
        override: override
      })
    });

    if (res && res.success) {
      showToast(res.message || 'Attendance saved successfully!', 'success');
      loadAttendanceSheet();
    } else if (res && res.is_duplicate) {
      if (confirm(`${res.message}\n\nDo you want to OVERWRITE and update today's attendance?`)) {
        saveAttendanceBatch(true);
      }
    } else {
      showToast(res?.message || 'Failed to save attendance.', 'error');
    }
  } catch (e) {
    showToast('Network error while saving attendance.', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origText;
      initLucide();
    }
  }
}

async function syncOfflineAttendance() {
  if (state.offlineQueue.length === 0) {
    showToast('No pending offline attendance records to sync.', 'info');
    return;
  }
  if (!state.isOnline) {
    showToast('Cannot sync while offline. Please connect to Wi-Fi/cellular network.', 'warning');
    return;
  }

  let syncedCount = 0;
  const queue = [...state.offlineQueue];
  for (const item of queue) {
    try {
      const res = await apiFetch('/api/attendance/batch', {
        method: 'POST',
        body: JSON.stringify({ ...item, override: true })
      });
      if (res && res.success) syncedCount++;
    } catch (e) {
      console.error('Failed to sync item', item, e);
    }
  }

  state.offlineQueue = [];
  localStorage.removeItem('rural_attendance_offline_queue');
  updateConnectionUI();
  showToast(`Successfully synchronized ${syncedCount} attendance batches to school server!`, 'success');
}

// =========================================================================
// 7. VIEW: ATTENDANCE HISTORY & REGISTER
// =========================================================================

async function renderAttendanceHistoryView(container) {
  const todayStr = new Date().toISOString().split('T')[0];
  const lastMonthStr = new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0];

  container.innerHTML = `
    <div class="space-y-5 animate-fade-in">
      
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div>
          <h2 class="text-xl font-black text-slate-900">Attendance History & Search</h2>
          <p class="text-xs text-slate-500">Filter, inspect, and export historical attendance records.</p>
        </div>
        <div class="flex items-center space-x-2">
          <a id="history-export-btn" href="/api/export/attendance/csv" class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 flex items-center space-x-1.5 transition">
            <i data-lucide="download" class="w-3.5 h-3.5"></i>
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      <!-- Filters Bar -->
      <div class="bg-white p-4 rounded-3xl border border-slate-100 shadow-sm grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Class</label>
          <select id="hist-class" onchange="loadAttendanceHistory(1)" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            <option value="">All Classes</option>
            ${state.classes.map(c => `<option value="${c.id}">${c.class_name} - ${c.section}</option>`).join('')}
          </select>
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">From Date</label>
          <input type="date" id="hist-start-date" value="${lastMonthStr}" onchange="loadAttendanceHistory(1)" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">To Date</label>
          <input type="date" id="hist-end-date" value="${todayStr}" onchange="loadAttendanceHistory(1)" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Status</label>
          <select id="hist-status" onchange="loadAttendanceHistory(1)" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            <option value="">All Statuses</option>
            <option value="Present">Present Only</option>
            <option value="Absent">Absent Only</option>
            <option value="Late">Late Only</option>
          </select>
        </div>

        <div class="flex items-end">
          <button onclick="loadAttendanceHistory(1)" class="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-1.5 transition">
            <i data-lucide="filter" class="w-3.5 h-3.5"></i>
            <span>Apply Filters</span>
          </button>
        </div>
      </div>

      <!-- History Table Container -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
        <div id="history-table-container" class="p-4">
          <!-- Loaded dynamically -->
        </div>
      </div>

    </div>
  `;

  initLucide();
  loadAttendanceHistory(1);
}

async function loadAttendanceHistory(page = 1) {
  const container = document.getElementById('history-table-container');
  if (!container) return;

  const classId = document.getElementById('hist-class')?.value || '';
  const startDate = document.getElementById('hist-start-date')?.value || '';
  const endDate = document.getElementById('hist-end-date')?.value || '';
  const status = document.getElementById('hist-status')?.value || '';

  // Update export button link
  const exportBtn = document.getElementById('history-export-btn');
  if (exportBtn) {
    exportBtn.href = `/api/export/attendance/csv?class_id=${classId}&start_date=${startDate}&end_date=${endDate}`;
  }

  container.innerHTML = `<div class="p-8 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-6 w-6 border-3 border-emerald-600 border-t-transparent"></div><p class="mt-2 text-xs font-semibold">Searching history...</p></div>`;

  const data = await apiFetch(`/api/attendance/history?class_id=${classId}&start_date=${startDate}&end_date=${endDate}&status=${status}&page=${page}&limit=25`);
  if (!data || !data.success) {
    container.innerHTML = `<div class="p-6 text-center text-rose-500">Failed to fetch attendance history.</div>`;
    return;
  }

  const records = data.records || [];
  const total = data.total || 0;
  const totalPages = Math.ceil(total / 25) || 1;

  if (records.length === 0) {
    container.innerHTML = `<div class="p-8 text-center text-slate-400">No attendance records found matching the criteria.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead>
          <tr class="bg-slate-50 text-slate-500 uppercase tracking-wider font-bold border-b border-slate-100">
            <th class="py-3 px-4">Date</th>
            <th class="py-3 px-4">Time</th>
            <th class="py-3 px-4">Student Name</th>
            <th class="py-3 px-4">Roll</th>
            <th class="py-3 px-4">Class</th>
            <th class="py-3 px-4">Status</th>
            <th class="py-3 px-4">Remarks</th>
            <th class="py-3 px-4">Marked By</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${records.map(r => `
            <tr class="hover:bg-slate-50/75 transition">
              <td class="py-3 px-4 font-bold text-slate-800">${r.date}</td>
              <td class="py-3 px-4 text-slate-400 font-mono text-[11px]">${r.time || '—'}</td>
              <td class="py-3 px-4 font-bold text-slate-900">${r.student_name}</td>
              <td class="py-3 px-4 text-slate-600">${r.roll_number}</td>
              <td class="py-3 px-4 text-slate-600 font-medium">${r.class_name} - ${r.section}</td>
              <td class="py-3 px-4">
                <span class="px-2.5 py-1 rounded-full text-[10px] font-bold border ${getStatusBadgeClass(r.status)}">
                  ${r.status}
                </span>
              </td>
              <td class="py-3 px-4 text-slate-500">${r.remarks || '—'}</td>
              <td class="py-3 px-4 text-slate-400 text-[11px]">${r.marked_by_name || 'Teacher'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between pt-4 border-t border-slate-100 text-xs text-slate-500">
      <span>Showing ${records.length} of ${total} records</span>
      <div class="flex items-center space-x-1.5">
        <button onclick="loadAttendanceHistory(${page - 1})" ${page <= 1 ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed">Previous</button>
        <span class="px-2 font-bold text-slate-800">Page ${page} of ${totalPages}</span>
        <button onclick="loadAttendanceHistory(${page + 1})" ${page >= totalPages ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed">Next</button>
      </div>
    </div>
  `;

  initLucide();
}

// =========================================================================
// 8. VIEW: REPORTS & MONTHLY REGISTERS
// =========================================================================

async function renderReportsView(container) {
  const currentMonth = new Date().toISOString().substring(0, 7); // YYYY-MM

  container.innerHTML = `
    <div class="space-y-6 animate-fade-in">
      
      <!-- Top Title -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div>
          <h2 class="text-xl font-black text-slate-900">Attendance Reports & Registers</h2>
          <p class="text-xs text-slate-500">Government compliant monthly class matrix, individual student reports, and low-attendance warnings.</p>
        </div>
        <div class="flex items-center space-x-2">
          <button onclick="window.print()" class="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold shadow flex items-center space-x-1.5 transition">
            <i data-lucide="printer" class="w-3.5 h-3.5"></i>
            <span>Print Report</span>
          </button>
        </div>
      </div>

      <!-- Report Tabs Selector -->
      <div class="flex items-center space-x-2 border-b border-slate-200 pb-1">
        <button onclick="switchReportTab('matrix')" id="tab-report-matrix" class="px-4 py-2 text-xs font-bold rounded-xl bg-emerald-600 text-white shadow transition">
          Monthly Class Register Matrix
        </button>
        <button onclick="switchReportTab('student')" id="tab-report-student" class="px-4 py-2 text-xs font-bold rounded-xl text-slate-600 hover:bg-slate-100 transition">
          Individual Student Drilldown
        </button>
        <button onclick="switchReportTab('low-attendance')" id="tab-report-low-attendance" class="px-4 py-2 text-xs font-bold rounded-xl text-slate-600 hover:bg-slate-100 transition">
          Low Attendance Alert List (&lt;75%)
        </button>
      </div>

      <!-- Tab Content Area -->
      <div id="report-tab-content">
        <!-- Rendered by tab switch -->
      </div>

    </div>
  `;

  initLucide();
  switchReportTab('matrix');
}

function switchReportTab(tabId) {
  document.querySelectorAll('[id^="tab-report-"]').forEach(btn => {
    btn.className = 'px-4 py-2 text-xs font-bold rounded-xl text-slate-600 hover:bg-slate-100 transition';
  });
  const activeBtn = document.getElementById(`tab-report-${tabId}`);
  if (activeBtn) {
    activeBtn.className = 'px-4 py-2 text-xs font-bold rounded-xl bg-emerald-600 text-white shadow transition';
  }

  const content = document.getElementById('report-tab-content');
  if (!content) return;

  if (tabId === 'matrix') {
    renderMatrixReportTab(content);
  } else if (tabId === 'student') {
    renderStudentReportTab(content);
  } else if (tabId === 'low-attendance') {
    renderLowAttendanceReportTab(content);
  }
}

async function renderMatrixReportTab(container) {
  const currentMonth = new Date().toISOString().substring(0, 7);

  container.innerHTML = `
    <div class="space-y-4">
      <!-- Selector bar -->
      <div class="bg-white p-4 rounded-3xl border border-slate-100 shadow-sm grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Select Class *</label>
          <select id="matrix-class-select" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            ${state.classes.map(c => `<option value="${c.id}">${c.class_name} - Section ${c.section}</option>`).join('')}
          </select>
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Select Month *</label>
          <input type="month" id="matrix-month-input" value="${currentMonth}" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
        </div>
        <div>
          <button onclick="loadMonthlyMatrix()" class="w-full py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-1.5 transition">
            <i data-lucide="file-spreadsheet" class="w-3.5 h-3.5"></i>
            <span>Generate Register Matrix</span>
          </button>
        </div>
      </div>

      <!-- Matrix Container -->
      <div id="matrix-table-container" class="bg-white p-4 rounded-3xl border border-slate-100 shadow-sm overflow-x-auto">
        <div class="p-8 text-center text-slate-400">Click "Generate Register Matrix" to view monthly student grid.</div>
      </div>
    </div>
  `;

  initLucide();
  loadMonthlyMatrix();
}

async function loadMonthlyMatrix() {
  const classId = document.getElementById('matrix-class-select')?.value;
  const month = document.getElementById('matrix-month-input')?.value;
  const container = document.getElementById('matrix-table-container');
  if (!classId || !month || !container) return;

  container.innerHTML = `<div class="p-8 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-6 w-6 border-3 border-emerald-600 border-t-transparent"></div><p class="mt-2 text-xs font-semibold">Generating monthly register grid...</p></div>`;

  const data = await apiFetch(`/api/reports/matrix/${classId}?month=${month}`);
  if (!data || !data.success) {
    container.innerHTML = `<div class="p-6 text-center text-rose-500">Failed to generate monthly register.</div>`;
    return;
  }

  const cls = data.class;
  const matrix = data.matrix || [];
  const daysList = data.days || [];

  container.innerHTML = `
    <div>
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 mb-3 gap-2">
        <div>
          <h3 class="text-sm font-black text-slate-900">${cls.class_name} - Section ${cls.section} Monthly Attendance Register</h3>
          <p class="text-xs text-slate-500">Month: ${month} • Class Teacher: ${cls.teacher_name || 'Sunita Devi'}</p>
        </div>
        <div class="flex items-center space-x-3 text-xs font-bold">
          <span class="flex items-center space-x-1"><span class="w-3 h-3 bg-emerald-200 rounded"></span><span>P = Present</span></span>
          <span class="flex items-center space-x-1"><span class="w-3 h-3 bg-rose-200 rounded"></span><span>A = Absent</span></span>
          <span class="flex items-center space-x-1"><span class="w-3 h-3 bg-amber-200 rounded"></span><span>L = Late</span></span>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="matrix-table w-full text-xs">
          <thead>
            <tr class="bg-slate-100 text-slate-700 font-bold">
              <th class="w-8">Roll</th>
              <th class="text-left w-36 pl-2">Student Name</th>
              ${daysList.map((d, i) => `<th class="w-6" title="${d}">${i + 1}</th>`).join('')}
              <th class="w-8 bg-emerald-100 text-emerald-800">P</th>
              <th class="w-8 bg-rose-100 text-rose-800">A</th>
              <th class="w-8 bg-amber-100 text-amber-800">L</th>
              <th class="w-12 bg-slate-200 text-slate-800">%</th>
            </tr>
          </thead>
          <tbody>
            ${matrix.map(row => {
              return `
                <tr>
                  <td class="font-bold text-slate-700">${row.roll_number}</td>
                  <td class="text-left font-bold text-slate-900 pl-2 whitespace-nowrap">${row.name}</td>
                  ${daysList.map(d => {
                    const status = row.days[d] || '—';
                    let cellClass = '';
                    if (status === 'Present') cellClass = 'matrix-cell-P';
                    else if (status === 'Absent') cellClass = 'matrix-cell-A';
                    else if (status === 'Late') cellClass = 'matrix-cell-L';

                    const shortStatus = status === 'Present' ? 'P' : (status === 'Absent' ? 'A' : (status === 'Late' ? 'L' : '·'));
                    return `<td class="${cellClass}">${shortStatus}</td>`;
                  }).join('')}
                  <td class="font-bold text-emerald-700 bg-emerald-50">${row.present_count}</td>
                  <td class="font-bold text-rose-700 bg-rose-50">${row.absent_count}</td>
                  <td class="font-bold text-amber-700 bg-amber-50">${row.late_count}</td>
                  <td class="font-black ${row.percentage < 75 ? 'text-rose-600 bg-rose-50' : 'text-emerald-700 bg-emerald-50'}">${row.percentage}%</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderStudentReportTab(container) {
  // Load students for selector
  const studentsRes = await apiFetch('/api/students');
  const students = studentsRes?.students || [];

  container.innerHTML = `
    <div class="space-y-4">
      <div class="bg-white p-4 rounded-3xl border border-slate-100 shadow-sm grid grid-cols-1 sm:grid-cols-2 gap-3 items-end">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Select Student *</label>
          <select id="student-report-select" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            ${students.map(s => `<option value="${s.id}">${s.name} (${s.class_name}-${s.section}, Roll: ${s.roll_number})</option>`).join('')}
          </select>
        </div>
        <div>
          <button onclick="loadIndividualStudentReport()" class="w-full py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-1.5 transition">
            <i data-lucide="user-check" class="w-3.5 h-3.5"></i>
            <span>Load Comprehensive Report</span>
          </button>
        </div>
      </div>

      <div id="student-report-container">
        <!-- Rendered dynamically -->
      </div>
    </div>
  `;

  initLucide();
  loadIndividualStudentReport();
}

async function loadIndividualStudentReport() {
  const studentId = document.getElementById('student-report-select')?.value;
  const container = document.getElementById('student-report-container');
  if (!studentId || !container) return;

  container.innerHTML = `<div class="p-8 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-6 w-6 border-3 border-emerald-600 border-t-transparent"></div><p class="mt-2 text-xs font-semibold">Loading student record...</p></div>`;

  const data = await apiFetch(`/api/reports/student/${studentId}`);
  if (!data || !data.success) {
    container.innerHTML = `<div class="p-6 text-center text-rose-500">Failed to load student report.</div>`;
    return;
  }

  const s = data.student;
  const sum = data.summary;

  container.innerHTML = `
    <div class="space-y-4">
      <div class="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h3 class="text-xl font-black text-slate-900">${s.name}</h3>
          <p class="text-xs text-slate-500">${s.class_name} • Section ${s.section} • Roll No: ${s.roll_number} • Parent: ${s.parent_name || 'N/A'} (${s.parent_phone || 'N/A'})</p>
        </div>
        <div class="flex items-center space-x-3">
          <div class="px-4 py-2 rounded-2xl ${sum.is_low_attendance ? 'bg-rose-50 border border-rose-200 text-rose-700' : 'bg-emerald-50 border border-emerald-200 text-emerald-700'} text-center">
            <span class="text-[10px] font-bold uppercase block">Attendance Rate</span>
            <span class="text-xl font-black">${sum.percentage}%</span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="bg-white p-4 rounded-2xl border border-slate-100 text-center">
          <span class="text-[10px] font-bold text-slate-400 uppercase">Working Days</span>
          <div class="text-xl font-black text-slate-800 mt-1">${sum.total_working_days}</div>
        </div>
        <div class="bg-white p-4 rounded-2xl border border-slate-100 text-center">
          <span class="text-[10px] font-bold text-slate-400 uppercase">Present</span>
          <div class="text-xl font-black text-emerald-600 mt-1">${sum.present_days}</div>
        </div>
        <div class="bg-white p-4 rounded-2xl border border-slate-100 text-center">
          <span class="text-[10px] font-bold text-slate-400 uppercase">Absent</span>
          <div class="text-xl font-black text-rose-600 mt-1">${sum.absent_days}</div>
        </div>
        <div class="bg-white p-4 rounded-2xl border border-slate-100 text-center">
          <span class="text-[10px] font-bold text-slate-400 uppercase">Late</span>
          <div class="text-xl font-black text-amber-600 mt-1">${sum.late_days}</div>
        </div>
      </div>

      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-5">
        <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Attendance History Log</h4>
        <div class="overflow-x-auto max-h-72">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="bg-slate-50 text-slate-500 font-bold border-b border-slate-100">
                <th class="py-2 px-3">Date</th>
                <th class="py-2 px-3">Time</th>
                <th class="py-2 px-3">Status</th>
                <th class="py-2 px-3">Remarks</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${(data.records || []).map(r => `
                <tr>
                  <td class="py-2 px-3 font-bold text-slate-800">${r.date}</td>
                  <td class="py-2 px-3 text-slate-400">${r.time || '08:30:00'}</td>
                  <td class="py-2 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold border ${getStatusBadgeClass(r.status)}">${r.status}</span></td>
                  <td class="py-2 px-3 text-slate-500">${r.remarks || 'Regular'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

async function renderLowAttendanceReportTab(container) {
  container.innerHTML = `<div class="p-8 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-6 w-6 border-3 border-emerald-600 border-t-transparent"></div><p class="mt-2 text-xs font-semibold">Scanning low attendance database...</p></div>`;

  const data = await apiFetch('/api/dashboard/stats');
  const lowStudents = data?.low_attendance_students || [];

  container.innerHTML = `
    <div class="space-y-4">
      <div class="bg-rose-50 border border-rose-200 rounded-3xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h3 class="text-base font-black text-rose-900 flex items-center space-x-2">
            <i data-lucide="alert-octagon" class="w-5 h-5 text-rose-600"></i>
            <span>Rural Education Retention Alert System</span>
          </h3>
          <p class="text-xs text-rose-700 mt-0.5">
            Students whose attendance is currently below the mandatory 75% threshold. Proactive outreach recommended.
          </p>
        </div>
        <div class="flex items-center space-x-2">
          <a href="/api/export/low-attendance/csv" class="px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow flex items-center space-x-1.5 transition">
            <i data-lucide="download" class="w-3.5 h-3.5"></i>
            <span>Export Alert CSV</span>
          </a>
        </div>
      </div>

      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden p-4">
        ${lowStudents.length === 0 ? `
          <div class="p-8 text-center text-emerald-600 font-bold text-xs">
            ✓ Excellent! No students currently below the 75% attendance threshold.
          </div>
        ` : `
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead>
                <tr class="bg-slate-50 text-slate-500 font-bold border-b border-slate-100 uppercase">
                  <th class="py-3 px-4">Student Name</th>
                  <th class="py-3 px-4">Class</th>
                  <th class="py-3 px-4">Working Days</th>
                  <th class="py-3 px-4">Present Days</th>
                  <th class="py-3 px-4">Attendance %</th>
                  <th class="py-3 px-4">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                ${lowStudents.map(s => {
                  const pct = s.total_days > 0 ? ((s.present_days / s.total_days) * 100).toFixed(1) : 0;
                  return `
                    <tr class="hover:bg-rose-50/50 transition">
                      <td class="py-3 px-4 font-bold text-slate-900">${s.name}</td>
                      <td class="py-3 px-4 text-slate-600 font-medium">${s.class_name} - ${s.section}</td>
                      <td class="py-3 px-4 text-slate-600">${s.total_days}</td>
                      <td class="py-3 px-4 text-slate-600">${s.present_days}</td>
                      <td class="py-3 px-4 font-black text-rose-600">${pct}%</td>
                      <td class="py-3 px-4">
                        <button onclick="triggerParentSMSAlert('${s.name}')" class="px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-bold hover:bg-amber-100 transition flex items-center space-x-1">
                          <i data-lucide="message-square" class="w-3 h-3"></i>
                          <span>Send Parent SMS</span>
                        </button>
                      </td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        `}
      </div>
    </div>
  `;

  initLucide();
}

function triggerParentSMSAlert(studentName) {
  showToast(`SMS Alert sent to parent of ${studentName}: "Important: Low attendance notice for your child at Green Valley Rural School."`, 'success');
}

// =========================================================================
// 9. VIEW: STUDENT MANAGEMENT (CRUD)
// =========================================================================

async function renderStudentsView(container) {
  container.innerHTML = `
    <div class="space-y-5 animate-fade-in">
      
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div>
          <h2 class="text-xl font-black text-slate-900">Student Management</h2>
          <p class="text-xs text-slate-500">Manage student enrollment, roll numbers, and parent contacts.</p>
        </div>
        <div class="flex items-center space-x-2">
          <button onclick="openStudentModal()" class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 flex items-center space-x-1.5 transition">
            <i data-lucide="user-plus" class="w-3.5 h-3.5"></i>
            <span>Add Student</span>
          </button>
          <a href="/api/students/export" class="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold flex items-center space-x-1.5 transition">
            <i data-lucide="download" class="w-3.5 h-3.5"></i>
            <span>Roster CSV</span>
          </a>
        </div>
      </div>

      <!-- Search & Filters -->
      <div class="bg-white p-4 rounded-3xl border border-slate-100 shadow-sm grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Search Name / ID / Roll</label>
          <input type="text" id="stu-search" onkeyup="loadStudentsList()" placeholder="Type to search..." class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Filter by Class</label>
          <select id="stu-class-filter" onchange="loadStudentsList()" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            <option value="">All Classes</option>
            ${state.classes.map(c => `<option value="${c.id}">${c.class_name} - Section ${c.section}</option>`).join('')}
          </select>
        </div>
        <div class="flex items-end">
          <button onclick="loadStudentsList()" class="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-1.5 transition">
            <i data-lucide="search" class="w-3.5 h-3.5"></i>
            <span>Filter Roster</span>
          </button>
        </div>
      </div>

      <!-- Students Table -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
        <div id="students-table-container" class="p-4">
          <!-- Loaded dynamically -->
        </div>
      </div>

    </div>
  `;

  initLucide();
  loadStudentsList();
}

async function loadStudentsList() {
  const container = document.getElementById('students-table-container');
  if (!container) return;

  const search = document.getElementById('stu-search')?.value || '';
  const classId = document.getElementById('stu-class-filter')?.value || '';

  container.innerHTML = `<div class="p-8 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-6 w-6 border-3 border-emerald-600 border-t-transparent"></div><p class="mt-2 text-xs font-semibold">Loading student roster...</p></div>`;

  const data = await apiFetch(`/api/students?search=${encodeURIComponent(search)}&class_id=${classId}`);
  if (!data || !data.success) {
    container.innerHTML = `<div class="p-6 text-center text-rose-500">Failed to load students.</div>`;
    return;
  }

  const students = data.students || [];

  if (students.length === 0) {
    container.innerHTML = `<div class="p-8 text-center text-slate-400">No students found matching query.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead>
          <tr class="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-100">
            <th class="py-3 px-4">Student ID</th>
            <th class="py-3 px-4">Full Name</th>
            <th class="py-3 px-4">Class</th>
            <th class="py-3 px-4">Roll No</th>
            <th class="py-3 px-4">Gender</th>
            <th class="py-3 px-4">Parent / Guardian</th>
            <th class="py-3 px-4">Phone</th>
            <th class="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${students.map(s => `
            <tr class="hover:bg-slate-50/75 transition">
              <td class="py-3 px-4 font-mono font-bold text-emerald-800">${s.student_id}</td>
              <td class="py-3 px-4 font-black text-slate-900">${s.name}</td>
              <td class="py-3 px-4 text-slate-600 font-medium">${s.class_name} - ${s.section}</td>
              <td class="py-3 px-4 font-bold text-slate-800">${s.roll_number}</td>
              <td class="py-3 px-4 text-slate-500">${s.gender}</td>
              <td class="py-3 px-4 text-slate-700 font-medium">${s.parent_name || '—'}</td>
              <td class="py-3 px-4 text-slate-500 font-mono text-[11px]">${s.parent_phone || s.phone || '—'}</td>
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end space-x-1.5">
                  <button onclick="openEditStudentModal(${JSON.stringify(s).replace(/"/g, '&quot;')})" class="p-1.5 rounded-lg text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition" title="Edit Student">
                    <i data-lucide="edit" class="w-4 h-4"></i>
                  </button>
                  <button onclick="deleteStudent(${s.id}, '${s.name}')" class="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition" title="Delete Student">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                  </button>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;

  initLucide();
}

function openStudentModal() {
  document.getElementById('student-form-id').value = '';
  document.getElementById('modal-student-title').textContent = 'Add New Student';
  document.getElementById('student-form').reset();
  populateModalDropdowns();
  document.getElementById('modal-student').classList.remove('hidden');
  initLucide();
}

function openEditStudentModal(s) {
  document.getElementById('student-form-id').value = s.id;
  document.getElementById('modal-student-title').textContent = `Edit Student: ${s.name}`;
  document.getElementById('student-name').value = s.name;
  document.getElementById('student-gender').value = s.gender;
  document.getElementById('student-dob').value = s.date_of_birth;
  document.getElementById('student-class-id').value = s.class_id;
  document.getElementById('student-section').value = s.section;
  document.getElementById('student-roll').value = s.roll_number;
  document.getElementById('student-parent-name').value = s.parent_name || '';
  document.getElementById('student-parent-phone').value = s.parent_phone || s.phone || '';
  document.getElementById('student-address').value = s.address || '';
  document.getElementById('modal-student').classList.remove('hidden');
  initLucide();
}

function closeStudentModal() {
  document.getElementById('modal-student').classList.add('hidden');
}

async function saveStudentForm() {
  const id = document.getElementById('student-form-id').value;
  const payload = {
    name: document.getElementById('student-name').value.trim(),
    gender: document.getElementById('student-gender').value,
    date_of_birth: document.getElementById('student-dob').value,
    class_id: document.getElementById('student-class-id').value,
    section: document.getElementById('student-section').value.trim(),
    roll_number: document.getElementById('student-roll').value.trim(),
    parent_name: document.getElementById('student-parent-name').value.trim(),
    parent_phone: document.getElementById('student-parent-phone').value.trim(),
    address: document.getElementById('student-address').value.trim(),
  };

  const endpoint = id ? `/api/students/${id}` : '/api/students';
  const method = id ? 'PUT' : 'POST';

  const res = await apiFetch(endpoint, {
    method: method,
    body: JSON.stringify(payload)
  });

  if (res && res.success) {
    showToast(res.message || 'Student saved successfully.', 'success');
    closeStudentModal();
    loadStudentsList();
  } else {
    showToast(res?.message || 'Error saving student.', 'error');
  }
}

async function deleteStudent(id, name) {
  if (!confirm(`Are you sure you want to delete student "${name}"? This action cannot be undone.`)) return;

  const res = await apiFetch(`/api/students/${id}`, { method: 'DELETE' });
  if (res && res.success) {
    showToast(`Student "${name}" deleted.`, 'success');
    loadStudentsList();
  } else {
    showToast(res?.message || 'Failed to delete student.', 'error');
  }
}

// =========================================================================
// 10. VIEW: TEACHER MANAGEMENT (CRUD)
// =========================================================================

async function renderTeachersView(container) {
  container.innerHTML = `
    <div class="space-y-5 animate-fade-in">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div>
          <h2 class="text-xl font-black text-slate-900">Teacher Management</h2>
          <p class="text-xs text-slate-500">Manage teaching staff, assigned subjects, and qualifications.</p>
        </div>
        <button onclick="openTeacherModal()" class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 flex items-center space-x-1.5 transition">
          <i data-lucide="user-plus" class="w-3.5 h-3.5"></i>
          <span>Add Teacher</span>
        </button>
      </div>

      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden p-4">
        <div id="teachers-table-container">
          <!-- Loaded dynamically -->
        </div>
      </div>
    </div>
  `;

  initLucide();
  loadTeachersList();
}

async function loadTeachersList() {
  const container = document.getElementById('teachers-table-container');
  if (!container) return;

  container.innerHTML = `<div class="p-8 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-6 w-6 border-3 border-emerald-600 border-t-transparent"></div><p class="mt-2 text-xs font-semibold">Loading teaching faculty...</p></div>`;

  const data = await apiFetch('/api/teachers');
  if (!data || !data.success) {
    container.innerHTML = `<div class="p-6 text-center text-rose-500">Failed to load teachers.</div>`;
    return;
  }

  const teachers = data.teachers || [];
  state.teachers = teachers;

  container.innerHTML = `
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead>
          <tr class="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-100">
            <th class="py-3 px-4">Teacher ID</th>
            <th class="py-3 px-4">Name</th>
            <th class="py-3 px-4">Email</th>
            <th class="py-3 px-4">Phone</th>
            <th class="py-3 px-4">Subject</th>
            <th class="py-3 px-4">Class Assigned</th>
            <th class="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${teachers.map(t => `
            <tr class="hover:bg-slate-50/75 transition">
              <td class="py-3 px-4 font-mono font-bold text-emerald-800">${t.teacher_id}</td>
              <td class="py-3 px-4 font-black text-slate-900">${t.name}</td>
              <td class="py-3 px-4 text-slate-500">${t.email}</td>
              <td class="py-3 px-4 text-slate-600 font-mono text-[11px]">${t.phone}</td>
              <td class="py-3 px-4 text-slate-700 font-semibold">${t.subject || 'General'}</td>
              <td class="py-3 px-4 text-slate-600">${t.class_name ? `${t.class_name} - ${t.assigned_section}` : '<span class="text-slate-400">Unassigned</span>'}</td>
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end space-x-1.5">
                  <button onclick="openEditTeacherModal(${JSON.stringify(t).replace(/"/g, '&quot;')})" class="p-1.5 rounded-lg text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition" title="Edit Teacher">
                    <i data-lucide="edit" class="w-4 h-4"></i>
                  </button>
                  <button onclick="deleteTeacher(${t.id}, '${t.name}')" class="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition" title="Delete Teacher">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                  </button>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;

  initLucide();
}

function openTeacherModal() {
  document.getElementById('teacher-form-id').value = '';
  document.getElementById('modal-teacher-title').textContent = 'Add New Teacher';
  document.getElementById('teacher-form').reset();
  document.getElementById('modal-teacher').classList.remove('hidden');
  initLucide();
}

function openEditTeacherModal(t) {
  document.getElementById('teacher-form-id').value = t.id;
  document.getElementById('modal-teacher-title').textContent = `Edit Teacher: ${t.name}`;
  document.getElementById('teacher-name').value = t.name;
  document.getElementById('teacher-email').value = t.email;
  document.getElementById('teacher-phone').value = t.phone;
  document.getElementById('teacher-subject').value = t.subject || '';
  document.getElementById('teacher-qualification').value = t.qualification || '';
  document.getElementById('teacher-status').value = t.status || 'active';
  document.getElementById('teacher-address').value = t.address || '';
  document.getElementById('modal-teacher').classList.remove('hidden');
  initLucide();
}

function closeTeacherModal() {
  document.getElementById('modal-teacher').classList.add('hidden');
}

async function saveTeacherForm() {
  const id = document.getElementById('teacher-form-id').value;
  const payload = {
    name: document.getElementById('teacher-name').value.trim(),
    email: document.getElementById('teacher-email').value.trim(),
    phone: document.getElementById('teacher-phone').value.trim(),
    subject: document.getElementById('teacher-subject').value.trim(),
    qualification: document.getElementById('teacher-qualification').value.trim(),
    status: document.getElementById('teacher-status').value,
    address: document.getElementById('teacher-address').value.trim()
  };

  const endpoint = id ? `/api/teachers/${id}` : '/api/teachers';
  const method = id ? 'PUT' : 'POST';

  const res = await apiFetch(endpoint, {
    method: method,
    body: JSON.stringify(payload)
  });

  if (res && res.success) {
    showToast(res.message || 'Teacher saved successfully.', 'success');
    closeTeacherModal();
    loadTeachersList();
  } else {
    showToast(res?.message || 'Error saving teacher.', 'error');
  }
}

async function deleteTeacher(id, name) {
  if (!confirm(`Are you sure you want to delete teacher "${name}"?`)) return;

  const res = await apiFetch(`/api/teachers/${id}`, { method: 'DELETE' });
  if (res && res.success) {
    showToast(`Teacher "${name}" deleted.`, 'success');
    loadTeachersList();
  } else {
    showToast(res?.message || 'Failed to delete teacher.', 'error');
  }
}

// =========================================================================
// 11. VIEW: CLASS MANAGEMENT
// =========================================================================

async function renderClassesView(container) {
  container.innerHTML = `
    <div class="space-y-5 animate-fade-in">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div>
          <h2 class="text-xl font-black text-slate-900">Class & Section Management</h2>
          <p class="text-xs text-slate-500">Organize rural school classes, section assignments, and room numbers.</p>
        </div>
        <button onclick="openClassModal()" class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 flex items-center space-x-1.5 transition">
          <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
          <span>Add Class</span>
        </button>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" id="classes-cards-container">
        <!-- Loaded dynamically -->
      </div>
    </div>
  `;

  initLucide();
  loadClassesList();
}

async function loadClassesList() {
  const container = document.getElementById('classes-cards-container');
  if (!container) return;

  container.innerHTML = `<div class="col-span-full p-8 text-center text-slate-400"><div class="inline-block animate-spin rounded-full h-6 w-6 border-3 border-emerald-600 border-t-transparent"></div><p class="mt-2 text-xs font-semibold">Loading classes...</p></div>`;

  const data = await apiFetch('/api/classes');
  if (!data || !data.success) {
    container.innerHTML = `<div class="col-span-full p-6 text-center text-rose-500">Failed to load classes.</div>`;
    return;
  }

  const classes = data.classes || [];
  state.classes = classes;

  container.innerHTML = classes.map(c => `
    <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-5 flex flex-col justify-between stat-card">
      <div>
        <div class="flex items-center justify-between mb-3">
          <span class="px-2.5 py-1 rounded-xl bg-emerald-50 text-emerald-800 text-xs font-black">Section ${c.section}</span>
          <span class="text-xs text-slate-400 font-mono">${c.room_number || 'Room 101'}</span>
        </div>
        <h3 class="text-lg font-black text-slate-900">${c.class_name}</h3>
        <div class="text-xs text-slate-500 mt-2 space-y-1">
          <p><strong class="text-slate-700">Class Teacher:</strong> ${c.class_teacher_name || 'Not assigned'}</p>
          <p><strong class="text-slate-700">Enrolled Students:</strong> ${c.student_count || 0}</p>
          <p><strong class="text-slate-700">Academic Year:</strong> ${c.academic_year || '2026-2027'}</p>
        </div>
      </div>

      <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
        <button onclick="startMarkingForClass(${c.id})" class="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center space-x-1">
          <i data-lucide="check-square" class="w-3.5 h-3.5"></i>
          <span>Take Attendance</span>
        </button>
        <div class="flex items-center space-x-1">
          <button onclick="openEditClassModal(${JSON.stringify(c).replace(/"/g, '&quot;')})" class="p-1.5 text-slate-400 hover:text-emerald-600">
            <i data-lucide="edit" class="w-4 h-4"></i>
          </button>
          <button onclick="deleteClass(${c.id}, '${c.class_name}-${c.section}')" class="p-1.5 text-slate-400 hover:text-rose-600">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </div>
      </div>
    </div>
  `).join('');

  initLucide();
}

function openClassModal() {
  document.getElementById('class-form-id').value = '';
  document.getElementById('modal-class-title').textContent = 'Add New Class';
  document.getElementById('class-form').reset();
  populateModalDropdowns();
  document.getElementById('modal-class').classList.remove('hidden');
  initLucide();
}

function openEditClassModal(c) {
  document.getElementById('class-form-id').value = c.id;
  document.getElementById('modal-class-title').textContent = `Edit Class: ${c.class_name} - ${c.section}`;
  document.getElementById('class-name').value = c.class_name;
  document.getElementById('class-section').value = c.section;
  document.getElementById('class-room').value = c.room_number || '';
  populateModalDropdowns();
  document.getElementById('class-teacher-id').value = c.teacher_id || '';
  document.getElementById('modal-class').classList.remove('hidden');
  initLucide();
}

function closeClassModal() {
  document.getElementById('modal-class').classList.add('hidden');
}

async function saveClassForm() {
  const id = document.getElementById('class-form-id').value;
  const payload = {
    class_name: document.getElementById('class-name').value.trim(),
    section: document.getElementById('class-section').value.trim(),
    room_number: document.getElementById('class-room').value.trim(),
    teacher_id: document.getElementById('class-teacher-id').value || null,
    academic_year: '2026-2027'
  };

  const endpoint = id ? `/api/classes/${id}` : '/api/classes';
  const method = id ? 'PUT' : 'POST';

  const res = await apiFetch(endpoint, {
    method: method,
    body: JSON.stringify(payload)
  });

  if (res && res.success) {
    showToast(res.message || 'Class saved successfully.', 'success');
    closeClassModal();
    loadClassesList();
    loadInitialData();
  } else {
    showToast(res?.message || 'Error saving class.', 'error');
  }
}

async function deleteClass(id, name) {
  if (!confirm(`Are you sure you want to delete class "${name}"?`)) return;

  const res = await apiFetch(`/api/classes/${id}`, { method: 'DELETE' });
  if (res && res.success) {
    showToast(`Class "${name}" deleted.`, 'success');
    loadClassesList();
    loadInitialData();
  } else {
    showToast(res?.message || 'Cannot delete class with active students.', 'error');
  }
}

// =========================================================================
// 12. VIEW: NOTIFICATIONS & SMS LOG
// =========================================================================

async function renderNotificationsView(container) {
  container.innerHTML = `
    <div class="space-y-6 animate-fade-in">
      <div class="flex items-center justify-between pb-2 border-b border-slate-200/80">
        <div>
          <h2 class="text-xl font-black text-slate-900">Notifications & Rural SMS Logs</h2>
          <p class="text-xs text-slate-500">Live feed of attendance alerts, parent SMS notifications, and system events.</p>
        </div>
        <button onclick="markAllNotificationsRead()" class="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition">
          Mark All Read
        </button>
      </div>

      <!-- Notifications Feed -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm divide-y divide-slate-100 p-4" id="notifications-full-list">
        <div class="p-8 text-center text-slate-400">Loading notifications...</div>
      </div>
    </div>
  `;

  initLucide();
  loadNotificationsFull();
}

async function loadNotifications() {
  const data = await apiFetch('/api/notifications');
  if (!data || !data.success) return;

  state.notifications = data.notifications || [];
  state.unreadNotifications = data.unread_count || 0;

  const badge = document.getElementById('unread-notification-count');
  if (badge) {
    if (state.unreadNotifications > 0) {
      badge.textContent = state.unreadNotifications;
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }

  const list = document.getElementById('notifications-list');
  if (list) {
    if (state.notifications.length === 0) {
      list.innerHTML = `<div class="p-4 text-center text-xs text-slate-400">No notifications at this time.</div>`;
    } else {
      list.innerHTML = state.notifications.map(n => `
        <div class="p-3 hover:bg-slate-50 transition flex items-start space-x-2.5 ${!n.is_read ? 'bg-emerald-50/40' : ''}">
          <div class="w-2 h-2 rounded-full ${!n.is_read ? 'bg-emerald-600' : 'bg-transparent'} mt-1.5 flex-shrink-0"></div>
          <div class="flex-1 min-w-0">
            <h5 class="text-xs font-bold text-slate-900 truncate">${n.title}</h5>
            <p class="text-[11px] text-slate-500 leading-snug mt-0.5">${n.message}</p>
            <span class="text-[9px] text-slate-400 mt-1 block">${n.created_at || 'Just now'}</span>
          </div>
        </div>
      `).join('');
    }
  }
}

async function loadNotificationsFull() {
  const container = document.getElementById('notifications-full-list');
  if (!container) return;

  const data = await apiFetch('/api/notifications');
  if (!data || !data.success) {
    container.innerHTML = `<div class="p-6 text-center text-rose-500">Failed to load notification history.</div>`;
    return;
  }

  const items = data.notifications || [];
  if (items.length === 0) {
    container.innerHTML = `<div class="p-8 text-center text-slate-400">No notifications on record.</div>`;
    return;
  }

  container.innerHTML = items.map(n => `
    <div class="p-4 flex items-start justify-between gap-3 ${!n.is_read ? 'bg-emerald-50/50 rounded-2xl' : ''}">
      <div class="flex items-start space-x-3">
        <div class="w-9 h-9 rounded-2xl ${n.type === 'alert' || n.type === 'warning' ? 'bg-rose-100 text-rose-600' : 'bg-emerald-100 text-emerald-700'} flex items-center justify-center font-bold flex-shrink-0">
          <i data-lucide="${n.type === 'alert' || n.type === 'warning' ? 'alert-triangle' : 'bell'}" class="w-4 h-4"></i>
        </div>
        <div>
          <h4 class="text-xs font-black text-slate-900">${n.title}</h4>
          <p class="text-xs text-slate-600 mt-0.5 leading-relaxed">${n.message}</p>
          <span class="text-[10px] text-slate-400 mt-1.5 block">${n.created_at}</span>
        </div>
      </div>
      ${!n.is_read ? `
        <button onclick="markNotificationRead(${n.id})" class="text-[11px] font-bold text-emerald-700 hover:underline flex-shrink-0">Mark read</button>
      ` : ''}
    </div>
  `).join('');

  initLucide();
}

function toggleNotificationDropdown() {
  const dd = document.getElementById('notification-dropdown');
  if (!dd) return;
  dd.classList.toggle('hidden');
}

function toggleUserDropdown() {
  const dd = document.getElementById('user-dropdown');
  if (!dd) return;
  dd.classList.toggle('hidden');
}

function closeAllDropdowns() {
  document.getElementById('notification-dropdown')?.classList.add('hidden');
  document.getElementById('user-dropdown')?.classList.add('hidden');
}

async function markNotificationRead(id) {
  await apiFetch(`/api/notifications/${id}/read`, { method: 'PUT' });
  loadNotifications();
  loadNotificationsFull();
}

async function markAllNotificationsRead() {
  await apiFetch('/api/notifications/read-all', { method: 'PUT' });
  loadNotifications();
  loadNotificationsFull();
  showToast('All notifications marked as read.', 'info');
}

// =========================================================================
// 13. VIEW: PROFILE & SYSTEM SETTINGS
// =========================================================================

async function renderSettingsView(container) {
  const user = state.currentUser || {};
  const settings = state.settings || {};
  const isAdmin = user.role === 'admin' || user.role === 'principal';

  container.innerHTML = `
    <div class="space-y-6 animate-fade-in max-w-4xl">
      
      <!-- Header -->
      <div class="pb-2 border-b border-slate-200/80">
        <h2 class="text-xl font-black text-slate-900">Profile & School Settings</h2>
        <p class="text-xs text-slate-500">Configure your profile credentials and school governance parameters.</p>
      </div>

      <!-- User Profile Card -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-6">
        <h3 class="text-sm font-bold text-slate-900 mb-4">My Account Details</h3>
        <form onsubmit="event.preventDefault(); updateProfile();" class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
              <input type="text" id="prof-name" value="${user.name || ''}" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Username (Read-Only)</label>
              <input type="text" value="${user.username || ''}" disabled class="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl text-xs text-slate-500 cursor-not-allowed">
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
              <input type="email" value="${user.email || ''}" disabled class="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl text-xs text-slate-500 cursor-not-allowed">
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Phone Number</label>
              <input type="text" id="prof-phone" value="${user.phone || ''}" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            </div>
          </div>
          <div class="flex justify-end">
            <button type="submit" class="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition">
              Update Profile
            </button>
          </div>
        </form>
      </div>

      <!-- Change Password Card -->
      <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-6">
        <h3 class="text-sm font-bold text-slate-900 mb-4">Security: Change Password</h3>
        <form onsubmit="event.preventDefault(); updatePassword();" class="space-y-3">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Current Password</label>
              <input type="password" id="pw-old" required placeholder="••••••••" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">New Password (Min. 6 chars)</label>
              <input type="password" id="pw-new" required placeholder="••••••••" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            </div>
          </div>
          <div class="flex justify-end">
            <button type="submit" class="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold transition">
              Update Password
            </button>
          </div>
        </form>
      </div>

      <!-- School Governance Settings (Admin / Principal Only) -->
      ${isAdmin ? `
        <div class="bg-white rounded-3xl border border-slate-100 shadow-sm p-6">
          <h3 class="text-sm font-bold text-slate-900 mb-4">School Master Configuration</h3>
          <form onsubmit="event.preventDefault(); saveSchoolSettings();" class="space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-700 mb-1">School Name</label>
                <input type="text" id="set-school-name" value="${settings.school_name || 'Green Valley Rural Model School'}" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-700 mb-1">Academic Year</label>
                <input type="text" id="set-academic-year" value="${settings.academic_year || '2026-2027'}" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-700 mb-1">Low Attendance Alert Threshold (%)</label>
                <input type="number" step="0.5" id="set-threshold" value="${settings.low_attendance_threshold || '75.0'}" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-700 mb-1">School Contact Phone</label>
                <input type="text" id="set-contact" value="${settings.contact_number || '+91 98765 43210'}" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
              </div>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Rural School Address</label>
              <input type="text" id="set-address" value="${settings.school_address || 'Village Rampur, District Education Zone, Pin 243504'}" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            </div>
            <div class="flex justify-end">
              <button type="submit" class="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition">
                Save System Settings
              </button>
            </div>
          </form>
        </div>
      ` : ''}

    </div>
  `;

  initLucide();
}

async function updateProfile() {
  const name = document.getElementById('prof-name').value.trim();
  const phone = document.getElementById('prof-phone').value.trim();

  const res = await apiFetch('/api/auth/profile', {
    method: 'PUT',
    body: JSON.stringify({ name, phone })
  });

  if (res && res.success) {
    state.currentUser.name = name;
    state.currentUser.phone = phone;
    document.getElementById('header-user-name').textContent = name;
    showToast('Profile updated successfully!', 'success');
  } else {
    showToast(res?.message || 'Failed to update profile.', 'error');
  }
}

async function updatePassword() {
  const old_password = document.getElementById('pw-old').value.trim();
  const new_password = document.getElementById('pw-new').value.trim();

  const res = await apiFetch('/api/auth/change-password', {
    method: 'PUT',
    body: JSON.stringify({ old_password, new_password })
  });

  if (res && res.success) {
    showToast('Password changed successfully!', 'success');
    document.getElementById('pw-old').value = '';
    document.getElementById('pw-new').value = '';
  } else {
    showToast(res?.message || 'Error updating password.', 'error');
  }
}

async function saveSchoolSettings() {
  const payload = {
    school_name: document.getElementById('set-school-name').value.trim(),
    academic_year: document.getElementById('set-academic-year').value.trim(),
    low_attendance_threshold: document.getElementById('set-threshold').value.trim(),
    contact_number: document.getElementById('set-contact').value.trim(),
    school_address: document.getElementById('set-address').value.trim()
  };

  const res = await apiFetch('/api/settings', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (res && res.success) {
    state.settings = { ...state.settings, ...payload };
    showToast('School settings saved!', 'success');
  } else {
    showToast(res?.message || 'Error updating settings.', 'error');
  }
}

// =========================================================================
// 14. UTILITY & TOAST SYSTEM
// =========================================================================

function getStatusBadgeClass(status) {
  if (status === 'Present') return 'bg-emerald-50 text-emerald-800 border-emerald-200';
  if (status === 'Absent') return 'bg-rose-50 text-rose-800 border-rose-200';
  if (status === 'Late') return 'bg-amber-50 text-amber-800 border-amber-200';
  return 'bg-slate-50 text-slate-600 border-slate-200';
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  let bg = 'bg-slate-900 text-white';
  let icon = 'info';

  if (type === 'success') {
    bg = 'bg-emerald-800 text-white border border-emerald-600';
    icon = 'check-circle-2';
  } else if (type === 'error') {
    bg = 'bg-rose-800 text-white border border-rose-600';
    icon = 'alert-circle';
  } else if (type === 'warning') {
    bg = 'bg-amber-700 text-white border border-amber-500';
    icon = 'alert-triangle';
  }

  toast.className = `${bg} px-4 py-3 rounded-2xl shadow-xl text-xs font-semibold flex items-center space-x-2.5 pointer-events-auto transform transition-all duration-300 translate-y-2 opacity-0 max-w-sm`;
  toast.innerHTML = `
    <i data-lucide="${icon}" class="w-4 h-4 flex-shrink-0"></i>
    <span class="flex-1 leading-snug">${message}</span>
  `;

  container.appendChild(toast);
  initLucide();

  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
