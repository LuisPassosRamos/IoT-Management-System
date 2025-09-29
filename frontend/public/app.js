(() => {
  const API_BASE_URL = (() => {
    const origin = window.location.origin;
    if (origin.includes(':8080')) {
      return origin.replace(':8080', ':8000');
    }
    return 'http://localhost:8000';
  })();

  const userIdStr = localStorage.getItem('userId');
  const state = {
    token: localStorage.getItem('authToken') || null,
    role: localStorage.getItem('userRole') || null,
    username: localStorage.getItem('username') || null,
    userId: userIdStr ? parseInt(userIdStr, 10) : null,
    fullName: localStorage.getItem('fullName') || '',
    resources: [],
    devices: [],
    reservations: [],
    history: [],
    stats: null,
    users: [],
    audit: [],
  };

  const dom = {};
  const headers = (json = true) => {
    const h = {};
    if (json) h['Content-Type'] = 'application/json';
    if (state.token) h.Authorization = `Bearer ${state.token}`;
    return h;
  };

  const request = async (path, options = {}) => {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    if (response.status === 401) throw new Error('unauthorized');
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || response.statusText || 'Erro na requisicao');
    }
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) return response.json();
    return response;
  };

  const api = {
    login: (username, password) => request('/login', { method: 'POST', headers: headers(), body: JSON.stringify({ username, password }) }),
    resources: () => request('/resources', { headers: headers(false) }),
    resource: (id) => request(`/resources/${id}`, { headers: headers(false) }),
    createResource: (payload) => request('/resources', { method: 'POST', headers: headers(), body: JSON.stringify(payload) }),
    updateResource: (id, payload) => request(`/resources/${id}`, { method: 'PUT', headers: headers(), body: JSON.stringify(payload) }),
    deleteResource: (id) => request(`/resources/${id}`, { method: 'DELETE', headers: headers(false) }),
    reserve: (id, payload) => request(`/resources/${id}/reserve`, { method: 'POST', headers: headers(), body: JSON.stringify(payload) }),
    release: (id, payload) => request(`/resources/${id}/release`, { method: 'POST', headers: headers(), body: JSON.stringify(payload) }),
    devices: () => request('/devices', { headers: headers(false) }),
    createDevice: (payload) => request('/devices', { method: 'POST', headers: headers(), body: JSON.stringify(payload) }),
    updateDevice: (id, payload) => request(`/devices/${id}`, { method: 'PUT', headers: headers(), body: JSON.stringify(payload) }),
    deleteDevice: (id) => request(`/devices/${id}`, { method: 'DELETE', headers: headers(false) }),
    reservations: (params = {}) => {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') query.append(key, value);
      });
      return request(`/reservations${query.toString() ? `?${query.toString()}` : ''}`, { headers: headers(false) });
    },
    stats: () => request('/reservations/stats/summary', { headers: headers(false) }),
    audit: () => request('/audit-logs', { headers: headers(false) }),
    users: () => request('/users', { headers: headers(false) }),
    createUser: (payload) => request('/users', { method: 'POST', headers: headers(), body: JSON.stringify(payload) }),
    updatePermissions: (id, resourceIds) => request(`/users/${id}/permissions`, { method: 'PUT', headers: headers(), body: JSON.stringify({ resource_ids: resourceIds }) }),
    deleteUser: (id) => request(`/users/${id}`, { method: 'DELETE', headers: headers(false) }),
    exportReservations: (format) => request(`/reservations/export?format=${format}`, { headers: headers(false) }),
  };
  const formatDate = (value) => {
    if (!value) return '-';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  };

  const statusBadge = (status) => {
    switch (status) {
      case 'active': return 'bg-success';
      case 'completed': return 'bg-secondary';
      case 'expired': return 'bg-warning text-dark';
      case 'cancelled': return 'bg-danger';
      case 'scheduled': return 'bg-info text-dark';
      default: return 'bg-light text-dark';
    }
  };

  const cacheDom = () => {
    dom.loginPage = document.getElementById('loginPage');
    dom.dashboardPage = document.getElementById('dashboardPage');
    dom.logoutBtn = document.getElementById('logoutBtn');
    dom.userInfo = document.getElementById('userInfo');
    dom.usernameDisplay = document.getElementById('usernameDisplay');
    dom.userRoleChip = document.getElementById('userRoleChip');
    dom.resourcesList = document.getElementById('resourcesList');
    dom.devicesList = document.getElementById('devicesList');
    dom.activeReservations = document.getElementById('activeReservations');
    dom.historyTable = document.querySelector('#historyTable tbody');
    dom.adminResourcesTable = document.querySelector('#adminResourcesTable tbody');
    dom.adminDevicesTable = document.querySelector('#adminDevicesTable tbody');
    dom.adminUsersTable = document.querySelector('#adminUsersTable tbody');
    dom.adminReservationsTable = document.querySelector('#adminReservationsTable tbody');
    dom.auditTable = document.querySelector('#auditLogsTable tbody');
    dom.userDashboard = document.getElementById('userDashboard');
    dom.adminDashboard = document.getElementById('adminDashboard');
    dom.statsCards = document.getElementById('statsCards');
    dom.userMetrics = document.getElementById('userMetrics');
  };
  const showLogin = () => {
    dom.loginPage?.classList.remove('d-none');
    dom.dashboardPage?.classList.add('d-none');
    dom.logoutBtn?.classList.add('d-none');
    dom.userInfo?.classList.add('d-none');
  };

  const showDashboard = () => {
    dom.loginPage?.classList.add('d-none');
    dom.dashboardPage?.classList.remove('d-none');
    dom.logoutBtn?.classList.remove('d-none');
    dom.userInfo?.classList.remove('d-none');
    if (dom.usernameDisplay) dom.usernameDisplay.textContent = state.fullName || state.username || '';
    if (dom.userRoleChip) dom.userRoleChip.textContent = state.role === 'admin' ? 'Administrador' : 'Usuario';
    if (state.role === 'admin') dom.adminDashboard?.classList.remove('d-none');
    else dom.adminDashboard?.classList.add('d-none');
  };
  const renderResources = () => {
    if (!dom.resourcesList) return;
    const searchValue = (document.getElementById('resourceSearch')?.value || '').toLowerCase();
    const typeValue = document.getElementById('resourceTypeFilter')?.value || '';
    const filtered = state.resources.filter((resource) => {
      const matchesSearch = resource.name.toLowerCase().includes(searchValue) || (resource.description || '').toLowerCase().includes(searchValue);
      const matchesType = !typeValue || resource.type === typeValue;
      return matchesSearch && matchesType;
    });
    if (!filtered.length) {
      dom.resourcesList.innerHTML = '<p class="text-muted mb-0">Nenhum recurso encontrado</p>';
      return;
    }
    dom.resourcesList.innerHTML = filtered.map((resource) => {
      const statusClass = resource.status === 'available' ? 'bg-success' : resource.status === 'reserved' ? 'bg-danger' : 'bg-warning';
      const statusText = resource.status === 'available' ? 'Disponivel' : resource.status === 'reserved' ? 'Reservado' : 'Manutencao';
      const availableUsers = Array.isArray(state.users) ? state.users : [];
      const userOptions = availableUsers
        .filter((user) => user.id !== state.userId)
        .map((user) => `<option value="${user.id}">${user.full_name || user.username}</option>`)
        .join('');
      const adminSelector = state.role === 'admin'
        ? `
          <div class="mb-3">
            <label class="form-label small mb-1" for="reserve-user-${resource.id}">Reservar para</label>
            <select class="form-select form-select-sm admin-reserve-select" data-resource="${resource.id}" id="reserve-user-${resource.id}">
              <option value="">Eu (${state.username || 'admin'})</option>
              ${userOptions}
            </select>
          </div>`
        : '';
      return `
        <div class="resource-card shadow-sm">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
              <h5 class="mb-1">${resource.name}</h5>
              <p class="text-muted small mb-0">${resource.description || 'Sem descricao'}</p>
            </div>
            <span class="badge ${statusClass} text-white">${statusText}</span>
          </div>
          <div class="row small text-muted mb-3">
            <div class="col">Tipo: <strong>${resource.type || '-'}</strong></div>
            <div class="col">Localizacao: <strong>${resource.location || '-'}</strong></div>
            <div class="col">Capacidade: <strong>${resource.capacity || '-'}</strong></div>
          </div>
          ${adminSelector}
          <div class="d-flex flex-wrap gap-2 align-items-center">
            <button class="btn btn-sm btn-success" data-action="reserve" data-id="${resource.id}" aria-label="Reservar recurso ${resource.name}" ${resource.status !== 'available' ? 'disabled' : ''}>Reservar</button>
            <button class="btn btn-sm btn-outline-secondary" data-action="release" data-id="${resource.id}" aria-label="Liberar recurso ${resource.name}" ${resource.status === 'reserved' ? '' : 'disabled'}>Liberar</button>
          </div>
        </div>
      `;
    }).join('');
    dom.resourcesList.querySelectorAll('button[data-action="reserve"]').forEach((btn) => btn.addEventListener('click', () => promptReservation(parseInt(btn.dataset.id, 10))));
    dom.resourcesList.querySelectorAll('button[data-action="release"]').forEach((btn) => btn.addEventListener('click', () => releaseResource(parseInt(btn.dataset.id, 10))));
  };

  const renderDevices = () => {
    if (!dom.devicesList) return;
    if (!state.devices.length) {
      dom.devicesList.innerHTML = '<p class="text-muted mb-0">Nenhum dispositivo cadastrado</p>';
      return;
    }
    dom.devicesList.innerHTML = state.devices.map((device) => `
      <div class="device-item">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <h6 class="mb-1">${device.name}</h6>
            <p class="text-muted small mb-0">Tipo: ${device.type} | Status: ${device.status}</p>
            <p class="text-muted small mb-0">Recurso: ${device.resource_id || '-'}</p>
          </div>
        </div>
      </div>
    `).join('');
  };

  const renderActiveReservations = () => {
    if (!dom.activeReservations) return;
    const active = state.reservations.filter((item) => item.status === 'active');
    if (!active.length) {
      dom.activeReservations.innerHTML = '<p class="text-muted mb-0">Nenhuma reserva ativa</p>';
      return;
    }
    dom.activeReservations.innerHTML = active.map((item) => `
      <div class="reservation-card">
        <div class="d-flex justify-content-between">
          <div>
            <strong>${item.resource_name || item.resource_id}</strong>
            <p class="text-muted small mb-1">Inicio: ${formatDate(item.start_time)} | Expira: ${formatDate(item.expires_at)}</p>
            <p class="text-muted small mb-0">Usuario: ${item.username || item.user_id}</p>
          </div>
          <button class="btn btn-sm btn-outline-danger" data-res-id="${item.resource_id}" aria-label="Encerrar reserva ${item.resource_name || item.resource_id}">Encerrar</button>
        </div>
      </div>
    `).join('');
    dom.activeReservations.querySelectorAll('button[data-res-id]').forEach((btn) => btn.addEventListener('click', () => releaseResource(parseInt(btn.dataset.resId, 10))));
  };
  const renderReservationTable = (data, tbody, includeActions) => {
    if (!tbody) return;
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="${includeActions ? 7 : 6}" class="text-muted text-center">Sem registros</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map((item) => {
      const base = `
        <td>${item.id}</td>
        <td>${item.resource_name || item.resource_id}</td>
        <td>${item.username || item.user_id}</td>
        <td>${formatDate(item.start_time)}</td>
        <td>${item.end_time ? formatDate(item.end_time) : '-'}</td>
        <td><span class="badge ${statusBadge(item.status)}">${item.status}</span></td>
        <td>${item.notes || '-'}</td>
      `;
      if (!includeActions) return `<tr>${base}</tr>`;
      const action = (item.status === 'active' || item.status === 'scheduled')
        ? `<button class="btn btn-sm btn-outline-danger" data-force-id="${item.resource_id}" aria-label="Forcar termino da reserva ${item.resource_name || item.resource_id}">Forcar termino</button>`
        : '-';
      return `<tr>${base}<td>${action}</td></tr>`;
    }).join('');
    if (includeActions) {
      tbody.querySelectorAll('button[data-force-id]').forEach((btn) => btn.addEventListener('click', () => forceEndReservation(parseInt(btn.dataset.forceId, 10))));
    }
  };

  const renderStats = () => {
    if (!dom.statsCards || !state.stats) return;
    const { reservations, top_resources: topResources, usage_by_day: usage } = state.stats;
    dom.statsCards.innerHTML = `
      <div class="col-md-4"><div class="metric-card"><span>Total de reservas</span><strong>${reservations.total_reservations}</strong></div></div>
      <div class="col-md-4"><div class="metric-card"><span>Reservas ativas</span><strong>${reservations.active_reservations}</strong></div></div>
      <div class="col-md-4"><div class="metric-card"><span>Tempo medio (min)</span><strong>${reservations.average_duration_minutes}</strong></div></div>
    `;
    const chartContainer = document.getElementById('usageChart');
    if (!chartContainer) return;
    const labels = Object.keys(usage || {});
    const values = labels.map((key) => usage[key]);
    if (!window.Chart) return;
    if (window.usageChartInstance) {
      window.usageChartInstance.data.labels = labels;
      window.usageChartInstance.data.datasets[0].data = values;
      window.usageChartInstance.update();
    } else {
      window.usageChartInstance = new Chart(chartContainer, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Reservas por dia',
            data: values,
            borderColor: '#198754',
            backgroundColor: 'rgba(25,135,84,0.2)',
            tension: 0.3,
            fill: true,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
        },
      });
    }
  };

  const renderMetrics = () => {
    if (!dom.userMetrics) return;
    const total = state.resources.length;
    const available = state.resources.filter((item) => item.status === 'available').length;
    const reserved = state.resources.filter((item) => item.status === 'reserved').length;
    dom.userMetrics.innerHTML = `
      <div class="col-md-4"><div class="metric-card"><span>Total de recursos</span><strong>${total}</strong></div></div>
      <div class="col-md-4"><div class="metric-card"><span>Disponiveis</span><strong>${available}</strong></div></div>
      <div class="col-md-4"><div class="metric-card"><span>Reservados</span><strong>${reserved}</strong></div></div>
    `;
  };
  const renderAdminTables = () => {
    if (dom.adminResourcesTable) {
      dom.adminResourcesTable.innerHTML = state.resources.map((resource) => `
        <tr>
          <td>${resource.id}</td>
          <td>${resource.name}</td>
          <td>${resource.status}</td>
          <td>${resource.type || '-'}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary me-2" data-edit-resource="${resource.id}">Editar</button>
            <button class="btn btn-sm btn-outline-danger" data-delete-resource="${resource.id}" aria-label="Remover recurso ${resource.name}">Remover</button>
          </td>
        </tr>
      `).join('');
      dom.adminResourcesTable.querySelectorAll('button[data-delete-resource]').forEach((btn) => btn.addEventListener('click', () => deleteResource(parseInt(btn.dataset.deleteResource, 10))));
      dom.adminResourcesTable.querySelectorAll('button[data-edit-resource]').forEach((btn) => btn.addEventListener('click', () => editResource(parseInt(btn.dataset.editResource, 10))));
    }

    if (dom.adminDevicesTable) {
      dom.adminDevicesTable.innerHTML = state.devices.map((device) => `
        <tr>
          <td>${device.id}</td>
          <td>${device.name}</td>
          <td>${device.status}</td>
          <td>${device.resource_id || '-'}</td>
          <td>
            <button class="btn btn-sm btn-outline-danger" data-delete-device="${device.id}" aria-label="Remover dispositivo ${device.name}">Remover</button>
          </td>
        </tr>
      `).join('');
      dom.adminDevicesTable.querySelectorAll('button[data-delete-device]').forEach((btn) => btn.addEventListener('click', () => deleteDevice(parseInt(btn.dataset.deleteDevice, 10))));
    }

    if (dom.adminUsersTable) {
      dom.adminUsersTable.innerHTML = state.users.map((user) => `
        <tr>
          <td>${user.id}</td>
          <td>${user.username}</td>
          <td>${user.role}</td>
          <td>${user.is_active ? 'Ativo' : 'Inativo'}</td>
          <td>
            <button class="btn btn-sm btn-outline-secondary me-2" data-permission-user="${user.id}" aria-label="Editar permissoes do usuario ${user.username}">Permissoes</button>
            <button class="btn btn-sm btn-outline-danger" data-delete-user="${user.id}" aria-label="Remover usuario ${user.username}">Remover</button>
          </td>
        </tr>
      `).join('');
      dom.adminUsersTable.querySelectorAll('button[data-delete-user]').forEach((btn) => btn.addEventListener('click', () => deleteUser(parseInt(btn.dataset.deleteUser, 10))));
      dom.adminUsersTable.querySelectorAll('button[data-permission-user]').forEach((btn) => btn.addEventListener('click', () => updatePermissionsPrompt(parseInt(btn.dataset.permissionUser, 10))));
    }

    if (dom.auditTable) {
      dom.auditTable.innerHTML = state.audit.map((log) => `
        <tr>
          <td>${formatDate(log.timestamp)}</td>
          <td>${log.user_id || '-'}</td>
          <td>${log.action}</td>
          <td>${log.resource_id || '-'}</td>
          <td>${log.device_id || '-'}</td>
          <td>${log.result}</td>
        </tr>
      `).join('');
      if (!state.audit.length) {
        dom.auditTable.innerHTML = '<tr><td colspan="6" class="text-muted text-center">Nenhum log registrado</td></tr>';
      }
    }
  };
  const promptReservation = async (resourceId) => {
    let selectedUserId = null;
    if (state.role === 'admin' && dom.resourcesList) {
      const selector = dom.resourcesList.querySelector(`select[data-resource="${resourceId}"]`);
      if (selector && selector.value) {
        const parsed = parseInt(selector.value, 10);
        if (!Number.isNaN(parsed)) selectedUserId = parsed;
      }
    }
    const durationInput = prompt('Duracao em minutos', '30');
    if (!durationInput) return;
    const duration = parseInt(durationInput, 10);
    if (Number.isNaN(duration) || duration <= 0) {
      alert('Duracao invalida');
      return;
    }
    try {
      const payload = { duration_minutes: duration };
      if (state.role === 'admin' && selectedUserId) {
        payload.user_id = selectedUserId;
      }
      await api.reserve(resourceId, payload);
      await Promise.all([loadResources(), loadActiveReservations(), loadHistory(), loadStats()]);
    } catch (error) {
      alert(`Falha ao reservar: ${error.message}`);
    }
  };

  const releaseResource = async (resourceId) => {
    try {
      await api.release(resourceId, { notes: 'Liberado pelo usuario' });
      await Promise.all([loadResources(), loadActiveReservations(), loadHistory(), loadStats()]);
    } catch (error) {
      alert(`Falha ao liberar: ${error.message}`);
    }
  };

  const deleteResource = async (resourceId) => {
    if (!confirm('Remover recurso?')) return;
    try {
      await api.deleteResource(resourceId);
      await loadResources();
    } catch (error) {
      alert(`Falha ao remover recurso: ${error.message}`);
    }
  };

  const editResource = (resourceId) => {
    const resource = state.resources.find((item) => item.id === resourceId);
    if (!resource) return;
    const newName = prompt('Nome do recurso', resource.name);
    if (!newName) return;
    const capacity = prompt('Capacidade', resource.capacity || '');
    api.updateResource(resourceId, {
      name: newName,
      capacity: capacity ? parseInt(capacity, 10) : null,
    }).then(loadResources).catch((error) => alert(`Falha ao atualizar recurso: ${error.message}`));
  };

  const deleteDevice = async (deviceId) => {
    if (!confirm('Remover dispositivo?')) return;
    try {
      await api.deleteDevice(deviceId);
      await loadDevices();
    } catch (error) {
      alert(`Falha ao remover dispositivo: ${error.message}`);
    }
  };

  const deleteUser = async (userId) => {
    if (!confirm('Remover usuario?')) return;
    try {
      await api.deleteUser(userId);
      await loadUsers();
    } catch (error) {
      alert(`Falha ao remover usuario: ${error.message}`);
    }
  };

  const updatePermissionsPrompt = async (userId) => {
    const user = state.users.find((item) => item.id === userId);
    if (!user) return;
    const current = (user.permitted_resource_ids || []).join(',');
    const input = prompt('IDs de recursos permitidos separados por virgula', current);
    if (input === null) return;
    const ids = input.split(',').map((value) => parseInt(value.trim(), 10)).filter((value) => !Number.isNaN(value));
    try {
      await api.updatePermissions(userId, ids);
      await loadUsers();
    } catch (error) {
      alert(`Falha ao atualizar permissoes: ${error.message}`);
    }
  };

  const forceEndReservation = async (resourceId) => {
    try {
      await api.release(resourceId, { notes: 'Liberado pelo admin', force: true });
      await Promise.all([loadResources(), loadActiveReservations(), loadHistory(), loadAdminReservations(), loadStats()]);
    } catch (error) {
      alert(`Falha ao encerrar reserva: ${error.message}`);
    }
  };

  const exportReservations = async (format) => {
    try {
      const response = await api.exportReservations(format);
      if (response instanceof Response) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = format === 'pdf' ? 'reservas.pdf' : 'reservas.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      alert(`Falha ao exportar: ${error.message}`);
    }
  };
  const loadResources = async () => {
    try {
      const resources = await api.resources();
      state.resources = resources;
      renderResources();
      renderMetrics();
      renderAdminTables();
      populateTypeFilter();
    } catch (error) {
      console.error('Falha ao carregar recursos', error);
    }
  };

  const loadDevices = async () => {
    try {
      state.devices = await api.devices();
      renderDevices();
      renderAdminTables();
    } catch (error) {
      console.error('Falha ao carregar dispositivos', error);
    }
  };

  const loadActiveReservations = async () => {
    try {
      const params = state.role === 'admin' ? { status: 'active' } : { status: 'active', user_id: state.userId };
      state.reservations = await api.reservations(params);
      renderActiveReservations();
    } catch (error) {
      console.error('Falha ao carregar reservas', error);
    }
  };

  const loadHistory = async () => {
    try {
      const start = document.getElementById('historyStart')?.value;
      const end = document.getElementById('historyEnd')?.value;
      const params = {};
      if (start) params.start_from = `${start}T00:00:00`;
      if (end) params.start_to = `${end}T23:59:59`;
      if (state.role !== 'admin') params.user_id = state.userId;
      const history = await api.reservations(params);
      state.history = history;
      renderReservationTable(history, dom.historyTable, false);
    } catch (error) {
      console.error('Falha ao carregar historico', error);
    }
  };

  const loadAdminReservations = async () => {
    if (state.role !== 'admin') return;
    try {
      const statusValue = document.getElementById('adminReservationStatus')?.value;
      const params = {};
      if (statusValue) params.status = statusValue;
      const reservations = await api.reservations(params);
      renderReservationTable(reservations, dom.adminReservationsTable, true);
    } catch (error) {
      console.error('Falha ao carregar reservas admin', error);
    }
  };

  const loadStats = async () => {
    try {
      state.stats = await api.stats();
      renderStats();
    } catch (error) {
      console.error('Falha ao carregar estatisticas', error);
    }
  };

  const loadUsers = async () => {
    if (state.role !== 'admin') return;
    try {
      state.users = await api.users();
      renderAdminTables();
    } catch (error) {
      console.error('Falha ao carregar usuarios', error);
    }
  };

  const loadAudit = async () => {
    if (state.role !== 'admin') return;
    try {
      state.audit = await api.audit();
      renderAdminTables();
    } catch (error) {
      console.error('Falha ao carregar auditoria', error);
    }
  };
  const populateTypeFilter = () => {
    const select = document.getElementById('resourceTypeFilter');
    if (!select) return;
    const types = Array.from(new Set(state.resources.map((item) => item.type || '')));
    select.innerHTML = ['<option value="">Todos</option>', ...types.filter(Boolean).map((type) => `<option value="${type}">${type}</option>`)].join('');
  };
  const setupEventListeners = () => {
    document.getElementById('loginForm')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const username = document.getElementById('username')?.value.trim();
      const password = document.getElementById('password')?.value.trim();
      const loginError = document.getElementById('loginError');
      if (!username || !password) return;
      try {
        const data = await api.login(username, password);
        state.token = data.token;
        state.role = data.role;
        state.username = data.username;
        state.userId = data.user_id;
        state.fullName = data.full_name || '';
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('userRole', data.role);
        localStorage.setItem('username', data.username);
        localStorage.setItem('userId', String(data.user_id));
        localStorage.setItem('fullName', state.fullName);
        dom.usernameDisplay.textContent = state.fullName || state.username || '';
        dom.userRoleChip.textContent = state.role === 'admin' ? 'Administrador' : 'Usuario';
        showDashboard();
        await loadAll();
        connectWebSocket();
        loginError?.classList.add('d-none');
      } catch (error) {
        if (loginError) {
          loginError.textContent = error.message || 'Falha no login';
          loginError.classList.remove('d-none');
        }
      }
    });

    dom.logoutBtn?.addEventListener('click', () => {
      localStorage.clear();
      state.token = null;
      state.role = null;
      state.username = null;
      state.userId = null;
      showLogin();
    });

    document.getElementById('resourceForm')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const name = document.getElementById('resourceName')?.value.trim();
      if (!name) return;
      const payload = {
        name,
        description: document.getElementById('resourceDescription')?.value.trim(),
        type: document.getElementById('resourceType')?.value.trim(),
        location: document.getElementById('resourceLocation')?.value.trim(),
        capacity: document.getElementById('resourceCapacity')?.value ? parseInt(document.getElementById('resourceCapacity').value, 10) : null,
      };
      try {
        await api.createResource(payload);
        ['resourceName','resourceDescription','resourceType','resourceLocation','resourceCapacity'].forEach((id) => {
          const input = document.getElementById(id);
          if (input) input.value = '';
        });
        await loadResources();
      } catch (error) {
        alert(`Falha ao criar recurso: ${error.message}`);
      }
    });

    document.getElementById('deviceForm')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const name = document.getElementById('deviceName')?.value.trim();
      if (!name) return;
      try {
        await api.createDevice({
          name,
          type: document.getElementById('deviceType')?.value || 'other',
          resource_id: document.getElementById('deviceResourceId')?.value ? parseInt(document.getElementById('deviceResourceId').value, 10) : null,
          status: 'inactive',
        });
        ['deviceName','deviceResourceId'].forEach((id) => { const input = document.getElementById(id); if (input) input.value = ''; });
        await loadDevices();
      } catch (error) {
        alert(`Falha ao criar dispositivo: ${error.message}`);
      }
    });

    document.getElementById('userForm')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const username = document.getElementById('userUsername')?.value.trim();
      const password = document.getElementById('userPassword')?.value;
      if (!username || !password) return;
      const allowed = (document.getElementById('userResourceIds')?.value || '')
        .split(',')
        .map((value) => parseInt(value.trim(), 10))
        .filter((value) => !Number.isNaN(value));
      try {
        await api.createUser({
          username,
          password,
          full_name: document.getElementById('userFullName')?.value.trim(),
          email: document.getElementById('userEmail')?.value.trim(),
          role: document.getElementById('userRoleSelect')?.value || 'user',
          allowed_resource_ids: allowed,
        });
        ['userUsername','userPassword','userFullName','userEmail','userResourceIds'].forEach((id) => { const input = document.getElementById(id); if (input) input.value = ''; });
        await loadUsers();
      } catch (error) {
        alert(`Falha ao criar usuario: ${error.message}`);
      }
    });

    document.getElementById('historyFilterBtn')?.addEventListener('click', loadHistory);
    document.getElementById('refreshStatsBtn')?.addEventListener('click', loadStats);
    document.getElementById('adminReservationFilterBtn')?.addEventListener('click', loadAdminReservations);
    document.getElementById('refreshAuditBtn')?.addEventListener('click', loadAudit);
    document.getElementById('exportCsvBtn')?.addEventListener('click', () => exportReservations('csv'));
    document.getElementById('exportPdfBtn')?.addEventListener('click', () => exportReservations('pdf'));
    document.getElementById('resourceSearch')?.addEventListener('input', renderResources);
    document.getElementById('resourceTypeFilter')?.addEventListener('change', renderResources);
  };
  let ws = null;
  const connectWebSocket = () => {
    if (ws) ws.close();
    ws = new WebSocket(API_BASE_URL.replace('http', 'ws') + '/ws/updates');
    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        if (!data || !data.type) return;
        switch (data.type) {
          case 'resource.updated':
          case 'resource.created':
            await syncResource(data.resourceId);
            break;
          case 'resource.deleted':
            state.resources = state.resources.filter((item) => item.id !== data.resourceId);
            renderResources();
            renderMetrics();
            renderAdminTables();
            break;
          case 'device.updated':
          case 'device.created':
          case 'device.deleted':
            await loadDevices();
            break;
          case 'reservation.created':
          case 'reservation.updated':
            await Promise.all([loadResources(), loadActiveReservations(), loadHistory(), loadStats()]);
            if (state.role === 'admin') await loadAdminReservations();
            break;
          default:
            break;
        }
      } catch (error) {
        console.error('Mensagem websocket invalida', error);
      }
    };
    ws.onclose = () => {
      if (state.token) setTimeout(connectWebSocket, 5000);
    };
  };

  const syncResource = async (resourceId) => {
    if (!resourceId) return;
    try {
      const resource = await api.resource(resourceId);
      const index = state.resources.findIndex((item) => item.id === resourceId);
      if (index >= 0) state.resources[index] = resource;
      else state.resources.push(resource);
      renderResources();
      renderMetrics();
      renderAdminTables();
    } catch (error) {
      console.error('Falha ao sincronizar recurso', error);
    }
  };

  const loadAll = async () => {
    await Promise.all([loadResources(), loadDevices(), loadActiveReservations(), loadHistory(), loadStats()]);
    if (state.role === 'admin') {
      await Promise.all([loadUsers(), loadAdminReservations(), loadAudit()]);
    }
  };

  const init = async () => {
    cacheDom();
    setupEventListeners();
    if (state.token && state.role && state.userId) {
      showDashboard();
      await loadAll();
      connectWebSocket();
    } else {
      showLogin();
    }
  };

  document.addEventListener('DOMContentLoaded', init);
})();
