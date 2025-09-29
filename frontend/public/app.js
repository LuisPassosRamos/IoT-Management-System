
// IoT Management System - Frontend Application
class IoTApp {
  constructor() {
    this.apiUrl = 'http://localhost:8000';
    this.token = localStorage.getItem('authToken');
    this.userRole = localStorage.getItem('userRole');
    this.username = localStorage.getItem('username');
    const storedUserId = localStorage.getItem('userId');
    this.userId = storedUserId ? parseInt(storedUserId, 10) : null;

    this.resourcesCache = [];
    this.devicesCache = [];
    this.reservationsCache = [];
    this.editingResourceId = null;
    this.editingDeviceId = null;

    this.init();
  }
  init() {
    this.setupEventListeners();
    this.setupAdminFormListeners();

    if (this.token && this.userRole && this.username && this.userId) {
      this.showDashboard();
    } else {
      this.showLogin();
    }
  }

  setupEventListeners() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        this.handleLogin();
      });
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => this.handleLogout());
    }

    setInterval(() => {
      const dashboard = document.getElementById('dashboardPage');
      if (this.token && dashboard && dashboard.style.display !== 'none') {
        this.loadDashboardData();
      }
    }, 10000);
  }

  setupAdminFormListeners() {
    const resourceForm = document.getElementById('resourceForm');
    if (resourceForm) {
      resourceForm.addEventListener('submit', (event) => {
        event.preventDefault();
        this.handleResourceFormSubmit();
      });
    }

    const resourceCancel = document.getElementById('resourceFormCancel');
    if (resourceCancel) {
      resourceCancel.addEventListener('click', () => this.resetResourceForm());
    }

    const deviceForm = document.getElementById('deviceForm');
    if (deviceForm) {
      deviceForm.addEventListener('submit', (event) => {
        event.preventDefault();
        this.handleDeviceFormSubmit();
      });
    }

    const deviceCancel = document.getElementById('deviceFormCancel');
    if (deviceCancel) {
      deviceCancel.addEventListener('click', () => this.resetDeviceForm());
    }
  }

  focusAdminTab(tabName) {
    const tabButton = document.querySelector(`#${tabName}-tab`);
    if (!tabButton) {
      return;
    }
    if (window.bootstrap && window.bootstrap.Tab) {
      const tab = new window.bootstrap.Tab(tabButton);
      tab.show();
    } else {
      tabButton.click();
    }
  }

  async handleLogin() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const username = usernameInput ? usernameInput.value : '';
    const password = passwordInput ? passwordInput.value : '';

    try {
      const response = await fetch(`${this.apiUrl}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        this.showError(error.detail || 'Credenciais invalidas. Tente novamente.');
        return;
      }

      const data = await response.json();
      this.token = data.token;
      this.userRole = data.role;
      this.username = data.username;
      this.userId = data.user_id;

      localStorage.setItem('authToken', this.token);
      localStorage.setItem('userRole', this.userRole);
      localStorage.setItem('username', this.username);
      localStorage.setItem('userId', String(this.userId));

      this.showMessage('Login realizado com sucesso!', 'success');
      this.showDashboard();
    } catch (error) {
      console.error('Login error:', error);
      this.showError('Erro de conexao. Verifique se o servidor esta rodando.');
    }
  }

  handleLogout() {
    this.token = null;
    this.userRole = null;
    this.username = null;
    this.userId = null;

    localStorage.removeItem('authToken');
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');
    localStorage.removeItem('userId');

    this.resetResourceForm();
    this.resetDeviceForm();

    this.showLogin();
    this.showMessage('Logout realizado com sucesso!', 'success');
  }

  showLogin() {
    const loginPage = document.getElementById('loginPage');
    if (loginPage) loginPage.style.display = 'block';
    const dashboardPage = document.getElementById('dashboardPage');
    if (dashboardPage) dashboardPage.style.display = 'none';
    const userInfo = document.getElementById('userInfo');
    if (userInfo) userInfo.style.display = 'none';
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.style.display = 'none';

    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.reset();
    const loginError = document.getElementById('loginError');
    if (loginError) loginError.style.display = 'none';
  }

  showDashboard() {
    const loginPage = document.getElementById('loginPage');
    if (loginPage) loginPage.style.display = 'none';
    const dashboardPage = document.getElementById('dashboardPage');
    if (dashboardPage) dashboardPage.style.display = 'block';
    const userInfo = document.getElementById('userInfo');
    if (userInfo) userInfo.style.display = 'block';
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.style.display = 'block';

    const usernameDisplay = document.getElementById('usernameDisplay');
    if (usernameDisplay) usernameDisplay.textContent = this.username || '';

    const loginError = document.getElementById('loginError');
    if (loginError) loginError.style.display = 'none';

    const userDashboard = document.getElementById('userDashboard');
    const adminDashboard = document.getElementById('adminDashboard');

    if (this.userRole === 'admin') {
      if (userDashboard) userDashboard.style.display = 'none';
      if (adminDashboard) adminDashboard.style.display = 'block';
    } else {
      if (userDashboard) userDashboard.style.display = 'block';
      if (adminDashboard) adminDashboard.style.display = 'none';
    }

    this.loadDashboardData();
  }
  async apiRequest(endpoint, method = 'GET', body = null) {
    const headers = {};
    if (body !== null) {
      headers['Content-Type'] = 'application/json';
    }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const options = { method, headers };
    if (body !== null) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.apiUrl}${endpoint}`, options);

    if (response.status === 401) {
      this.handleLogout();
      throw new Error('Authentication required');
    }

    return response;
  }

  async loadDashboardData() {
    try {
      const tasks = [this.loadResources(), this.loadDevices()];
      if (this.userRole === 'admin') {
        tasks.push(this.loadReservations());
      }
      await Promise.all(tasks);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  }

  async loadResources() {
    try {
      const response = await this.apiRequest('/resources');
      if (!response.ok) {
        throw new Error('Failed to load resources');
      }
      const resources = await response.json();
      this.resourcesCache = resources;
      if (this.userRole === 'admin') {
        this.renderAdminResources(resources);
      } else {
        this.renderUserResources(resources);
      }
    } catch (error) {
      console.error('Error loading resources:', error);
    }
  }

  async loadDevices() {
    try {
      const response = await this.apiRequest('/devices');
      if (!response.ok) {
        throw new Error('Failed to load devices');
      }
      const devices = await response.json();
      this.devicesCache = devices;
      if (this.userRole === 'admin') {
        this.renderAdminDevices(devices);
      } else {
        this.renderUserDevices(devices);
      }
    } catch (error) {
      console.error('Error loading devices:', error);
    }
  }

  async loadReservations() {
    if (this.userRole !== 'admin') {
      return;
    }
    try {
      const response = await this.apiRequest('/reservations');
      if (!response.ok) {
        throw new Error('Failed to load reservations');
      }
      const reservations = await response.json();
      this.reservationsCache = reservations;
      this.renderAdminReservations(reservations);
    } catch (error) {
      console.error('Error loading reservations:', error);
    }
  }
  renderUserResources(resources) {
    const container = document.getElementById('resourcesList');
    if (!container) {
      return;
    }

    if (resources.length === 0) {
      container.innerHTML = '<p class="text-muted">Nenhum recurso disponivel.</p>';
      return;
    }

    container.innerHTML = resources.map((resource) => `
      <div class="resource-card p-3 ${resource.available ? 'resource-available' : 'resource-reserved'}">
        <div class="row align-items-center">
          <div class="col-md-8">
            <h6 class="mb-1">${resource.name}</h6>
            <p class="text-muted mb-1">${resource.description}</p>
            <span class="badge ${resource.available ? 'bg-success' : 'bg-danger'}">
              ${resource.available ? 'Disponivel' : 'Reservado'}
            </span>
          </div>
          <div class="col-md-4 text-end">
            ${this.renderResourceActions(resource)}
          </div>
        </div>
      </div>
    `).join('');
  }

  renderResourceActions(resource) {
    if (resource.available) {
      return `<button class="btn btn-success btn-sm" onclick="app.reserveResource(${resource.id})">Reservar</button>`;
    }
    if (resource.reserved_by === this.userId) {
      return `<button class="btn btn-outline-success btn-sm" onclick="app.releaseResource(${resource.id})">Liberar</button>`;
    }
    return '<span class="text-muted">Indisponivel</span>';
  }

  renderUserDevices(devices) {
    const container = document.getElementById('devicesList');
    if (!container) {
      return;
    }

    if (devices.length === 0) {
      container.innerHTML = '<p class="text-muted">Nenhum dispositivo encontrado.</p>';
      return;
    }

    container.innerHTML = `
      <div class="row">
        ${devices.map((device) => `
          <div class="col-md-6 mb-3">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">${device.name}</h6>
                <p class="card-text">
                  <span class="device-status ${device.status}">${this.getStatusText(device)}</span>
                </p>
                ${device.value !== undefined && device.value !== null ? `<p class="card-text"><small class="text-muted">Valor: ${device.value}</small></p>` : ''}
                <div>${this.renderDeviceActions(device)}</div>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  renderDeviceActions(device) {
    const actions = [];
    if (device.type === 'lock') {
      actions.push(
        `<button class="btn btn-outline-success btn-sm me-2" onclick="app.executeDeviceAction(${device.id}, 'unlock')">Destrancar</button>`,
        `<button class="btn btn-outline-secondary btn-sm me-2" onclick="app.executeDeviceAction(${device.id}, 'lock')">Trancar</button>`
      );
    } else if (device.type === 'sensor') {
      actions.push(
        `<button class="btn btn-outline-success btn-sm me-2" onclick="app.executeDeviceAction(${device.id}, 'read')">Ler sensor</button>`,
        `<button class="btn btn-outline-secondary btn-sm me-2" onclick="app.executeDeviceAction(${device.id}, 'activate')">Ativar</button>`
      );
    }
    actions.push(`<button class="btn btn-outline-info btn-sm" onclick="app.viewDeviceDetails(${device.id})">Detalhes</button>`);
    return actions.join('');
  }
  renderAdminResources(resources) {
    const container = document.getElementById('adminResourcesList');
    if (!container) {
      return;
    }

    if (resources.length === 0) {
      container.innerHTML = '<p class="text-muted mb-0">Nenhum recurso cadastrado.</p>';
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table class="table table-striped align-middle">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>Descricao</th>
              <th>Status</th>
              <th>Reservado por</th>
              <th>Dispositivo</th>
              <th>Acoes</th>
            </tr>
          </thead>
          <tbody>
            ${resources.map((resource) => `
              <tr>
                <td>${resource.id}</td>
                <td>${resource.name}</td>
                <td>${resource.description}</td>
                <td>
                  <span class="badge ${resource.available ? 'bg-success' : 'bg-danger'}">
                    ${resource.available ? 'Disponivel' : 'Reservado'}
                  </span>
                </td>
                <td>${resource.reserved_by ?? '-'}</td>
                <td>${resource.device_id ?? '-'}</td>
                <td>${this.renderAdminResourceActions(resource)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  renderAdminResourceActions(resource) {
    const actions = [
      `<button class="btn btn-sm btn-outline-primary me-2" onclick="app.startResourceEdit(${resource.id})">Editar</button>`,
      `<button class="btn btn-sm btn-outline-danger me-2" onclick="app.deleteResource(${resource.id})">Excluir</button>`
    ];
    if (!resource.available) {
      actions.push(`<button class="btn btn-sm btn-outline-warning" onclick="app.adminReleaseResource(${resource.id})">Forcar liberacao</button>`);
    } else {
      actions.push('<span class="text-muted">Disponivel</span>');
    }
    return actions.join(' ');
  }

  renderAdminDevices(devices) {
    const container = document.getElementById('adminDevicesList');
    if (!container) {
      return;
    }

    if (devices.length === 0) {
      container.innerHTML = '<p class="text-muted mb-0">Nenhum dispositivo cadastrado.</p>';
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table class="table table-striped align-middle">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>Tipo</th>
              <th>Status</th>
              <th>Valor</th>
              <th>Recurso</th>
              <th>Acoes</th>
            </tr>
          </thead>
          <tbody>
            ${devices.map((device) => `
              <tr>
                <td>${device.id}</td>
                <td>${device.name}</td>
                <td>${device.type}</td>
                <td><span class="device-status ${device.status}">${this.getStatusText(device)}</span></td>
                <td>${device.value !== undefined && device.value !== null ? device.value : '-'}</td>
                <td>${device.resource_id ?? '-'}</td>
                <td>${this.renderAdminDeviceActions(device)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  renderAdminDeviceActions(device) {
    return `
      <button class="btn btn-sm btn-outline-primary me-2" onclick="app.startDeviceEdit(${device.id})">Editar</button>
      <button class="btn btn-sm btn-outline-danger me-2" onclick="app.deleteDevice(${device.id})">Excluir</button>
      <button class="btn btn-sm btn-outline-info" onclick="app.viewDeviceDetails(${device.id})">Detalhes</button>
    `;
  }

  renderAdminReservations(reservations) {
    const container = document.getElementById('adminReservationsList');
    if (!container) {
      return;
    }

    if (reservations.length === 0) {
      container.innerHTML = '<p class="text-muted mb-0">Nenhuma reserva cadastrada.</p>';
      return;
    }

    container.innerHTML = `
      <div class="table-responsive">
        <table class="table table-striped align-middle">
          <thead>
            <tr>
              <th>ID</th>
              <th>Recurso</th>
              <th>Usuario</th>
              <th>Status</th>
              <th>Criada em</th>
              <th>Acoes</th>
            </tr>
          </thead>
          <tbody>
            ${reservations.map((reservation) => `
              <tr>
                <td>${reservation.id}</td>
                <td>${reservation.resource_name || reservation.resource_id}</td>
                <td>${reservation.username || reservation.user_id}</td>
                <td>${this.renderReservationStatusBadge(reservation.status)}</td>
                <td>${this.formatTimestamp(reservation.timestamp)}</td>
                <td>${this.renderReservationActions(reservation)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }
  renderReservationStatusBadge(status) {
    const badges = {
      active: { className: 'bg-warning text-dark', label: 'Ativa' },
      completed: { className: 'bg-success', label: 'Concluida' },
      cancelled: { className: 'bg-secondary', label: 'Cancelada' }
    };
    const badge = badges[status] || { className: 'bg-light text-dark', label: status };
    return `<span class="badge ${badge.className}">${badge.label}</span>`;
  }

  renderReservationActions(reservation) {
    const actions = [];
    if (reservation.status !== 'cancelled') {
      actions.push(`<button class="btn btn-sm btn-outline-warning me-2" onclick="app.updateReservationStatus(${reservation.id}, 'cancelled')">Cancelar</button>`);
    }
    if (reservation.status !== 'completed') {
      actions.push(`<button class="btn btn-sm btn-outline-success me-2" onclick="app.updateReservationStatus(${reservation.id}, 'completed')">Concluir</button>`);
    }
    actions.push(`<button class="btn btn-sm btn-outline-danger" onclick="app.deleteReservation(${reservation.id})">Remover</button>`);
    return actions.join(' ');
  }

  formatTimestamp(timestamp) {
    if (!timestamp) {
      return '-';
    }
    try {
      const date = new Date(timestamp);
      if (Number.isNaN(date.getTime())) {
        return timestamp;
      }
      return date.toLocaleString();
    } catch (error) {
      return timestamp;
    }
  }
  async handleResourceFormSubmit() {
    const nameInput = document.getElementById('resourceName');
    const descriptionInput = document.getElementById('resourceDescription');
    const deviceIdInput = document.getElementById('resourceDeviceId');

    const payload = {
      name: nameInput ? nameInput.value.trim() : '',
      description: descriptionInput ? descriptionInput.value.trim() : ''
    };

    const deviceIdRaw = deviceIdInput ? deviceIdInput.value.trim() : '';
    if (deviceIdRaw !== '') {
      payload.device_id = parseInt(deviceIdRaw, 10);
    } else if (this.editingResourceId !== null) {
      payload.device_id = null;
    }

    try {
      let response;
      if (this.editingResourceId !== null) {
        response = await this.apiRequest(`/resources/${this.editingResourceId}`, 'PUT', payload);
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.detail || 'Erro ao atualizar recurso');
        }
        this.showMessage('Recurso atualizado com sucesso!', 'success');
      } else {
        response = await this.apiRequest('/resources', 'POST', payload);
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.detail || 'Erro ao criar recurso');
        }
        this.showMessage('Recurso criado com sucesso!', 'success');
      }

      this.resetResourceForm();
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error saving resource:', error);
      this.showError(error.message || 'Erro ao salvar recurso');
    }
  }

  startResourceEdit(resourceId) {
    const resource = this.resourcesCache.find((item) => item.id === resourceId);
    if (!resource) {
      return;
    }
    this.editingResourceId = resourceId;

    const title = document.getElementById('resourceFormTitle');
    if (title) {
      title.textContent = 'Editar recurso';
    }
    const submitBtn = document.getElementById('resourceFormSubmit');
    if (submitBtn) {
      submitBtn.textContent = 'Salvar recurso';
    }
    const cancelBtn = document.getElementById('resourceFormCancel');
    if (cancelBtn) {
      cancelBtn.style.display = 'inline-block';
    }

    const nameInput = document.getElementById('resourceName');
    if (nameInput) {
      nameInput.value = resource.name || '';
    }
    const descriptionInput = document.getElementById('resourceDescription');
    if (descriptionInput) {
      descriptionInput.value = resource.description || '';
    }
    const deviceIdInput = document.getElementById('resourceDeviceId');
    if (deviceIdInput) {
      deviceIdInput.value = resource.device_id ?? '';
    }

    this.focusAdminTab('resources');
  }

  resetResourceForm() {
    const form = document.getElementById('resourceForm');
    if (form) {
      form.reset();
    }
    this.editingResourceId = null;

    const title = document.getElementById('resourceFormTitle');
    if (title) {
      title.textContent = 'Cadastrar recurso';
    }
    const submitBtn = document.getElementById('resourceFormSubmit');
    if (submitBtn) {
      submitBtn.textContent = 'Adicionar recurso';
    }
    const cancelBtn = document.getElementById('resourceFormCancel');
    if (cancelBtn) {
      cancelBtn.style.display = 'none';
    }
  }

  async deleteResource(resourceId) {
    if (!confirm('Deseja excluir este recurso?')) {
      return;
    }
    try {
      const response = await this.apiRequest(`/resources/${resourceId}`, 'DELETE');
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao excluir recurso');
      }
      this.showMessage('Recurso excluido com sucesso!', 'success');
      if (this.editingResourceId === resourceId) {
        this.resetResourceForm();
      }
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error deleting resource:', error);
      this.showError(error.message || 'Erro ao excluir recurso');
    }
  }
  async handleDeviceFormSubmit() {
    const nameInput = document.getElementById('deviceName');
    const typeInput = document.getElementById('deviceType');
    const statusInput = document.getElementById('deviceStatus');
    const resourceIdInput = document.getElementById('deviceResourceId');
    const valueInput = document.getElementById('deviceValue');

    const payload = {
      name: nameInput ? nameInput.value.trim() : '',
      type: typeInput ? typeInput.value : 'lock',
      status: statusInput ? statusInput.value : 'inactive'
    };

    const resourceIdRaw = resourceIdInput ? resourceIdInput.value.trim() : '';
    if (resourceIdRaw !== '') {
      payload.resource_id = parseInt(resourceIdRaw, 10);
    } else if (this.editingDeviceId !== null) {
      payload.resource_id = null;
    }

    const valueRaw = valueInput ? valueInput.value.trim() : '';
    if (valueRaw !== '') {
      payload.value = parseFloat(valueRaw);
    } else if (this.editingDeviceId !== null) {
      payload.value = null;
    }

    try {
      let response;
      if (this.editingDeviceId !== null) {
        response = await this.apiRequest(`/devices/${this.editingDeviceId}`, 'PUT', payload);
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.detail || 'Erro ao atualizar dispositivo');
        }
        this.showMessage('Dispositivo atualizado com sucesso!', 'success');
      } else {
        response = await this.apiRequest('/devices', 'POST', payload);
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.detail || 'Erro ao criar dispositivo');
        }
        this.showMessage('Dispositivo criado com sucesso!', 'success');
      }

      this.resetDeviceForm();
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error saving device:', error);
      this.showError(error.message || 'Erro ao salvar dispositivo');
    }
  }

  startDeviceEdit(deviceId) {
    const device = this.devicesCache.find((item) => item.id === deviceId);
    if (!device) {
      return;
    }

    this.editingDeviceId = deviceId;

    const title = document.getElementById('deviceFormTitle');
    if (title) {
      title.textContent = 'Editar dispositivo';
    }
    const submitBtn = document.getElementById('deviceFormSubmit');
    if (submitBtn) {
      submitBtn.textContent = 'Salvar dispositivo';
    }
    const cancelBtn = document.getElementById('deviceFormCancel');
    if (cancelBtn) {
      cancelBtn.style.display = 'inline-block';
    }

    const nameInput = document.getElementById('deviceName');
    if (nameInput) {
      nameInput.value = device.name || '';
    }
    const typeInput = document.getElementById('deviceType');
    if (typeInput) {
      typeInput.value = device.type || 'lock';
    }
    const statusInput = document.getElementById('deviceStatus');
    if (statusInput) {
      statusInput.value = device.status || 'inactive';
    }
    const resourceIdInput = document.getElementById('deviceResourceId');
    if (resourceIdInput) {
      resourceIdInput.value = device.resource_id ?? '';
    }
    const valueInput = document.getElementById('deviceValue');
    if (valueInput) {
      valueInput.value = device.value ?? '';
    }

    this.focusAdminTab('devices');
  }

  resetDeviceForm() {
    const form = document.getElementById('deviceForm');
    if (form) {
      form.reset();
    }
    this.editingDeviceId = null;

    const title = document.getElementById('deviceFormTitle');
    if (title) {
      title.textContent = 'Cadastrar dispositivo';
    }
    const submitBtn = document.getElementById('deviceFormSubmit');
    if (submitBtn) {
      submitBtn.textContent = 'Adicionar dispositivo';
    }
    const cancelBtn = document.getElementById('deviceFormCancel');
    if (cancelBtn) {
      cancelBtn.style.display = 'none';
    }
  }

  async deleteDevice(deviceId) {
    if (!confirm('Deseja excluir este dispositivo?')) {
      return;
    }
    try {
      const response = await this.apiRequest(`/devices/${deviceId}`, 'DELETE');
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao excluir dispositivo');
      }
      this.showMessage('Dispositivo excluido com sucesso!', 'success');
      if (this.editingDeviceId === deviceId) {
        this.resetDeviceForm();
      }
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error deleting device:', error);
      this.showError(error.message || 'Erro ao excluir dispositivo');
    }
  }
  async reserveResource(resourceId) {
    try {
      const response = await this.apiRequest(`/resources/${resourceId}/reserve`, 'POST', {
        user_id: this.userId
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao reservar recurso');
      }
      this.showMessage('Recurso reservado com sucesso!', 'success');
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error reserving resource:', error);
      this.showError(error.message || 'Erro ao reservar recurso');
    }
  }

  async releaseResource(resourceId) {
    try {
      const response = await this.apiRequest(`/resources/${resourceId}/release`, 'POST');
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao liberar recurso');
      }
      this.showMessage('Recurso liberado com sucesso!', 'success');
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error releasing resource:', error);
      this.showError(error.message || 'Erro ao liberar recurso');
    }
  }

  async adminReleaseResource(resourceId) {
    try {
      const resource = this.resourcesCache.find((item) => item.id === resourceId);
      if (resource && resource.available) {
        this.showMessage('Recurso ja esta disponivel.', 'info');
        return;
      }
      const response = await this.apiRequest(`/resources/${resourceId}/release`, 'POST');
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao liberar recurso');
      }
      this.showMessage('Recurso liberado pelo administrador.', 'success');
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error releasing resource:', error);
      this.showError(error.message || 'Erro ao liberar recurso');
    }
  }

  async executeDeviceAction(deviceId, action) {
    try {
      const response = await this.apiRequest(`/devices/${deviceId}/action`, 'POST', { action });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao executar acao');
      }
      const result = await response.json();
      this.showMessage(result.message || 'Acao executada com sucesso!', 'success');
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error executing device action:', error);
      this.showError(error.message || 'Erro ao executar acao');
    }
  }

  async viewDeviceDetails(deviceId) {
    try {
      const response = await this.apiRequest(`/devices/${deviceId}`);
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao obter detalhes do dispositivo');
      }
      const device = await response.json();
      const info = [
        `<strong>${device.name}</strong>`,
        `Tipo: ${device.type}`,
        `Status: ${this.getStatusText(device)}`
      ];
      if (device.value !== undefined && device.value !== null) {
        info.push(`Valor: ${device.value}`);
      }
      if (device.resource_id !== undefined && device.resource_id !== null) {
        info.push(`Recurso vinculado: ${device.resource_id}`);
      }
      this.showMessage(info.join('<br>'), 'info');
    } catch (error) {
      console.error('Error fetching device details:', error);
      this.showError(error.message || 'Erro ao obter detalhes do dispositivo');
    }
  }

  async updateReservationStatus(reservationId, status) {
    try {
      const response = await this.apiRequest(`/reservations/${reservationId}`, 'PATCH', { status });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao atualizar reserva');
      }
      await response.json();
      const message = status === 'cancelled'
        ? 'Reserva cancelada com sucesso!'
        : 'Reserva atualizada com sucesso!';
      this.showMessage(message, 'success');
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error updating reservation:', error);
      this.showError(error.message || 'Erro ao atualizar reserva');
    }
  }

  async deleteReservation(reservationId) {
    if (!confirm('Deseja remover esta reserva?')) {
      return;
    }
    try {
      const response = await this.apiRequest(`/reservations/${reservationId}`, 'DELETE');
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Erro ao remover reserva');
      }
      this.showMessage('Reserva removida com sucesso!', 'success');
      await this.loadDashboardData();
    } catch (error) {
      console.error('Error deleting reservation:', error);
      this.showError(error.message || 'Erro ao remover reserva');
    }
  }
  getStatusText(device) {
    const statusMap = {
      active: 'Ativo',
      inactive: 'Inativo',
      locked: 'Trancado',
      unlocked: 'Destrancado'
    };
    return statusMap[device.status] || device.status;
  }

  showMessage(message, type = 'success') {
    const container = document.getElementById('messageContainer');
    if (!container) {
      return;
    }

    const toast = document.createElement('div');
    toast.className = `toast show toast-${type}`;
    toast.innerHTML = `
      <div class="toast-body">
        ${message}
        <button type="button" class="btn-close float-end" data-bs-dismiss="toast"></button>
      </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 5000);
  }

  showError(message) {
    this.showMessage(message, 'error');
    const errorDiv = document.getElementById('loginError');
    if (errorDiv) {
      errorDiv.textContent = message;
      errorDiv.style.display = 'block';
    }
  }
}

const app = new IoTApp();
