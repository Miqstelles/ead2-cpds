# Sprint 2 — Multicast / Broadcast / Canais

**Periodo:** 1 semana (planejada)
**Sprint Goal:** Habilitar comunicacao em grupo (multicast em canais nomeados)
e difusao geral (broadcast), com cobertura de testes em cenarios de 3+
clientes simultaneos.

## Sprint Backlog

| ID   | User Story                                                           | Estimativa |
|------|----------------------------------------------------------------------|------------|
| US06 | Criar/subscrever/desinscrever em canais nomeados                     | M          |
| US07 | Enviar mensagem multicast em um canal                                | M          |
| US08 | Enviar broadcast a todos os registrados                              | S          |
| US09 | Consumir mensagens da minha fila (polling)                           | S          |

## Acao tecnica adicional (carry-over Sprint 1)

A retro da Sprint 1 anotou que o `Client._read_msg` ficava com `target =
"<channel>"` em multicast porque o canal nao era enviado de volta no `MSG`.
Sprint 2 corrige:

- `protocol.format_msg` agora aceita `channel: Optional[str]` opcional.
- `broker.py` inclui `channel=` no `MSG` quando `target_type == MULTICAST`.
- `client.py._read_msg` parseia `channel` e atribui a `Message.target`.

## Daily (resumo)

- D1: planning + atualizacao do MSG com `channel=`
- D2: implementacao de testes de multicast (5 casos)
- D3: implementacao de testes de broadcast (4 casos)
- D4: implementacao de testes de canais (5 casos)
- D5: cenario de 5 clientes em broadcast e 4 em multicast
- D6: documentacao + atualizacao de backlog
- D7: review + retro

## Sprint Review

- **Demos:**
  - 4 clientes (alice/bob/carol/dave) em 2 canais distintos: cada um recebe
    apenas a mensagem do canal em que esta inscrito.
  - 5 clientes em broadcast: todos recebem exceto o produtor.
  - Logs em `production.log` mostram `BROADCAST` e `MULTICAST` como
    `target_type`, com `target=*` para broadcast e `target=<canal>` para
    multicast.
  - `lamport_consumed` estritamente crescente para um mesmo consumidor que
    recebe varias mensagens em sequencia.
- **Aceito pelo PO:** sim.

## Sprint Retro

**O que foi bem:**
- A abstracao de `MessageBuffer` ja preparada para multicast/broadcast desde
  a Sprint 1 simplificou o trabalho — boa parte foi "ligar fios".
- O ajuste do `MSG` com `channel=` foi incremental e nao quebrou testes
  anteriores.
- Cenario de 5 clientes (`test_broadcast_com_5_clientes`) deu confianca de
  que o thread-per-connection do broker aguenta paralelismo razoavel.

**O que pode melhorar:**
- Falta um teste explicito de concorrencia "alice envia enquanto bob consome"
  — todos os testes atuais sao serializados. Considerar para Sprint 3.
- O codigo do CLI nao tem teste; manualmente verificado, mas seria bom
  cobrir o REPL via subprocess (escopo futuro).

**Action items para Sprint 3:**
- Reusar `pgp_chat` (crypto_adapter) para suportar `--encrypt` no CLI.
- Garantir que broker nao decifra (so roteia) — teste de opacidade do
  payload no broker.
- Atualizar `protocolo-de-testes.md` com a saida final completa.
- Tag `v1.0.0` na entrega final.

## Metricas

- Linhas adicionais de codigo (src): aprox. 40 linhas (ajuste de protocol/broker/client).
- Testes adicionados: 16 (2 unitarios + 14 integracao).
- Testes totais apos Sprint 2: **61 verdes** (37 unitarios + 24 integracao).
- Tempo de execucao: aprox. 13s.
