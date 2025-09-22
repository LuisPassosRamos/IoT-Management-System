Sistema IoT de Gestão de Recursos Compartilhados – Guia de Desenvolvimento
Checklist de Desenvolvimento
[ ] Organização da Estrutura de Diretórios
[ ] Definir uma estrutura de pastas clara separando o projeto em frontend e backend.
[ ] Criar o diretório raiz do projeto com subdiretórios principais, por exemplo:
backend/ – Código do servidor (API REST, lógica de simulação de dispositivos, autenticação).
frontend/ – Aplicação web (páginas HTML, CSS/Bootstrap, JavaScript).
data/ (opcional) – Arquivos de armazenamento (por exemplo, banco de dados JSON ou outros recursos persistentes).
[ ] Dentro de backend/, criar subpastas para organizar o código, por exemplo:
app/ – Código-fonte do aplicativo backend organizado em módulos (por exemplo, routes, models, services).
tests/ – (Opcional) Testes unitários ou de integração do backend.
Dockerfile – Arquivo Docker específico do backend (pode ficar no raiz de backend/).
[ ] Dentro de frontend/, criar subpastas para separar arquivos da interface, por exemplo:
public/ – Arquivos estáticos (HTML, CSS, JS, imagens) que serão servidos ao usuário.
src/ – (Opcional, se aplicável) Código-fonte estruturado da interface caso use um bundler ou framework frontend.
Dockerfile – Arquivo Docker para o frontend (pode ficar no raiz de frontend/ se necessário).
[ ] Criação de Ambiente com Docker
[ ] Configurar um Dockerfile do backend:
Usar uma imagem base do Python (por exemplo, python:3.9-slim) compatível com o framework escolhido.
Copiar o código do backend para o contêiner e instalar as dependências (por exemplo, instalar Flask ou FastAPI, biblioteca de autenticação JWT se usada, etc.).
Definir a variável de ambiente que indica a porta (ex: FLASK_RUN_PORT=5000 ou configurar no Dockerfile diretamente) e o comando de inicialização (ex: flask run --host=0.0.0.0 ou executar o servidor do FastAPI via Uvicorn).
[ ] Configurar um Dockerfile do frontend (separado):
Se o frontend for estático (HTML/JS/CSS puros), considerar usar uma imagem do Nginx ou Apache para servir os arquivos. Copiar o conteúdo de frontend/public para o diretório de servição (ex: /usr/share/nginx/html no Nginx).
Se o frontend for uma aplicação com servidor de desenvolvimento (não muito provável neste caso simples), configurar a imagem base adequada (por exemplo, Node.js) e os comandos para build/serve.
[ ] Criar um arquivo docker-compose.yml na raiz do projeto para orquestrar os contêineres:
Definir um serviço para o backend (usando o Dockerfile do backend). Mapear a porta interna (ex: 5000) para uma porta do host (ex: 5000) para acesso à API.
Definir um serviço para o frontend (usando o Dockerfile do frontend ou uma imagem de servidor web). Mapear a porta apropriada (ex: 80 do contêiner Nginx para 8080 no host).
Configurar rede do Docker Compose de modo que o frontend possa se comunicar com o backend (geralmente os serviços já ficam na mesma rede interna do Compose; usar o nome do serviço do backend como host nas requisições do frontend).
Opcionalmente, adicionar volumes para desenvolvimento (por exemplo, bind mount do código para o contêiner) para facilitar atualizações sem rebuild completo, embora para protótipo isso não seja essencial.
[ ] Documentar e testar o ambiente Docker:
Escrever instruções de uso (no README) para construir as imagens (docker-compose build) e rodar os contêineres (docker-compose up).
Testar subindo o docker-compose e acessando tanto a interface web (frontend) quanto a API (backend) para garantir que estão funcionando e se comunicando corretamente.
[ ] Configuração do Backend (API e Simulação)
[ ] Inicializar um projeto Python para o backend, utilizando o framework escolhido (Flask ou FastAPI de preferência pela simplicidade).
Organizar o ponto de entrada (por ex., app.py ou main.py) que inicia a aplicação web.
Se usar Flask, configurar a aplicação e registrar blueprints (módulos de rotas) para separar funcionalidades. Se usar FastAPI, organizar routers de forma similar.
[ ] Implementar rotas RESTful para os recursos do sistema (seguindo arquitetura REST):
Exemplos de rotas de dispositivos IoT:
GET /devices – Lista os dispositivos simulados e seus estados atuais.
POST /devices/{id}/action – Aciona uma ação em um dispositivo específico (exemplo: POST /devices/3/unlock para desbloquear o dispositivo de ID 3).
GET /devices/{id} – (Opcional) Obter detalhes ou estado específico de um dispositivo.
Exemplos de rotas de recursos compartilhados:
GET /resources – Lista os recursos compartilhados (ex: salas, equipamentos) e sua disponibilidade/estado atual.
POST /resources/{id}/reserve – Realiza a reserva do recurso especificado (associando-o a um usuário, marcando como indisponível, etc.).
POST /resources/{id}/release – (Opcional) Libera ou devolve o recurso, encerrando a reserva e atualizando o estado do dispositivo associado (ex: tranca fechada).
GET /reservations – (Opcional) Lista reservas ativas ou histórico de reservas (funcionalidade administrativa).
[ ] Simular dispositivos IoT (sensores, atuadores, trancas, etc.):
Criar estruturas de dados, classes ou funções para representar os dispositivos. Por exemplo, uma classe Lock com métodos unlock() e lock(), ou uma classe Sensor com método read() que gera um valor simulado.
Sem hardware real, os métodos devem mudar o estado interno simulado e retornar resultados consistentes: ao "desbloquear" uma tranca, marcar seu estado como aberto; ao ler um sensor, retornar um valor aleatório dentro de um range plausível ou um valor fixo definido para testes.
Garantir que os resultados dessas operações sejam utilizados nas respostas das rotas da API. Por exemplo, o POST /devices/3/unlock aciona Lock.unlock() internamente e então a resposta da API indica que o dispositivo 3 está desbloqueado.
[ ] Implementar lógica de negócio simulada para gestão de recursos compartilhados:
Ao realizar uma reserva de recurso (POST /resources/{id}/reserve), atualizar no sistema o status desse recurso para "indisponível" (reservado) e associá-lo a um usuário (ex: registrar qual usuário fez a reserva), tudo isso em memória ou no arquivo JSON.
Se houver um dispositivo IoT vinculado ao recurso (por exemplo, uma fechadura eletrônica em uma sala), chamar a simulação correspondente (ex: método de desbloqueio) para refletir que o recurso foi liberado para uso, e registrar essa ação.
Implementar também a liberação/devolução de recurso (se aplicável): marcando o recurso como disponível novamente e, se necessário, acionar a simulação de fechamento de tranca ou reset de sensor.
[ ] Integrar persistência simples de dados:
Utilizar um arquivo JSON como banco de dados simulado para armazenar informações do sistema: usuários, dispositivos, recursos e reservas. Esse arquivo pode ser algo como data/db.json.
Estruturar o JSON de forma organizada, por exemplo:


{
  "users": [...],
  "devices": [...],
  "resources": [...],
  "reservations": [...]
}
Implementar funções utilitárias no backend para ler e escrever nesse arquivo JSON sempre que houver alterações (por exemplo, carregar os dados na inicialização da aplicação e salvar no disco em cada operação de criação/atualização relevante). Isso pode ser feito de maneira simples com o módulo json do Python.
(Opcional) Em vez de manipular JSON "na mão", considerar o uso de uma biblioteca ou abordagem simples como TinyDB (banco NoSQL em arquivo JSON) ou mesmo um SQLite, caso isso agilize as operações. Entretanto, manter a simplicidade é prioridade.
[ ] Simular autenticação básica de usuários:
Definir no JSON inicial um conjunto de usuários com credenciais (pode usar senhas em plaintext para simplificar o protótipo, ou hashed se desejar um pouco mais de realismo). Incluir um campo que indique o perfil, por exemplo "role": "admin" para um usuário administrador versus "role": "user" para um comum.
Implementar a rota POST /login no backend: ela deve verificar se o usuário e senha fornecidos correspondem a um registro válido no "banco" JSON.
Se válido, retornar um token de sessão (pode ser um JWT simples assinado com uma chave fixa, ou até um token fictício gerado aleatoriamente só para simular a sessão). Esse token será usado pelo frontend para autenticação nas demais chamadas.
Se inválido, retornar erro apropriado (401 Unauthorized).
No backend, criar um mecanismo simples de controle de acesso: rotas sensíveis (como as de reserve/release ou listagem de reservas, criação de recursos, etc.) devem checar se o token enviado pelo frontend é válido e se o usuário tem permissão (ex: só admin pode criar novos recursos ou listar todas reservas). Isso pode ser feito via um middleware simples ou manualmente em cada rota protegida.
[ ] Seguir boas práticas de desenvolvimento no backend:
Escrever código claro e legível, dividindo em funções e módulos para evitar duplicação e facilitar manutenção (princípios de Clean Code). Por exemplo, separar as rotas da lógica de simulação e da lógica de persistência, mantendo cada parte do código focada em uma tarefa.
Nomear variáveis e funções de forma descritiva, adicionar comentários quando necessário para explicar partes complexas, e aderir ao padrão de estilo PEP 8 do Python.
Garantir que a estrutura modular facilite futuras expansões (por exemplo, seja fácil adicionar um novo tipo de dispositivo IoT simulado criando um novo módulo/classe sem precisar refatorar muita coisa do core).
[ ] (Opcional) Implementar WebSocket para atualizações em tempo real:
Caso seja necessário que o frontend receba atualizações instantâneas (por exemplo, mudança de estado de um dispositivo sem o usuário precisar atualizar a página), configurar um canal WebSocket no backend.
Se estiver usando Flask, pode-se integrar o Flask-SocketIO; se for FastAPI, é possível usar suporte nativo a WebSockets ou libraries como Starlette (base do FastAPI) para websockets.
Implementar emissões de eventos: por exemplo, quando um dispositivo mudar de estado (simulado), o backend emite um evento via WebSocket para o frontend contendo o novo estado, que então atualiza a interface imediatamente.
Documentar e assegurar que, se o WebSocket não estiver habilitado, a aplicação ainda funcione usando polling periódico como alternativa (o WebSocket é um aprimoramento para experiência em tempo real).
[ ] Configuração do Frontend (Interface Web)
[ ] Configurar o projeto frontend para usar Bootstrap como base de estilo e responsividade:
Incluir o CSS do Bootstrap (via CDN no HTML principal, ou import local) e garantir que as cores predominantes do tema sejam branco e verde (cores padrão do IFBA). Isso pode ser feito por meio de classes utilitárias do Bootstrap (por exemplo, utilizar classes bg-success ou text-success para aplicar tons de verde) e CSS customizado adicional para ajustar tons exatos conforme necessário.
Criar um layout consistente para a aplicação: por exemplo, um navbar/header no topo com o título do sistema e opções de navegação (mudando opções conforme login/admin), e talvez um footer simples. Aplicar cor de fundo branca nas áreas principais e usar detalhes em verde (ex: barra de navegação ou botões de ação em verde IFBA).
[ ] Implementar a Tela de Login:
Desenvolver uma página de login (login.html) com um formulário solicitando usuário e senha. Estilizar o formulário com Bootstrap (usar classes como form-control, btn btn-success para o botão de submissão, etc.).
Usar JavaScript (Fetch API ou AJAX) para enviar as credenciais fornecidas pelo usuário à API (POST /login).
Tratar a resposta do login: se sucesso, armazenar o token de autenticação retornado (por exemplo, salvar no localStorage do navegador ou em um cookie, de forma simples) e redirecionar o usuário para a página principal (dashboard). Se falhar, exibir uma mensagem de erro na própria página de login (por exemplo, um alerta Bootstrap em vermelho indicando credenciais inválidas).
[ ] Implementar a Tela de Dashboard do Usuário (pós-login comum):
Criar uma página principal (dashboard.html) que apresente ao usuário uma visão geral dos recursos compartilhados disponíveis e o estado dos dispositivos IoT simulados associados. Por exemplo: uma lista ou tabela de recursos indicando quais estão disponíveis, reservados, e possivelmente um indicador de status do dispositivo (ex: "Tranca aberta/fechada", "Sensor: ativo/inativo/valor").
Incluir botões ou ações para o usuário interagir, dependendo de suas permissões. Usuário comum poderia, por exemplo, clicar em "Reservar" em um recurso disponível (o que enviará uma requisição POST /resources/{id}/reserve para o backend) ou "Liberar" se ele mesmo tiver reservado e estiver devolvendo. Essas ações devem atualizar a interface (por exemplo, remover o recurso de sua lista de disponíveis ou atualizar o status para "reservado por você").
Usar JavaScript para buscar os dados do backend assim que a página carregar: fazer um GET em /resources para popular a lista de recursos, e talvez GET em /devices para estados de dispositivos. Exibir esses dados de forma amigável (talvez usando componentes como cards ou listas do Bootstrap).
Garantir que a interface atualize periodicamente ou em tempo real: se não implementar WebSocket, configurar um intervalo (setInterval) para refazer requisições (por ex., a cada 5 segundos) e atualizar o status dos recursos/dispositivos na página. Se houver WebSocket, escutar eventos e atualizar imediatamente quando recebidos (ex.: mudar o estado de um ícone de cadeado de fechado para aberto quando chegar um evento de unlock).
[ ] Implementar as Telas de Administração (disponíveis apenas para usuários administradores):
Proteger essas páginas para que somente sejam acessíveis se o usuário logado tiver perfil admin (isso pode ser feito simplesmente verificando um campo no token ou no armazenamento local antes de permitir acessar, além de o backend também proteger as rotas).
Tela de Gerenciamento de Recursos/Dispositivos: página que lista todos os recursos e dispositivos, com opções para CRUD (Create, Read, Update, Delete) básicas. Por exemplo: formulário para adicionar novo recurso (nome, descrição, dispositivo vinculado), botões para editar ou remover recursos existentes. As ações de criação/edição/remoção devem chamar as APIs correspondentes no backend (por ex: POST /resources para criar, PUT /resources/{id} para editar, DELETE /resources/{id} para excluir).
Tela de Visualização de Reservas e Usuários: página onde o admin pode ver todas as reservas ativas e histórico (resultado de GET /reservations se implementado), e possivelmente gerenciar usuários (esta última funcionalidade pode ser opcional caso foque apenas em recursos, mas poderia permitir cadastrar novos usuários ou alterar senhas, etc.).
Incluir elementos de UI para facilitar administração, como tabelas (usando table.table do Bootstrap) mostrando dados, e modais ou páginas separadas para formularios de criação/edição.
[ ] Integração do Frontend com a API:
Em todas as páginas protegidas (dashboard, admin), antes de fazer requisições, incluir o token de autenticação nos headers das requisições Fetch/AJAX (ex: Authorization: Bearer <token> se usando JWT, ou outro header conforme implementado) para que o backend reconheça o usuário.
Consumir os endpoints do backend adequadamente: por exemplo, na página de dashboard, após login, chamar GET /resources e atualizar o DOM com a lista de recursos retornada; ao clicar em "Reservar", chamar POST /resources/{id}/reserve; na página admin, chamar POST /resources ao submeter formulário de criação de novo recurso, etc.
Tratar as respostas de forma assíncrona e proporcionar feedback ao usuário: exibir mensagens de sucesso ou erro após ações (usar componentes de alerta do Bootstrap, modais de confirmação, etc.). Atualizar a interface local conforme a ação (por exemplo, se um recurso foi removido via API, retirar seu elemento da lista na página sem precisar recarregar por completo).
Se implementado WebSocket no backend, estabelecer a conexão no frontend (por exemplo, usando a biblioteca Socket.IO se Flask-SocketIO, ou a API nativa de WebSocket do browser se FastAPI) assim que o usuário estiver no dashboard. Definir callbacks para eventos recebidos, atualizando elementos da página de acordo (por ex.: exibir em tempo real que "Recurso X foi reservado por outro usuário agora" ou "Dispositivo Y mudou para estado Z").
[ ] Testar e Refinar a Interface:
Realizar testes manuais de navegação: acessar a tela de login, entrar com um usuário comum, verificar se o dashboard carrega os dados corretamente e se as ações de reservar/liberar funcionam e refletem mudanças. Repetir com um usuário admin, acessando as telas de administração e testando funções de CRUD.
Ajustar detalhes de layout e usabilidade conforme necessário: assegurar que as páginas ficam legíveis tanto em desktop quanto em dispositivos móveis (aproveitando o grid responsivo do Bootstrap), que textos e botões estejam em português claro, e que as cores e contrastes estejam agradáveis (por exemplo, atenção com texto em verde sobre fundo branco e vice-versa para manter legibilidade).
Conferir se todos os fluxos importantes têm feedback ao usuário (por exemplo, se a reserva falhar por algum motivo, uma mensagem é exibida; se uma ação requer login, o sistema redireciona para login apropriadamente, etc.).
[ ] Observações Finais e Boas Práticas
[ ] Simulação vs. Funcionalidade Real: lembrar que todas as interações dependentes de hardware IoT são simuladas no código. Ou seja, o sistema deve funcionar sem dispositivos físicos, mas exibindo resultados coerentes das ações simuladas (ex: ao "destrancar" via interface, o estado do dispositivo passa a destrancado na simulação). Funcionalidades que não dependem de hardware (como login, fluxo de reserva via interface) são implementadas diretamente, sem necessidade de simulação especial. Isso garante que o sistema possa ser testado integralmente apenas pela interface web.
[ ] Testes básicos do sistema:
Realizar testes unitários ou de integração no backend, se possível, utilizando frameworks como pytest ou unittest. Por exemplo, testar separadamente as funções de simulação (ver se ao chamar a função de desbloquear tranca o estado muda conforme esperado), as rotas da API (usando um cliente de teste Flask/FastAPI para verificar respostas HTTP e mudanças no "banco" JSON), e a autenticação (login com credenciais corretas vs. incorretas).
Testes manuais integrados: executar o sistema via Docker e passar por cenários completos – um usuário reservando um recurso, depois liberando, um admin criando um novo recurso, etc. – para verificar se todas as partes (frontend ↔ backend ↔ simulação) estão se comunicando corretamente.
[ ] Extensibilidade e Manutenibilidade:
Projetar e comentar o código pensando em futuras expansões. Por exemplo, deixar claro nos comentários ou documentação quais partes do sistema precisariam ser adaptadas para conectar a dispositivos reais no futuro (talvez indicando pontos de integração onde hoje há simulação).
Estruturar o código de forma genérica onde possível: por exemplo, se há código repetitivo para diferentes tipos de dispositivos simulados, considerar abstrair em uma função ou classe base. Usar configurações (arquivos de config ou constantes) para parâmetros que possam mudar (como intervalo de atualização, ou toggle para ativar/desativar WebSocket), facilitando ajustes.
Se houver tempo, incluir no README ou documentação interna sugestões de próximos passos para transformar o protótipo em um sistema de produção (por exemplo: trocar o JSON flat-file por um banco de dados robusto, usar HTTPS e tokens seguros, validações mais rigorosas de entrada de dados, etc.).
[ ] Documentação do Código e do Projeto:
Escrever um README.md na raiz do projeto detalhando: a descrição do sistema, instruções de como instalar/deploy (incluindo como usar o Docker Compose), como usar a aplicação (passo a passo para acessar a interface, realizar login, etc.), e informar quais funcionalidades estão simuladas.
Documentar as rotas da API (por exemplo, listar todos os endpoints disponíveis, métodos HTTP, parâmetros esperados e exemplos de resposta). Isso pode ser no README ou em um documento separado de API. Se usar FastAPI, aproveite a documentação automática via Swagger (docs) embutida.
Comentar partes importantes do código no backend e frontend para que outro desenvolvedor (ou a própria IA geradora) entenda a intenção de cada módulo. Manter a consistência de nomenclatura e estrutura para facilitar navegação pelo código.
Incluir instruções de como rodar os testes (se houver) e mencionar qualquer ferramenta usada que precise ser instalada ou configurada.
[ ] Conformidade com boas práticas:
Fazer uma revisão final no código fonte assegurando conformidade com o estilo (no Python, seguir PEP 8; no HTML/CSS, manter indentação e fechamento de tags corretos; no JavaScript, evitar variáveis globais desnecessárias, etc.). Ferramentas como linters ou formatadores automáticos podem ajudar aqui (por exemplo, flake8 ou black para Python).
Garantir que a solução está modularizada e limpa: arquivos organizados, responsabilidades bem divididas, facilitando localização de funcionalidade (por exemplo, se alguém quiser alterar algo no frontend, saber exatamente onde ir; se for ajustar uma rota ou regra de negócio no backend, idem).
Por fim, verificar se todos os requisitos iniciais foram atendidos na simulação (dispositivos simulados com reflexo na interface, autenticação básica funcionando, arquitetura separada frontend/backend com Docker, uso do tema de cores solicitado, etc.), assegurando que o protótipo seja funcional e apresente uma experiência realista mesmo sendo uma simulação.

