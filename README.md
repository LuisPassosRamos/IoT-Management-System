# IoT Management System

Sistema de Gestao de Recursos Compartilhados com dispositivos IoT simulados. O projeto foi reorganizado para atender aos requisitos de cadastro completo, auditoria, estatisticas e comunicacao em tempo real.

## Visao Geral

- **Backend**: FastAPI + SQLAlchemy + SQLite (rotas REST e WebSocket)
- **Frontend**: HTML/Bootstrap/JavaScript com atualizacao em tempo real
- **Simulador**: Script Python que envia status periodicos de dispositivos
- **Logs**: Auditoria estruturada `{timestamp, user, action, resourceId, result}`
- **Documentacao**: Diagramas PlantUML, relatorio tecnico e roteiro de slides

## Estrutura de Diretorios

```
backend/                 # API FastAPI
  app/
    core/                # Configuracoes
    db/                  # Base SQLAlchemy e init_db
    models/              # Modelos ORM + schemas Pydantic
    routers/             # auth, resources, devices, reservations, users, audit, realtime
    services/            # auth, reservation_service, audit, notifications
  tests/                 # Testes pytest
frontend/
  public/                # index.html, styles.css, app.js
  Dockerfile
device/
  simulator.py           # Simulador de dispositivos IoT
  requirements.txt
 data/
  iot.db                 # Banco SQLite (gerado automaticamente)
docs/
  uml/                   # Diagramas PlantUML
  report/                # Relatorio tecnico
  presentation/          # Roteiro de slides
```

## Dependencias Principais

- Python 3.11+
- FastAPI, SQLAlchemy, passlib, fpdf2
- Bootstrap 5, Chart.js (frontend)
- httpx (simulador)

## Configuracao Rapida (ambiente local)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
set SECRET_KEY=change-me    # Windows (PowerShell)
export SECRET_KEY=change-me # Linux/macOS
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Documentacao Swagger: `http://localhost:8000/docs`

### 2. Frontend estatico

```bash
cd frontend/public
python -m http.server 8080
```

Acesse `http://localhost:8080`.

### 3. Simulador de dispositivos (opcional)

```bash
cd device
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python simulator.py --base-url http://localhost:8000 --username admin --password admin123 --interval 30
```

### 4. Docker Compose (opcional)

```bash
docker compose up --build
```

## Credenciais de exemplo

| Usuario | Senha     | Papel         |
|---------|-----------|---------------|
| admin   | admin123  | Administrador |
| user    | user123   | Usuario comum |

## Principais Endpoints

- `POST /login`
- `GET /resources` | `POST /resources` | `PUT /resources/{id}` | `DELETE /resources/{id}`
- `POST /resources/{id}/reserve` | `POST /resources/{id}/release`
- `GET /reservations` (filtros por status, user, recurso, datas)
- `GET /reservations/stats/summary`
- `GET /reservations/export?format=csv|pdf`
- `GET /devices` | `POST /devices` | `POST /devices/report`
- `GET /users` | `POST /users` | `PUT /users/{id}/permissions`
- `GET /audit-logs`
- WebSocket: `ws://localhost:8000/ws/updates`

## Frontend (app.js)

- Exibe recursos com filtro de texto/tipo e botoes de reserva/liberacao
- Lista reservas ativas, historico filtravel e estatisticas com Chart.js
- Painel admin com CRUD de recursos, dispositivos, usuarios e auditoria
- Conexao WebSocket para atualizacoes imediatas de recursos/reservas/dispositivos

## Simulador (device/simulator.py)

- Autentica no backend e descobre dispositivos
- Threads enviam status periodico via `/devices/report`
- Bloqueios sao deixados `locked`/`unlocked` conforme status do recurso
- Parametros CLI: `--base-url`, `--username`, `--password`, `--interval`, `--insecure`

## Testes

```bash
cd backend
python -m pytest
```

> Observacao: instale `pytest` caso nao esteja presente (`pip install pytest`).

## Documentacao

- Diagramas: `docs/uml/*.puml`
- Relatorio tecnico: `docs/report/relatorio.md`
- Roteiro de slides: `docs/presentation/apresentacao.md`
