# IoT Management System

Sistema completo para gestao de recursos compartilhados com apoio de dispositivos IoT simulados. O projeto inclui backend FastAPI, frontend responsivo em Bootstrap, simulador de dispositivos em Python e artefatos de documentacao.

## Visao geral

- **Controle de reservas** com verificacao de conflitos, timeout automatico e liberacao forçada por administradores.
- **IoT integrado**: dispositivos virtuais trocam comandos com o backend (`lock`/`unlock`, leituras de sensores) via API dedicada.
- **Auditoria completa** com logs estruturados e exportacao historica (CSV/PDF).
- **Atualizacoes em tempo real** via WebSocket para recursos, reservas e dispositivos.
- **Documentacao**: diagramas PlantUML, relatorio tecnico e roteiro de apresentacao.

## Arquitetura

```
IoT Management System
├── backend/          # API FastAPI + SQLAlchemy + WebSocket
│   ├── app/core/     # Configuracoes e variaveis de ambiente
│   ├── app/db/       # Base declarativa e inicializacao do banco
│   ├── app/models/   # Modelos ORM e schemas Pydantic
│   ├── app/routers/  # Rotas: auth, resources, devices, reservations, users, audit, realtime
│   ├── app/services/ # Regras de negocio, fila de comandos, autenticacao, notificacoes
│   └── tests/        # Testes pytest (API e servicos)
├── frontend/         # Interface responsiva (Bootstrap, Chart.js, JS vanilla)
│   └── public/
├── device/           # Simulador de dispositivos IoT (Python + httpx)
└── data/             # Banco SQLite padrao (`iot.db`)
```

Componentes se comunicam exclusivamente por HTTP/JSON. O backend expone WebSocket (`/ws/updates`) para notificacoes.

## Banco de dados

- **SQLite** local (pode ser substituido via `DATABASE_URL`).
- **SQLAlchemy** 2.x com models tipados (`User`, `Resource`, `Device`, `Reservation`, `DeviceCommand`, `AuditLog`).
- Seeds iniciais: usuarios `admin`/`user`, recursos exemplo, dispositivos lock/sensor.

Entidades-chave:
- `device_commands`: fila FIFO para comandos a serem executados pelo simulador (`lock`/`unlock`, outros).
- `reservations`: inclui `expires_at`, `status` (scheduled/active/completed/expired/cancelled) e `released_by_admin`.
- `audit_logs`: armazena `{timestamp, user, action, resource_id, device_id, reservation_id, result, details}`.

## Backend

**Tecnologias**: FastAPI, Pydantic v2, SQLAlchemy 2, Passlib (bcrypt), fpdf2, Uvicorn.

**Rotas principais**:
- Authentication: `POST /login` (JWT Bearer).
- Recursos: `GET/POST/PUT/DELETE /resources`, `POST /resources/{id}/reserve`, `POST /resources/{id}/release`.
- Reservas: `GET /reservations` (filtros por status, usuario, recurso, periodo), `GET /reservations/stats/summary`, `GET /reservations/export?format=csv|pdf`.
- Dispositivos: `GET/POST/PUT/DELETE /devices`, `POST /devices/report`, `POST /devices/{id}/commands/next` (consumir comandos).
- Usuarios: `GET/POST/PUT /users`, `PUT /users/{id}/permissions` (somente admin).
- Auditoria: `GET /audit-logs` (admin).
- WebSocket: `ws://<host>:8000/ws/updates` (eventos `resource.*`, `reservation.*`, `device.*`).

**Workers e fila**:
- `reservation_service` executa verificacao periodica (`activate_scheduled_reservations`, `expire_overdue_reservations`).
- Comandos `lock`/`unlock` sao enfileirados na tabela `device_commands` para o simulador consumir.
- `device_commands.fetch_next_command` devolve e marca como consumido (retorna 204 quando vazio).

**Auditoria e permissoes**:
- `ResourcePermission` restringe usuario comum a recursos explicitamente permitidos.
- Admins podem reservar para qualquer usuario (payload `user_id`).
- Logs gerados para reservas, dispositivos e alteracoes de recursos/usuarios.

## Frontend

- **Stack**: HTML5, Bootstrap 5, Chart.js, ES6 vanilla (sem frameworks).
- **Modulo JS** (`public/app.js`):
  - Autentica usuario, guarda token no `localStorage`.
  - Painel usuario: lista de recursos com filtros, reserva/liberacao, reservas ativas, historico filtravel, estatisticas (grafico linha).
  - Painel admin: abas para recursos, dispositivos, usuarios, reservas, auditoria; CRUD completo + exportacao CSV/PDF.
  - Admin pode selecionar outro usuario para reservar (`select` na carta de recurso).
  - WebSocket reconecta automaticamente e sincroniza caches.
  - Botões possuem `aria-label` e layout se adapta (flex wrap, selectors responsivos).

## Simulador de dispositivos (`device/simulator.py`)

- CLI Python 3.11+ usando `httpx`.
- Autentica, descobre dispositivos (`GET /devices`).
- Para cada dispositivo, thread dedicada:
  - busca comandos pendentes (`POST /devices/{id}/commands/next`) e executa (`lock`/`unlock`, `read`).
  - envia leitura/estado atual via `/devices/report` (sensores geram temperatura aleatoria).
  - ajusta estado local conforme reservas (consulta recurso associado).

Execucao:
```bash
cd device
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python simulator.py --base-url http://localhost:8000 --username admin --password admin123 --interval 30
```
Parâmetros extras: `--interval` (segundos), `--insecure`.

## WebSocket e eventos

Eventos JSON enviados pelo backend:
- `resource.created | updated | deleted`
- `reservation.created | updated`
- `device.created | updated | deleted`
- `device.command` (quando fila recebe `lock`/`unlock`)

Payload tipico:
```json
{
  "type": "reservation.updated",
  "reservationId": 12,
  "resourceId": 3,
  "userId": 2,
  "status": "active"
}
```

## Configuracao e execucao

### Requisitos
- Python 3.11+
- Node nao necessario (frontend estatico)
- Docker opcional

### Variaveis importantes
- `SECRET_KEY`: chave JWT (default inseguro).
- `DATABASE_URL`: ex.: `postgresql+psycopg://user:pass@localhost/iot`.
- `RESERVATION_TIMEOUT_MINUTES`, `RESERVATION_CHECK_INTERVAL_SECONDS`.
- `CORS_ORIGINS`: hosts permitidos (comma-separated).

### Execucao local
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend estatico
cd frontend/public
python -m http.server 8080
```
Acesse: API `http://localhost:8000`, UI `http://localhost:8080`.

### Docker
```bash
docker compose up --build
```
Servicos: backend (8000), frontend (8080).

## Testes

- Testes de API (`backend/tests/test_api.py`) cobrem fluxo end-to-end: login, CRUD, reservas, exportacoes, auditoria.
- Testes de servicos (`backend/tests/test_services.py`) cobrem fila de comandos, autorizacao de recursos e liberacao.

Antes de executar os testes garanta que todas as dependencias estejam instaladas:
```bash
cd backend
pip install -r requirements.txt
python -m pytest
```
(Instale `pytest` caso necessario; o arquivo de requirements inclui `sqlalchemy` e `httpx` usados nos testes.)

## API resumida

| Metodo | Rota | Descricao | Permissao |
|--------|------|-----------|-----------|
| POST | /login | Autenticacao JWT | Publico |
| GET | /resources | Lista recursos (filtrado por permissao) | Autenticado |
| POST | /resources | Cria recurso | Admin |
| POST | /resources/{id}/reserve | Reserva recurso (admin pode informar `user_id`) | Autenticado |
| POST | /resources/{id}/release | Libera recurso (`force` exige admin) | Autenticado |
| GET | /reservations | Historico com filtros | Admin / Usuario (restrito) |
| GET | /reservations/stats/summary | Estatisticas gerais | Admin |
| GET | /reservations/export | Exporta CSV/PDF | Admin |
| GET | /devices | Lista dispositivos | Autenticado (restrito) |
| POST | /devices/{id}/commands/next | Retorna proximo comando pendente | Autenticado |
| POST | /devices/report | Reporta status | Publico (simulador) |
| GET | /users | Lista usuarios | Admin |
| PUT | /users/{id}/permissions | Atualiza permissao de recursos | Admin |
| GET | /audit-logs | Auditoria | Admin |

## Uso tipico
1. **Administrador** faz login e cadastra recursos/dispositivos.
2. **Simulador** e iniciado para enviar status e executar comandos.
3. Usuarios autenticam, visualizam recursos permitidos e reservam.
4. Backend gera comando `unlock` -> simulador executa -> estado atualizado.
5. Ao expirar/liberar, backend gera `lock` e atualiza historico/auditoria.
6. Admin exporta historico e consulta estatisticas/auditoria.

## Credenciais de exemplo
| Usuario | Senha | Perfil |
|---------|-------|--------|
| admin   | admin123 | Administrador |
| user    | user123  | Usuario comum |

## Acessibilidade e responsividade
- Componentes principais possuem `aria-label`.
- Layout responsivo (Bootstrap grid + ajustes em `.admin-reserve-select`).
- Botões agrupados com flex-wrap para telas pequenas.

## Melhorias futuras sugeridas
- Interface grafica para agendamento futuro (reservas scheduled).
- Integracao com dispositivos reais (MQTT/HTTP seguro).
- Internacionalizacao (i18n) e tema escuro.
- Pipeline CI/CD (lint, testes, build docker).

## Documentacao complementar
- `docs/uml/*.puml`: diagramas de componentes, sequencia e casos de uso (PlantUML).
- `docs/report/relatorio.md`: relatorio tecnico completo.
- `docs/presentation/apresentacao.md`: roteiro de slides (10-12 slides).

---
Desenvolvido como projeto academico para o IFBA.
