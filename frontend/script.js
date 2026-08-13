/**
 * script.js – TaskFlow2 Frontend
 * 
 * Full SPA controller. Requires auth.js to be loaded first.
 */
'use strict';

// ═══════════════════════════════════════════════════════════════
// 1. AUTH GUARD – redirect immediately if no token
// ═══════════════════════════════════════════════════════════════
Auth.guardPage();

// ═══════════════════════════════════════════════════════════════
// 2. CONFIGURATION
// ═══════════════════════════════════════════════════════════════
const API_BASE = Config.getApiBase();

// ═══════════════════════════════════════════════════════════════
// 3. STATE
// ═══════════════════════════════════════════════════════════════
let currentTasks    = [];
let currentProjects = [];
let editingTaskId   = null;
let isSorted        = false;

// ═══════════════════════════════════════════════════════════════
// 4. DOM REFERENCES
// ═══════════════════════════════════════════════════════════════
const loader         = document.getElementById('loader');
const toastContainer = document.getElementById('toast-container');

// Navigation
const navItems  = document.querySelectorAll('.sidebar-nav li[data-section]');
const pageTitle = document.getElementById('page-title');

// Header
const currentUserName = document.getElementById('current-user-name');
const headerLogout    = document.getElementById('header-logout');
const sidebarLogout   = document.getElementById('sidebar-logout');

// Task form
const taskForm     = document.getElementById('task-form');
const taskTitle    = document.getElementById('task-title');
const taskDesc     = document.getElementById('task-desc');
const taskPriority = document.getElementById('task-priority');
const taskDue      = document.getElementById('task-due');
const taskProject  = document.getElementById('task-project');

// Quick-add form
const quickAddForm = document.getElementById('quick-add-form');
const quickText    = document.getElementById('quick-text');
const quickProject = document.getElementById('quick-project');

// Edit modal
const editModal    = document.getElementById('edit-modal');
const editForm     = document.getElementById('edit-form');
const modalCloseBtn = document.getElementById('modal-close-btn');
const editId       = document.getElementById('edit-id');
const editTitle    = document.getElementById('edit-title');
const editDesc     = document.getElementById('edit-desc');
const editPriority = document.getElementById('edit-priority');
const editDue      = document.getElementById('edit-due');
const editProject  = document.getElementById('edit-project');
const editStatus   = document.getElementById('edit-status');
const improveBtn   = document.getElementById('improve-btn');

// Search & sort
const searchInput    = document.getElementById('search-input');
const searchAlgo     = document.getElementById('search-algo');
const searchBtn      = document.getElementById('search-btn');
const clearSearchBtn = document.getElementById('clear-search-btn');
const sortBtn        = document.getElementById('sort-btn');
const resetSortBtn   = document.getElementById('reset-sort-btn');

// Task list
const taskListEl        = document.getElementById('task-list');
const recentTaskListEl  = document.getElementById('recent-task-list');
const taskCountBadge    = document.getElementById('task-count-badge');

// Project section
const projectForm   = document.getElementById('project-form');
const projectName   = document.getElementById('project-name');
const projectDescEl = document.getElementById('project-desc');
const projectListEl = document.getElementById('project-list');
const projectsCountBadge = document.getElementById('projects-count-badge');

// Footer
document.getElementById('footer-year').textContent = new Date().getFullYear();

// ═══════════════════════════════════════════════════════════════
// 5. UTILITIES
// ═══════════════════════════════════════════════════════════════
function showLoader()  { loader.style.display = 'flex'; }
function hideLoader()  { loader.style.display = 'none'; }

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', info: 'fa-info-circle' };
  toast.innerHTML = `<i class="fas ${icons[type] || 'fa-info-circle'}"></i> ${message}`;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function saveToCache(key, data) {
  try { localStorage.setItem(`taskflow_${key}`, JSON.stringify(data)); } catch (_) {}
}
function loadFromCache(key) {
  try {
    const raw = localStorage.getItem(`taskflow_${key}`);
    return raw ? JSON.parse(raw) : null;
  } catch (_) { return null; }
}

function formatDate(dateStr) {
  if (!dateStr) return 'No due date';
  try {
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr; // raw string like "tomorrow"
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  } catch (_) { return dateStr; }
}

function animateNumber(el, target) {
  const start = parseInt(el.textContent) || 0;
  if (start === target) { el.textContent = target; return; }
  const step = target > start ? 1 : -1;
  let current = start;
  const interval = setInterval(() => {
    current += step;
    el.textContent = current;
    if (current === target) clearInterval(interval);
  }, Math.max(1, Math.floor(300 / Math.abs(target - start))));
}

// ═══════════════════════════════════════════════════════════════
// 6. FETCH WRAPPER (injects Bearer token, handles 401)
// ═══════════════════════════════════════════════════════════════
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await Auth.fetchWithAuth(url, options);

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      try { detail = await response.text() || detail; } catch (_2) {}
    }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

// ═══════════════════════════════════════════════════════════════
// 7. NAVIGATION
// ═══════════════════════════════════════════════════════════════
const SECTION_TITLES = {
  dashboard: 'Dashboard',
  tasks:     'Tasks',
  projects:  'Projects',
};

function showSection(name) {
  // Update sidebar active state
  navItems.forEach(li => {
    li.classList.toggle('active', li.dataset.section === name);
  });

  // Show/hide sections
  document.querySelectorAll('.page-section').forEach(sec => {
    sec.classList.add('hidden');
  });
  const target = document.getElementById(`section-${name}`);
  if (target) target.classList.remove('hidden');

  // Update header title
  pageTitle.textContent = SECTION_TITLES[name] || name;

  // Lazy-load section data
  if (name === 'projects') renderProjectList();
  if (name === 'dashboard') updateStatisticsFromAPI();
}

navItems.forEach(li => {
  li.addEventListener('click', () => showSection(li.dataset.section));
});

// ═══════════════════════════════════════════════════════════════
// 8. USER PROFILE
// ═══════════════════════════════════════════════════════════════
async function loadCurrentUser() {
  let user = Auth.getUser();
  if (!user) {
    try {
      user = await fetchAPI('/auth/me');
      Auth.setUser(user);
    } catch (e) {
      console.error('Could not load user profile:', e);
    }
  }
  if (user) {
    currentUserName.textContent = user.full_name;
  }
}

// Logout handlers
headerLogout.addEventListener('click', () => Auth.logout());
sidebarLogout.addEventListener('click', () => Auth.logout());

// ═══════════════════════════════════════════════════════════════
// 9. STATISTICS (uses /projects/statistics API)
// ═══════════════════════════════════════════════════════════════
async function updateStatisticsFromAPI() {
  try {
    const stats = await fetchAPI('/projects/statistics');
    let total = 0, high = 0, medium = 0, low = 0;
    stats.forEach(p => {
      total  += p.total_tasks;
      high   += p.priority_counts.high;
      medium += p.priority_counts.medium;
      low    += p.priority_counts.low;
    });
    animateNumber(document.querySelector('#stat-total .stat-number'),    total);
    animateNumber(document.querySelector('#stat-high .stat-number'),     high);
    animateNumber(document.querySelector('#stat-medium .stat-number'),   medium);
    animateNumber(document.querySelector('#stat-low .stat-number'),      low);
    animateNumber(document.querySelector('#stat-projects .stat-number'), stats.length);
  } catch (e) {
    console.warn('Stats from API failed, using local data:', e.message);
    // Fallback: count from cached tasks
    let high = 0, medium = 0, low = 0;
    currentTasks.forEach(t => {
      if (t.priority === 'high') high++;
      else if (t.priority === 'medium') medium++;
      else low++;
    });
    document.querySelector('#stat-total .stat-number').textContent    = currentTasks.length;
    document.querySelector('#stat-high .stat-number').textContent     = high;
    document.querySelector('#stat-medium .stat-number').textContent   = medium;
    document.querySelector('#stat-low .stat-number').textContent      = low;
    document.querySelector('#stat-projects .stat-number').textContent = currentProjects.length;
  }

  // Status counts – separate endpoint, non-blocking
  try {
    const sc = await fetchAPI('/tasks/status-counts');
    animateNumber(document.querySelector('#stat-todo .stat-number'),       sc.todo        || 0);
    animateNumber(document.querySelector('#stat-inprogress .stat-number'), sc.in_progress || 0);
    animateNumber(document.querySelector('#stat-completed .stat-number'),  sc.completed   || 0);
  } catch (e) {
    // Fallback: count from local cache
    let todo = 0, inprog = 0, done = 0;
    currentTasks.forEach(t => {
      const sv = t.status && t.status.value ? t.status.value : (t.status || 'todo');
      if (sv === 'todo') todo++;
      else if (sv === 'in_progress') inprog++;
      else if (sv === 'completed') done++;
    });
    document.querySelector('#stat-todo .stat-number').textContent       = todo;
    document.querySelector('#stat-inprogress .stat-number').textContent = inprog;
    document.querySelector('#stat-completed .stat-number').textContent  = done;
  }
}

// ═══════════════════════════════════════════════════════════════
// 10. PROJECT DROPDOWNS
// ═══════════════════════════════════════════════════════════════
function populateProjectDropdowns() {
  const selects = [taskProject, quickProject, editProject];
  selects.forEach(sel => {
    const current = sel.value;
    sel.innerHTML = '<option value="">Select Project</option>';
    currentProjects.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name;
      sel.appendChild(opt);
    });
    // Restore previous selection if still valid
    if (current && currentProjects.some(p => String(p.id) === current)) {
      sel.value = current;
    }
  });
}

async function loadProjects() {
  try {
    const projects = await fetchAPI('/projects');
    currentProjects = projects;
    saveToCache('projects', projects);
    populateProjectDropdowns();
    return projects;
  } catch (e) {
    console.error('Failed to load projects:', e);
    showToast('Failed to load projects', 'error');
    return [];
  }
}

// ═══════════════════════════════════════════════════════════════
// 11. TASK RENDERING
// ═══════════════════════════════════════════════════════════════
function getProjectName(projectId) {
  const p = currentProjects.find(p => p.id === projectId);
  return p ? p.name : `Project #${projectId}`;
}

function buildTaskItem(task, isCompact = false) {
  const item = document.createElement('div');
  item.className = 'task-item';
  item.id = `task-${task.id}`;

  const priorityValue = task.priority && task.priority.value
    ? task.priority.value
    : (task.priority || 'medium');

  // Normalise status — API returns enum object or plain string
  const statusValue = task.status && task.status.value
    ? task.status.value
    : (task.status || 'todo');

  const STATUS_LABELS = { todo: 'To Do', in_progress: 'In Progress', completed: 'Completed' };
  const statusLabel   = STATUS_LABELS[statusValue] || statusValue;

  const projectName = getProjectName(task.project_id);
  const createdDate = formatDate(task.created_at);
  const dueDate     = task.due_date || 'No due date';

  item.innerHTML = `
    <div class="task-info">
      <div class="task-title">${escapeHtml(task.title)}</div>
      ${!isCompact ? `<div class="task-desc">${escapeHtml(task.description || 'No description')}</div>` : ''}
      <div class="task-meta">
        <span class="priority-badge priority-${priorityValue}">${priorityValue}</span>
        <span class="status-badge status-${statusValue}">${statusLabel}</span>
        <span><i class="far fa-calendar-alt"></i> ${escapeHtml(dueDate)}</span>
        <span><i class="fas fa-project-diagram"></i> ${escapeHtml(projectName)}</span>
        <span><i class="far fa-clock"></i> ${createdDate}</span>
      </div>
    </div>
    <div class="task-actions">
      ${!isCompact ? `
      <select class="status-select" title="Change status" aria-label="Change task status">
        <option value="todo"        ${statusValue === 'todo'        ? 'selected' : ''}>To Do</option>
        <option value="in_progress" ${statusValue === 'in_progress' ? 'selected' : ''}>In Progress</option>
        <option value="completed"   ${statusValue === 'completed'   ? 'selected' : ''}>Completed</option>
      </select>` : ''}
      <button class="btn btn-secondary btn-sm edit-btn" title="Edit task">
        <i class="fas fa-edit"></i>
      </button>
      <button class="btn btn-danger btn-sm delete-btn" title="Delete task">
        <i class="fas fa-trash"></i>
      </button>
    </div>
  `;

  item.querySelector('.edit-btn').addEventListener('click', () => openEditModal(task));
  item.querySelector('.delete-btn').addEventListener('click', () => deleteTask(task.id));

  // Inline status change
  if (!isCompact) {
    item.querySelector('.status-select').addEventListener('change', async function () {
      const newStatus = this.value;
      try {
        await fetchAPI(`/tasks/${task.id}/status`, {
          method: 'PATCH',
          body: JSON.stringify({ status: newStatus }),
        });
        // Update local cache so re-renders stay consistent
        const cached = currentTasks.find(t => t.id === task.id);
        if (cached) cached.status = newStatus;
        // Refresh status badge text without full re-render
        const badge = item.querySelector('.status-badge');
        if (badge) {
          badge.className = `status-badge status-${newStatus}`;
          badge.textContent = STATUS_LABELS[newStatus] || newStatus;
        }
        await updateStatisticsFromAPI();
        showToast(`Status → ${STATUS_LABELS[newStatus]}`, 'success');
      } catch (e) {
        showToast(`Status update failed: ${e.message}`, 'error');
        this.value = statusValue; // revert
      }
    });
  }

  return item;
}

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderTasks(tasks) {
  taskListEl.innerHTML = '';

  if (!tasks || tasks.length === 0) {
    taskListEl.innerHTML = `
      <div class="empty-message">
        <i class="fas fa-inbox"></i>
        <p>No tasks found</p>
        <small>Create a task using the form above</small>
      </div>`;
    taskCountBadge.textContent = '';
    return;
  }

  taskCountBadge.textContent = `(${tasks.length})`;
  tasks.forEach((task, i) => {
    const el = buildTaskItem(task);
    el.style.animationDelay = `${i * 30}ms`;
    taskListEl.appendChild(el);
  });
}

function renderRecentTasks(tasks) {
  recentTaskListEl.innerHTML = '';
  const recent = [...tasks]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  if (!recent.length) {
    recentTaskListEl.innerHTML = `
      <div class="empty-message">
        <i class="fas fa-inbox"></i>
        <p>No tasks yet</p>
        <small>Go to Tasks to create your first task</small>
      </div>`;
    return;
  }
  recent.forEach((task, i) => {
    const el = buildTaskItem(task, true);
    el.style.animationDelay = `${i * 40}ms`;
    recentTaskListEl.appendChild(el);
  });
}

async function loadTasks() {
  try {
    const tasks = await fetchAPI('/tasks');
    currentTasks = tasks;
    saveToCache('tasks', tasks);
    renderTasks(tasks);
    renderRecentTasks(tasks);
    return tasks;
  } catch (e) {
    console.error('Failed to load tasks:', e);
    showToast('Failed to load tasks', 'error');
    return [];
  }
}

// ═══════════════════════════════════════════════════════════════
// 12. TASK CRUD
// ═══════════════════════════════════════════════════════════════
async function createTask(event) {
  event.preventDefault();
  const title = taskTitle.value.trim();
  if (!title) { showToast('Title is required', 'error'); return; }
  const projectId = taskProject.value;
  if (!projectId) { showToast('Please select a project', 'error'); return; }

  const data = {
    title,
    description: taskDesc.value.trim() || null,
    priority: taskPriority.value,
    due_date: taskDue.value.trim() || null,
    project_id: parseInt(projectId, 10),
  };

  showLoader();
  try {
    await fetchAPI('/tasks', { method: 'POST', body: JSON.stringify(data) });
    showToast('Task created!', 'success');
    taskForm.reset();
    isSorted = false;
    resetSortBtn.style.display = 'none';
    sortBtn.style.display = '';
    await loadTasks();
    await updateStatisticsFromAPI();
  } catch (e) {
    showToast(`Failed to create task: ${e.message}`, 'error');
  } finally {
    hideLoader();
  }
}

async function deleteTask(id) {
  if (!confirm('Delete this task? This cannot be undone.')) return;
  showLoader();
  try {
    await fetchAPI(`/tasks/${id}`, { method: 'DELETE' });
    showToast('Task deleted', 'success');
    await loadTasks();
    await updateStatisticsFromAPI();
  } catch (e) {
    showToast(`Failed to delete task: ${e.message}`, 'error');
  } finally {
    hideLoader();
  }
}

// ─── Edit Modal ───────────────────────────────────────────────
function openEditModal(task) {
  editingTaskId = task.id;
  editId.value  = task.id;
  editTitle.value   = task.title;
  editDesc.value    = task.description || '';
  editPriority.value = task.priority && task.priority.value
    ? task.priority.value
    : (task.priority || 'medium');
  editDue.value     = task.due_date || '';
  // Set status
  const sv = task.status && task.status.value ? task.status.value : (task.status || 'todo');
  editStatus.value = sv;
  // Wait for dropdown to have options, then set
  populateProjectDropdowns();
  setTimeout(() => { editProject.value = String(task.project_id); }, 0);
  editModal.classList.add('show');
  editTitle.focus();
}

function closeEditModal() {
  editModal.classList.remove('show');
  editingTaskId = null;
  editForm.reset();
}

modalCloseBtn.addEventListener('click', closeEditModal);
window.addEventListener('click', e => { if (e.target === editModal) closeEditModal(); });
window.addEventListener('keydown', e => { if (e.key === 'Escape' && editModal.classList.contains('show')) closeEditModal(); });

// ─── AI Improve Task ──────────────────────────────────────────
improveBtn.addEventListener('click', async () => {
  const currentTitle = editTitle.value.trim();
  if (!currentTitle) { showToast('Enter a task title first', 'error'); return; }

  improveBtn.disabled = true;
  improveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Improving…';

  try {
    const result = await fetchAPI('/tasks/improve', {
      method: 'POST',
      body: JSON.stringify({
        title:       currentTitle,
        description: editDesc.value.trim() || null,
        priority:    editPriority.value || 'medium',
        due_date:    editDue.value.trim() || null,
      }),
    });

    // Apply improvements to the modal fields
    if (result.title)       editTitle.value    = result.title;
    if (result.description) editDesc.value     = result.description;
    if (result.priority)    editPriority.value = result.priority;
    if (result.due_date)    editDue.value      = result.due_date;

    showToast('Task improved by AI ✨', 'success');
  } catch (e) {
    showToast(`Improve failed: ${e.message}`, 'error');
  } finally {
    improveBtn.disabled = false;
    improveBtn.innerHTML = '<i class="fas fa-magic"></i> Improve with AI';
  }
});
async function updateTask(event) {
  event.preventDefault();
  const id    = parseInt(editId.value, 10);
  const title = editTitle.value.trim();
  if (!title) { showToast('Title is required', 'error'); return; }
  const projectId = editProject.value;
  if (!projectId) { showToast('Please select a project', 'error'); return; }

  const data = {
    title,
    description: editDesc.value.trim() || null,
    priority: editPriority.value,
    status: editStatus.value,
    due_date: editDue.value.trim() || null,
    project_id: parseInt(projectId, 10),
  };

  showLoader();
  try {
    await fetchAPI(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) });
    showToast('Task updated!', 'success');
    closeEditModal();
    await loadTasks();
    await updateStatisticsFromAPI();
  } catch (e) {
    showToast(`Failed to update task: ${e.message}`, 'error');
  } finally {
    hideLoader();
  }
}

// ═══════════════════════════════════════════════════════════════
// 13. SEARCH
// ═══════════════════════════════════════════════════════════════
async function searchTask() {
  const title = searchInput.value.trim();
  if (!title) { showToast('Enter a title to search', 'error'); return; }

  const algo = searchAlgo.value;
  showLoader();
  try {
    const result = await fetchAPI(
      `/tasks/search?title=${encodeURIComponent(title)}&algo=${algo}`
    );

    if (result) {
      // Highlight the found item in the list
      const found = document.getElementById(`task-${result.id}`);
      if (found) {
        found.scrollIntoView({ behavior: 'smooth', block: 'center' });
        found.classList.add('task-highlight');
        setTimeout(() => found.classList.remove('task-highlight'), 2500);
        showToast(`Found: "${result.title}"`, 'success');
      } else {
        // Task exists in DB but may not be in current view (e.g. sorted/filtered)
        showToast(`Found: "${result.title}" (ID ${result.id}). Reloading list…`, 'info');
        await loadTasks();
        setTimeout(() => {
          const el = document.getElementById(`task-${result.id}`);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            el.classList.add('task-highlight');
            setTimeout(() => el.classList.remove('task-highlight'), 2500);
          }
        }, 300);
      }
      clearSearchBtn.style.display = '';
    }
  } catch (e) {
    // The backend returns "Task not found" (not a raw "404") as the detail string
    const msg = e.message || '';
    if (msg.includes('Task not found') || msg.includes('No tasks found') || msg.includes('404')) {
      showToast('No task found with that exact title', 'error');
    } else {
      showToast(`Search error: ${msg}`, 'error');
    }
  } finally {
    hideLoader();
  }
}

clearSearchBtn.addEventListener('click', () => {
  searchInput.value = '';
  clearSearchBtn.style.display = 'none';
  renderTasks(currentTasks);
});

searchBtn.addEventListener('click', searchTask);
searchInput.addEventListener('keydown', e => { if (e.key === 'Enter') searchTask(); });

// ═══════════════════════════════════════════════════════════════
// 14. SORT
// ═══════════════════════════════════════════════════════════════
async function sortTasks() {
  showLoader();
  try {
    const tasks = await fetchAPI('/tasks?sort=priority');
    currentTasks = tasks;
    renderTasks(tasks);
    isSorted = true;
    sortBtn.style.display = 'none';
    resetSortBtn.style.display = '';
    showToast('Sorted by priority (low → high)', 'info');
  } catch (e) {
    showToast(`Sort failed: ${e.message}`, 'error');
  } finally {
    hideLoader();
  }
}

async function resetSort() {
  showLoader();
  try {
    const tasks = await fetchAPI('/tasks');
    currentTasks = tasks;
    renderTasks(tasks);
    isSorted = false;
    resetSortBtn.style.display = 'none';
    sortBtn.style.display = '';
    showToast('Sort reset', 'info');
  } catch (e) {
    showToast(`Reset failed: ${e.message}`, 'error');
  } finally {
    hideLoader();
  }
}

sortBtn.addEventListener('click', sortTasks);
resetSortBtn.addEventListener('click', resetSort);

// ═══════════════════════════════════════════════════════════════
// 15. AI QUICK ADD
// ═══════════════════════════════════════════════════════════════
async function quickAddTask(event) {
  event.preventDefault();
  const text = quickText.value.trim();
  if (!text) { showToast('Please describe the task', 'error'); return; }
  const projectId = quickProject.value;
  if (!projectId) { showToast('Please select a project', 'error'); return; }

  showLoader();
  try {
    const created = await fetchAPI('/tasks/quick-add', {
      method: 'POST',
      body: JSON.stringify({ text, project_id: parseInt(projectId, 10) }),
    });
    showToast(`AI created task: "${created.title}"`, 'success');
    quickAddForm.reset();
    await loadTasks();
    await updateStatisticsFromAPI();
  } catch (e) {
    showToast(`AI quick-add failed: ${e.message}`, 'error');
  } finally {
    hideLoader();
  }
}

// ═══════════════════════════════════════════════════════════════
// 16. PROJECTS SECTION
// ═══════════════════════════════════════════════════════════════
async function createProject(event) {
  event.preventDefault();
  const name = projectName.value.trim();
  if (!name) { showToast('Project name is required', 'error'); return; }

  showLoader();
  try {
    await fetchAPI('/projects', {
      method: 'POST',
      body: JSON.stringify({
        name,
        description: projectDescEl.value.trim() || null,
      }),
    });
    showToast('Project created!', 'success');
    projectForm.reset();
    await loadProjects();
    renderProjectList();
    await updateStatisticsFromAPI();
  } catch (e) {
    showToast(`Failed to create project: ${e.message}`, 'error');
  } finally {
    hideLoader();
  }
}

async function renderProjectList() {
  // Always fetch fresh statistics for project cards
  let statsMap = {};
  try {
    const stats = await fetchAPI('/projects/statistics');
    stats.forEach(s => {
      statsMap[s.project_id] = s;
    });
  } catch (_) {}

  projectListEl.innerHTML = '';

  if (!currentProjects.length) {
    projectListEl.innerHTML = `
      <div class="empty-message">
        <i class="fas fa-folder-open"></i>
        <p>No projects yet</p>
        <small>Create your first project above</small>
      </div>`;
    projectsCountBadge.textContent = '';
    return;
  }

  projectsCountBadge.textContent = `(${currentProjects.length})`;

  currentProjects.forEach((project, i) => {
    const stat = statsMap[project.id] || {
      total_tasks: 0,
      priority_counts: { high: 0, medium: 0, low: 0 }
    };

    const card = document.createElement('div');
    card.className = 'project-card';
    card.style.animationDelay = `${i * 40}ms`;
    card.innerHTML = `
      <div class="project-card-header">
        <h3>${escapeHtml(project.name)}</h3>
        <span class="project-badge">${stat.total_tasks} task${stat.total_tasks !== 1 ? 's' : ''}</span>
      </div>
      <p class="project-desc">${escapeHtml(project.description || 'No description')}</p>
      <div class="priority-bars">
        <span class="priority-bar-item"><span class="dot dot-high"></span>
          <span style="color:#e74c3c;">${stat.priority_counts.high}</span>
        </span>
        <span class="priority-bar-item"><span class="dot dot-medium"></span>
          <span style="color:#f39c12;">${stat.priority_counts.medium}</span>
        </span>
        <span class="priority-bar-item"><span class="dot dot-low"></span>
          <span style="color:#2ecc71;">${stat.priority_counts.low}</span>
        </span>
      </div>
      <div class="project-meta">
        <span><i class="fas fa-user"></i> ${escapeHtml(Auth.getUser()?.full_name || 'You')}</span>
        <span><i class="far fa-calendar"></i> ${formatDate(project.created_at)}</span>
      </div>
      <div class="task-actions" style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.06);">
        <button class="btn btn-secondary btn-sm proj-edit-btn" title="Edit project">
          <i class="fas fa-edit"></i> Edit
        </button>
        <button class="btn btn-danger btn-sm proj-delete-btn" title="Delete project">
          <i class="fas fa-trash"></i> Delete
        </button>
      </div>
    `;
    card.querySelector('.proj-edit-btn').addEventListener('click', () => openProjectEditModal(project));
    card.querySelector('.proj-delete-btn').addEventListener('click', () => deleteProject(project.id, project.name));
    projectListEl.appendChild(card);
  });
}

// ═══════════════════════════════════════════════════════════════
// 16b. PROJECT EDIT / DELETE
// ═══════════════════════════════════════════════════════════════

// ── Project edit modal state ──────────────────────────────────
let editingProjectId = null;

function openProjectEditModal(project) {
  editingProjectId = project.id;
  // Reuse the existing project form fields as an inline edit
  // We show a simple prompt-style modal built on the fly
  const modalHtml = `
    <div id="proj-edit-modal" style="
      position:fixed;inset:0;z-index:2000;
      background:rgba(0,0,0,0.65);backdrop-filter:blur(6px);
      display:flex;align-items:center;justify-content:center;">
      <div style="
        background:#1a1830;border:1px solid rgba(255,255,255,0.07);
        border-radius:24px;padding:32px;max-width:480px;width:90%;
        box-shadow:0 24px 60px rgba(0,0,0,0.5);">
        <h2 style="font-size:1.1rem;font-weight:600;margin-bottom:22px;color:#fff;display:flex;align-items:center;gap:10px;">
          <i class="fas fa-edit" style="color:#6c5ce7;"></i> Edit Project
        </h2>
        <div class="form-group">
          <label for="pem-name">Project Name</label>
          <input type="text" id="pem-name" value="${escapeHtml(project.name)}" required />
        </div>
        <div class="form-group">
          <label for="pem-desc">Description</label>
          <textarea id="pem-desc" rows="2">${escapeHtml(project.description || '')}</textarea>
        </div>
        <div style="display:flex;gap:12px;margin-top:8px;">
          <button id="pem-save" class="btn btn-primary"><i class="fas fa-save"></i> Save</button>
          <button id="pem-cancel" class="btn btn-secondary"><i class="fas fa-times"></i> Cancel</button>
        </div>
      </div>
    </div>`;

  document.body.insertAdjacentHTML('beforeend', modalHtml);
  const modal = document.getElementById('proj-edit-modal');
  document.getElementById('pem-name').focus();

  document.getElementById('pem-cancel').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });

  document.getElementById('pem-save').addEventListener('click', async () => {
    const name = document.getElementById('pem-name').value.trim();
    const desc = document.getElementById('pem-desc').value.trim() || null;
    if (!name) { showToast('Project name is required', 'error'); return; }

    showLoader();
    try {
      await fetchAPI(`/projects/${editingProjectId}`, {
        method: 'PUT',
        body: JSON.stringify({ name, description: desc }),
      });
      showToast('Project updated!', 'success');
      modal.remove();
      await loadProjects();
      await renderProjectList();
      await updateStatisticsFromAPI();
    } catch (e) {
      showToast(`Failed to update project: ${e.message}`, 'error');
    } finally {
      hideLoader();
      editingProjectId = null;
    }
  });
}

async function deleteProject(projectId, projectName) {
  if (!confirm(`Delete project "${projectName}" and ALL its tasks? This cannot be undone.`)) return;
  showLoader();
  try {
    await fetchAPI(`/projects/${projectId}`, { method: 'DELETE' });
    showToast(`Project "${projectName}" deleted`, 'success');
    await loadProjects();
    await renderProjectList();
    await updateStatisticsFromAPI();
    // Also refresh task list since tasks were cascade-deleted
    await loadTasks();
  } catch (e) {
    showToast(`Failed to delete project: ${e.message}`, 'error');
  } finally {
    hideLoader();
  }
}

// ═══════════════════════════════════════════════════════════════
// 17. EVENT LISTENERS
// ═══════════════════════════════════════════════════════════════
taskForm.addEventListener('submit', createTask);
editForm.addEventListener('submit', updateTask);
quickAddForm.addEventListener('submit', quickAddTask);
projectForm.addEventListener('submit', createProject);

// ═══════════════════════════════════════════════════════════════
// 18. INITIALISATION
// ═══════════════════════════════════════════════════════════════
async function init() {
  // Show cached data instantly to avoid blank flash
  const cachedTasks    = loadFromCache('tasks');
  const cachedProjects = loadFromCache('projects');

  if (cachedProjects) {
    currentProjects = cachedProjects;
    populateProjectDropdowns();
  }
  if (cachedTasks) {
    currentTasks = cachedTasks;
    renderTasks(cachedTasks);
    renderRecentTasks(cachedTasks);
  }

  // Load user profile (fast – uses cache if present)
  await loadCurrentUser();

  // Parallel fetch of all data
  try {
    await Promise.all([
      loadProjects(),
      loadTasks(),
    ]);
  } catch (e) {
    console.warn('Some initial data failed to load:', e);
  }

  // Update statistics
  await updateStatisticsFromAPI();

  // Default section
  showSection('dashboard');
}

// ── Start ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
