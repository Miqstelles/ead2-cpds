# Sprint 1 — Nucleo + Unicast

**Periodo:** 1 semana (planejada)
**Sprint Goal:** Entregar broker e cliente capazes de registrar nomes,
enviar e consumir mensagens unicast com carimbo logico de Lamport e log
de producao/consumo conferivel.

## Sprint Backlog

| ID   | User Story                                                   | Estimativa |
|------|--------------------------------------------------------------|------------|
| US01 | Registrar cliente com nome unico                             | M          |
| US02 | Enviar/consumir mensagem unicast                             | M          |
| US03 | Lamport em produtor/broker/consumidor                        | S          |
| US04 | Logs de producao e consumo (CSV)                             | S          |
| US05 | Buffer com identificacao do produtor                         | S          |

## Daily (resumo)

- D1: setup do repositorio, `pyproject.toml`, decisao por Python 3.9+
- D2: `LamportClock`, `Message`, `Protocol`, testes unitarios
- D3: `MessageBuffer`, `LogManager`, testes unitarios (35 verdes)
- D4: `Broker` + `Client` + `CLI`
- D5: testes de integracao (10 verdes), totalizando 45 testes
- D6: documentacao
- D7: review + retro

## Sprint Review

- **Demos:**
  - `mensageria broker --port 9000` sobe o bus.
  - `mensageria client --name alice --send-unicast bob "oi"` envia.
  - `mensageria client --name bob --consume` consome.
  - `cat logs/production.log logs/consumption.log` mostra rastros logicos.
- **Aceito pelo PO:** sim (PO = aluno).

## Sprint Retro

**O que foi bem:**
- Camadas (lamport / message / protocol / buffer / log) ficaram pequenas
  e testaveis, sem acoplamento entre elas.
- Decisao por TCP unico canal (vs TCP+UDP do RTSP/RTP) simplificou a
  Sprint 1 sem perder requisito.

**O que pode melhorar:**
- O `Client._read_msg` reconstroi `target` para `<channel>` no multicast,
  pois o canal nao e enviado de volta. Em Sprint 2 incluir `channel` no
  `MSG` quando aplicavel.
- Adicionar `pytest-timeout` no Sprint 2 ajuda a evitar test flake em
  cenarios concorrentes.

**Action items para Sprint 2:**
- Adicionar `channel=` ao `MSG` para multicast.
- Cobrir teste de 3 clientes em multicast.
- Cobrir teste de 3 clientes em broadcast.
- Cobrir teste com nomes nao-ASCII (acentos) — apenas se houver tempo.

## Metricas

- Linhas de codigo (src): aproximadamente 700 linhas.
- Testes: 45 (35 unitarios + 10 integracao).
- Cobertura focada em pontos criticos: Lamport, validacao de Message,
  parsing de protocolo, buffer, logs, registro/unicast E2E.
