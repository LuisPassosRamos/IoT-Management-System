# IoT Management System

Sistema de Gestão de Recursos Compartilhados com simulação IoT - Projeto desenvolvido seguindo os princípios Clean Code e padrões PEP 8.

## 🚀 Funcionalidades

- **Backend FastAPI** com API REST completa
- **Frontend Bootstrap** responsivo com tema IFBA (branco/verde)
- **Simulação de dispositivos IoT** (trancas eletrônicas, sensores)
- **Sistema de autenticação** JWT com controle de roles
- **Gestão de recursos compartilhados** com reservas
- **Interface administrativa** para gerenciamento completo
- **Atualizações em tempo real** via polling
- **Persistência em JSON** para prototipagem

## 🏗️ Arquitetura

```
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── main.py         # Aplicação principal
│   │   ├── models/         # Modelos Pydantic
│   │   ├── routers/        # Rotas da API
│   │   ├── services/       # Lógica de negócio e simulação IoT
│   │   └── storage/        # Persistência JSON
│   └── requirements.txt    # Dependências Python
├── frontend/               # Frontend estático
│   └── public/
│       ├── index.html      # Interface principal
│       ├── styles.css      # Tema IFBA
│       └── app.js          # Lógica JavaScript
├── data/                   # Armazenamento
│   └── db.json            # Banco de dados JSON
└── docker-compose.yml     # Orquestração containers
```

## 🔧 Instalação e Execução

### Pré-requisitos
- Python 3.13+
- Docker (opcional)

### Método 1: Execução Local

1. **Clone o repositório**
```bash
git clone https://github.com/LuisPassosRamos/IoT-Management-System.git
cd IoT-Management-System
```

2. **Configure o Backend**
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

3. **Configure o Frontend** (em outro terminal)
```bash
cd frontend/public
python -m http.server 8080
```

4. **Acesse a aplicação**
- Frontend: http://localhost:8080
- API Docs: http://localhost:8000/docs

### Método 2: Docker Compose

```bash
docker compose build
docker compose up
```

- Frontend: http://localhost:8080
- Backend: http://localhost:8000

## 🔐 Credenciais de Teste

| Usuário | Senha | Papel |
|---------|-------|-------|
| admin | admin123 | Administrador |
| user | user123 | Usuário comum |

## 📚 API Endpoints

### Autenticação
- `POST /login` - Login de usuário

### Dispositivos IoT
- `GET /devices` - Listar dispositivos
- `GET /devices/{id}` - Obter dispositivo específico
- `POST /devices/{id}/action` - Executar ação no dispositivo

### Recursos Compartilhados
- `GET /resources` - Listar recursos
- `POST /resources/{id}/reserve` - Reservar recurso
- `POST /resources/{id}/release` - Liberar recurso

### Utilitários
- `GET /health` - Health check
- `GET /` - Informações da API

## 🎨 Interface

### Tela de Login
![Login](https://github.com/user-attachments/assets/d32aae7b-2e33-4e8b-b4ef-9a3989d04be0)

### Painel Administrativo
![Dashboard](https://github.com/user-attachments/assets/1a4cff82-56d1-42e7-abd9-dc7cd7f87a56)

## 💡 Simulação IoT

### Dispositivos Suportados

**Trancas Eletrônicas:**
- Ações: `unlock`, `lock`
- Estados: `locked`, `unlocked`

**Sensores:**
- Ações: `read`, `activate`, `deactivate`
- Estados: `active`, `inactive`
- Valores simulados (temperatura: 20-30°C)

### Fluxo de Reserva

1. Usuário visualiza recursos disponíveis
2. Seleciona recurso para reservar
3. Sistema marca recurso como reservado
4. Dispositivo IoT associado é acionado automaticamente
5. Usuário pode liberar recurso quando terminar

## 🔬 Testes

```bash
cd backend
pip install pytest httpx
pytest tests/ -v
```

## 📋 Qualidade de Código

### PEP 8 Compliance
```bash
cd backend
pip install flake8 black
flake8 app/ --max-line-length=79
black app/ --line-length=79
```

### Princípios Aplicados
- **Clean Code**: funções pequenas, nomes descritivos
- **SOLID**: separação de responsabilidades
- **Type Hints**: tipagem estática em todo backend
- **Modularidade**: código organizado em módulos específicos

## 🏭 Produção

Para usar em produção, considere:

- Substituir JSON por PostgreSQL/MongoDB
- Implementar HTTPS e autenticação segura
- Adicionar monitoramento e logs estruturados
- Configurar CI/CD pipelines
- Implementar testes de integração
- Conectar dispositivos IoT reais via MQTT/HTTP

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é open source e está disponível sob a licença MIT.

---

**Desenvolvido com 💚 para o IFBA - Instituto Federal da Bahia**
