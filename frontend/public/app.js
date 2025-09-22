// IoT Management System - Frontend Application
class IoTApp {
  constructor() {
    this.apiUrl = 'http://localhost:8000';
    this.token = localStorage.getItem('authToken');
    this.userRole = localStorage.getItem('userRole');
    this.username = localStorage.getItem('username');
    this.userId = parseInt(localStorage.getItem('userId')) || null;
    
    this.init();
  }

  init() {
    this.setupEventListeners();
    
    if (this.token && this.userRole && this.username) {
      this.showDashboard();
    } else {
      this.showLogin();
    }
  }

  setupEventListeners() {
    // Login form
    document.getElementById('loginForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleLogin();
    });

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', () => {
      this.handleLogout();
    });

    // Auto-refresh data every 10 seconds
    setInterval(() => {
      if (this.token && document.getElementById('dashboardPage').style.display !== 'none') {
        this.loadDashboardData();
      }
    }, 10000);
  }

  // Authentication methods
  async handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
      const response = await fetch(`${this.apiUrl}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        const data = await response.json();
        
        this.token = data.token;
        this.userRole = data.role;
        this.username = data.username;
        
        // Get user ID from backend (simplified approach)
        this.userId = username === 'admin' ? 1 : 2;
        
        localStorage.setItem('authToken', this.token);
        localStorage.setItem('userRole', this.userRole);
        localStorage.setItem('username', this.username);
        localStorage.setItem('userId', this.userId.toString());
        
        this.showMessage('Login realizado com sucesso!', 'success');
        this.showDashboard();
      } else {
        const error = await response.json();
        this.showError('Credenciais inválidas. Tente novamente.');
      }
    } catch (error) {
      console.error('Login error:', error);
      this.showError('Erro de conexão. Verifique se o servidor está rodando.');
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
    
    this.showLogin();
    this.showMessage('Logout realizado com sucesso!', 'success');
  }

  // UI methods
  showLogin() {
    document.getElementById('loginPage').style.display = 'block';
    document.getElementById('dashboardPage').style.display = 'none';
    document.getElementById('userInfo').style.display = 'none';
    document.getElementById('logoutBtn').style.display = 'none';
    
    // Clear form
    document.getElementById('loginForm').reset();
    document.getElementById('loginError').style.display = 'none';
  }

  showDashboard() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('dashboardPage').style.display = 'block';
    document.getElementById('userInfo').style.display = 'block';
    document.getElementById('logoutBtn').style.display = 'block';
    
    document.getElementById('usernameDisplay').textContent = this.username;
    
    if (this.userRole === 'admin') {
      document.getElementById('userDashboard').style.display = 'none';
      document.getElementById('adminDashboard').style.display = 'block';
    } else {
      document.getElementById('userDashboard').style.display = 'block';
      document.getElementById('adminDashboard').style.display = 'none';
    }
    
    this.loadDashboardData();
  }

  // API methods
  async apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      }
    };

    if (body) {
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
      await Promise.all([
        this.loadResources(),
        this.loadDevices()
      ]);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  }

  async loadResources() {
    try {
      const response = await this.apiRequest('/resources');
      const resources = await response.json();
      
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
      const devices = await response.json();
      
      if (this.userRole === 'admin') {
        this.renderAdminDevices(devices);
      } else {
        this.renderUserDevices(devices);
      }
    } catch (error) {
      console.error('Error loading devices:', error);
    }
  }

  // Rendering methods
  renderUserResources(resources) {
    const container = document.getElementById('resourcesList');
    
    if (resources.length === 0) {
      container.innerHTML = '<p class="text-muted">Nenhum recurso disponível.</p>';
      return;
    }

    container.innerHTML = resources.map(resource => `
      <div class="resource-card p-3 ${resource.available ? 'resource-available' : 'resource-reserved'}">
        <div class="row align-items-center">
          <div class="col-md-8">
            <h6 class="mb-1">${resource.name}</h6>
            <p class="text-muted mb-1">${resource.description}</p>
            <span class="badge ${resource.available ? 'bg-success' : 'bg-danger'}">
              ${resource.available ? 'Disponível' : 'Reservado'}
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
      return `
        <button class="btn btn-success btn-sm" onclick="app.reserveResource(${resource.id})">
          Reservar
        </button>
      `;
    } else if (resource.reserved_by === this.userId) {
      return `
        <button class="btn btn-outline-success btn-sm" onclick="app.releaseResource(${resource.id})">
          Liberar
        </button>
      `;
    } else {
      return '<span class="text-muted">Indisponível</span>';
    }
  }

  renderUserDevices(devices) {
    const container = document.getElementById('devicesList');
    
    if (devices.length === 0) {
      container.innerHTML = '<p class="text-muted">Nenhum dispositivo encontrado.</p>';
      return;
    }

    container.innerHTML = `
      <div class="row">
        ${devices.map(device => `
          <div class="col-md-6 mb-3">
            <div class="card">
              <div class="card-body">
                <h6 class="card-title">${device.name}</h6>
                <p class="card-text">
                  <span class="device-status ${device.status}">${this.getStatusText(device)}</span>
                </p>
                ${device.value !== undefined ? `<p class="card-text"><small class="text-muted">Valor: ${device.value}</small></p>` : ''}
                <div>
                  ${this.renderDeviceActions(device)}
                </div>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  renderDeviceActions(device) {
    if (device.type === 'lock') {
      return `
        <button class="btn btn-outline-success btn-sm me-2" onclick="app.executeDeviceAction(${device.id}, 'unlock')">
          Destrancar
        </button>
        <button class="btn btn-outline-secondary btn-sm" onclick="app.executeDeviceAction(${device.id}, 'lock')">
          Trancar
        </button>
      `;
    } else if (device.type === 'sensor') {
      return `
        <button class="btn btn-outline-success btn-sm me-2" onclick="app.executeDeviceAction(${device.id}, 'read')">
          Ler Sensor
        </button>
        <button class="btn btn-outline-secondary btn-sm" onclick="app.executeDeviceAction(${device.id}, 'activate')">
          Ativar
        </button>
      `;
    }
    return '';
  }

  renderAdminResources(resources) {
    const container = document.getElementById('adminResourcesList');
    
    container.innerHTML = `
      <div class="table-responsive">
        <table class="table table-striped">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>Descrição</th>
              <th>Status</th>
              <th>Reservado por</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            ${resources.map(resource => `
              <tr>
                <td>${resource.id}</td>
                <td>${resource.name}</td>
                <td>${resource.description}</td>
                <td>
                  <span class="badge ${resource.available ? 'bg-success' : 'bg-danger'}">
                    ${resource.available ? 'Disponível' : 'Reservado'}
                  </span>
                </td>
                <td>${resource.reserved_by || '-'}</td>
                <td>
                  ${resource.available ? 
                    `<button class="btn btn-sm btn-outline-danger" onclick="app.adminReleaseResource(${resource.id})">Liberar</button>` :
                    `<button class="btn btn-sm btn-outline-success" onclick="app.adminReleaseResource(${resource.id})">Forçar Liberação</button>`
                  }
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  renderAdminDevices(devices) {
    const container = document.getElementById('adminDevicesList');
    
    container.innerHTML = `
      <div class="table-responsive">
        <table class="table table-striped">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>Tipo</th>
              <th>Status</th>
              <th>Valor</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            ${devices.map(device => `
              <tr>
                <td>${device.id}</td>
                <td>${device.name}</td>
                <td>${device.type}</td>
                <td><span class="device-status ${device.status}">${this.getStatusText(device)}</span></td>
                <td>${device.value !== undefined ? device.value : '-'}</td>
                <td>
                  ${this.renderDeviceActions(device)}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  // Action methods
  async reserveResource(resourceId) {
    try {
      const response = await this.apiRequest(`/resources/${resourceId}/reserve`, 'POST', {
        user_id: this.userId
      });

      if (response.ok) {
        this.showMessage('Recurso reservado com sucesso!', 'success');
        this.loadDashboardData();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Erro ao reservar recurso');
      }
    } catch (error) {
      console.error('Error reserving resource:', error);
      this.showError('Erro de conexão');
    }
  }

  async releaseResource(resourceId) {
    try {
      const response = await this.apiRequest(`/resources/${resourceId}/release`, 'POST');

      if (response.ok) {
        this.showMessage('Recurso liberado com sucesso!', 'success');
        this.loadDashboardData();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Erro ao liberar recurso');
      }
    } catch (error) {
      console.error('Error releasing resource:', error);
      this.showError('Erro de conexão');
    }
  }

  async adminReleaseResource(resourceId) {
    try {
      const response = await this.apiRequest(`/resources/${resourceId}/release`, 'POST');

      if (response.ok) {
        this.showMessage('Recurso liberado pelo administrador!', 'success');
        this.loadDashboardData();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Erro ao liberar recurso');
      }
    } catch (error) {
      console.error('Error releasing resource:', error);
      this.showError('Erro de conexão');
    }
  }

  async executeDeviceAction(deviceId, action) {
    try {
      const response = await this.apiRequest(`/devices/${deviceId}/action`, 'POST', {
        action: action
      });

      if (response.ok) {
        const result = await response.json();
        this.showMessage(result.message || 'Ação executada com sucesso!', 'success');
        this.loadDashboardData();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Erro ao executar ação');
      }
    } catch (error) {
      console.error('Error executing device action:', error);
      this.showError('Erro de conexão');
    }
  }

  // Utility methods
  getStatusText(device) {
    const statusMap = {
      'active': 'Ativo',
      'inactive': 'Inativo',
      'locked': 'Trancado',
      'unlocked': 'Destrancado'
    };
    return statusMap[device.status] || device.status;
  }

  showMessage(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast show toast-${type}`;
    toast.innerHTML = `
      <div class="toast-body">
        ${message}
        <button type="button" class="btn-close float-end" data-bs-dismiss="toast"></button>
      </div>
    `;
    
    document.getElementById('messageContainer').appendChild(toast);
    
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

// Initialize the application
const app = new IoTApp();