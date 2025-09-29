# IoT Management System

Sistema de GestÃ£o de Recursos Compartilhados com simulaÃ§Ã£o IoT - Projeto desenvolvido seguindo os princÃ­pios Clean Code e padrÃµes PEP 8.

## ðŸš€ Funcionalidades

- **Backend FastAPI** com API REST completa
- **Frontend Bootstrap** responsivo com tema IFBA (branco/verde)
- **SimulaÃ§Ã£o de dispositivos IoT** (trancas eletrÃ´nicas, sensores)
- **Sistema de autenticaÃ§Ã£o** JWT com controle de roles
- **GestÃ£o de recursos compartilhados** com reservas
- **Interface administrativa** para gerenciamento completo
- **AtualizaÃ§Ãµes em tempo real** via polling
- **PersistÃªncia em JSON** para prototipagem

## ðŸ—ï¸ Arquitetura

```
â”œâ”€â”€ backend/                 # FastAPI Backend
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ main.py         # AplicaÃ§Ã£o principal
â”‚   â”‚   â”œâ”€â”€ models/         # Modelos Pydantic
â”‚   â”‚   â”œâ”€â”€ routers/        # Rotas da API
â”‚   â”‚   â”œâ”€â”€ services/       # LÃ³gica de negÃ³cio e simulaÃ§Ã£o IoT
â”‚   â”‚   â””â”€â”€ storage/        # PersistÃªncia JSON
â”‚   â””â”€â”€ requirements.txt    # DependÃªncias Python
â”œâ”€â”€ frontend/               # Frontend estÃ¡tico
â”‚   â””â”€â”€ public/
â”‚       â”œâ”€â”€ index.html      # Interface principal
â”‚       â”œâ”€â”€ styles.css      # Tema IFBA
â”‚       â””â”€â”€ app.js          # LÃ³gica JavaScript
â”œâ”€â”€ data/                   # Armazenamento
â”‚   â””â”€â”€ db.json            # Banco de dados JSON
â””â”€â”€ docker-compose.yml     # OrquestraÃ§Ã£o containers
```

## ðŸ”§ InstalaÃ§Ã£o e ExecuÃ§Ã£o

### PrÃ©-requisitos
- Python 3.9+
- Docker (opcional)

### MÃ©todo 1: ExecuÃ§Ã£o Local

1. **Clone o repositÃ³rio**
```bash
git clone https://github.com/LuisPassosRamos/IoT-Management-System.git
cd IoT-Management-System
```

2. **Configure o Backend**
```bash
cd backend
pip install -r requirements.txt
# Defina SECRET_KEY antes de iniciar (ex.: $env:SECRET_KEY="change-me" ou export SECRET_KEY=change-me)
python -m app.main
```

3. **Configure o Frontend** (em outro terminal)
```bash
cd frontend/public
python -m http.server 8080
```

4. **Acesse a aplicaÃ§Ã£o**
- Frontend: http://localhost:8080
- API Docs: http://localhost:8000/docs

### MÃ©todo 2: Docker Compose

```bash
docker compose build
docker compose up
```

- Frontend: http://localhost:8080
- Backend: http://localhost:8000

## ðŸ” Credenciais de Teste

| UsuÃ¡rio | Senha | Papel |
|---------|-------|-------|
| admin | admin123 | Administrador |
| user | user123 | UsuÃ¡rio comum |

## ðŸ“š API Endpoints

### Autenticacao
- `POST /login` - Login de usuario

### Dispositivos IoT
- `GET /devices` - Listar dispositivos
- `GET /devices/{id}` - Detalhar dispositivo
- `POST /devices` - Cadastrar dispositivo (admin)
- `PUT /devices/{id}` - Atualizar dispositivo (admin)
- `DELETE /devices/{id}` - Remover dispositivo (admin)
- `POST /devices/{id}/action` - Executar acao no dispositivo

### Recursos Compartilhados
- `GET /resources` - Listar recursos
- `POST /resources` - Cadastrar recurso (admin)
- `PUT /resources/{id}` - Atualizar recurso (admin)
- `DELETE /resources/{id}` - Remover recurso (admin)
- `POST /resources/{id}/reserve` - Reservar recurso
- `POST /resources/{id}/release` - Liberar recurso

### Reservas
- `GET /reservations` - Listar reservas (admin)
- `PATCH /reservations/{id}` - Atualizar status da reserva (admin)
- `DELETE /reservations/{id}` - Excluir reserva (admin)

### UtilitariosÃ¡rios
- `GET /health` - Health check
- `GET /` - InformaÃ§Ãµes da API

## ðŸŽ¨ Interface

### Tela de Login
![Login](https://github.com/user-attachments/assets/d32aae7b-2e33-4e8b-b4ef-9a3989d04be0)

### Painel Administrativo
![Dashboard](https://github.com/user-attachments/assets/1a4cff82-56d1-42e7-abd9-dc7cd7f87a56)

## ðŸ’¡ SimulaÃ§Ã£o IoT

### Dispositivos Suportados

**Trancas EletrÃ´nicas:**
- AÃ§Ãµes: `unlock`, `lock`
- Estados: `locked`, `unlocked`

**Sensores:**
- AÃ§Ãµes: `read`, `activate`, `deactivate`
- Estados: `active`, `inactive`
- Valores simulados (temperatura: 20-30Â°C)

### Fluxo de Reserva

1. UsuÃ¡rio visualiza recursos disponÃ­veis
2. Seleciona recurso para reservar
3. Sistema marca recurso como reservado
4. Dispositivo IoT associado Ã© acionado automaticamente
5. UsuÃ¡rio pode liberar recurso quando terminar

## ðŸ”¬ Testes

```bash
cd backend
pip install pytest httpx
pytest tests/ -v
```

## ðŸ“‹ Qualidade de CÃ³digo

### PEP 8 Compliance
```bash
cd backend
pip install flake8 black
flake8 app/ --max-line-length=79
black app/ --line-length=79
```

### PrincÃ­pios Aplicados
- **Clean Code**: funÃ§Ãµes pequenas, nomes descritivos
- **SOLID**: separaÃ§Ã£o de responsabilidades
- **Type Hints**: tipagem estÃ¡tica em todo backend
- **Modularidade**: cÃ³digo organizado em mÃ³dulos especÃ­ficos

## ðŸ­ ProduÃ§Ã£o

Para usar em produÃ§Ã£o, considere:

- Substituir JSON por PostgreSQL/MongoDB
- Implementar HTTPS e autenticaÃ§Ã£o segura
- Adicionar monitoramento e logs estruturados
- Configurar CI/CD pipelines
- Implementar testes de integraÃ§Ã£o
- Conectar dispositivos IoT reais via MQTT/HTTP

## ðŸ¤ ContribuiÃ§Ã£o

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanÃ§as
4. Push para a branch
5. Abra um Pull Request

## ðŸ“„ LicenÃ§a

Este projeto Ã© open source e estÃ¡ disponÃ­vel sob a licenÃ§a MIT.

---

**Desenvolvido com ðŸ’š para o IFBA - Instituto Federal da Bahia**




