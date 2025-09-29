# IoT Device Simulator

Este diretorio contem um simulador simples de dispositivos IoT que se comunica com o backend via HTTP. O objetivo e enviar atualizacoes periodicas de status para o endpoint `/devices/report` e consultar o backend para ajustar o comportamento de acordo com reservas ativas.

## Pre-requisitos

- Python 3.11+
- Dependencias listadas em `requirements.txt`

```bash
pip install -r requirements.txt
```

## Execucao

```bash
python simulator.py --base-url http://localhost:8000 --username admin --password admin123
```

Parametros opcionais:

- `--interval`: intervalo (segundos) entre atualizacoes (padrao 30).
- `--insecure`: desativa verificacao TLS (para ambientes de teste).

O simulador autentica com o backend, descobre os dispositivos associados e cria uma thread por dispositivo. Cada thread envia medicoes de estado periodicamente:

- **Sensor**: gera leituras aleatorias (ex.: temperatura) e envia ao backend.
- **Lock**: consulta o estado do recurso e envia status `locked` ou `unlocked`.
- **Outros tipos**: enviam eventos de manutencao simples.

## Recebimento de comandos

A partir da versao atual o simulador tambem consulta o endpoint `/devices/{id}/commands/next` para executar os comandos enviados pelo backend:

- `unlock` libera a fechadura relacionada a uma reserva ativa.
- `lock` trava a fechadura quando a reserva termina ou e cancelada.

Comandos processados sao confirmados reportando imediatamente o novo estado via `/devices/report`. Dessa forma o requisito "recebe comandos do backend" e atendido.

O simulador pode ser encerrado com `Ctrl+C`.
