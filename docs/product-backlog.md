# Product Backlog

Backlog ordenado por valor / dependencia. Sprints de 1 semana cada.

## User Stories

| ID  | Como    | Quero                                                      | Para que                                | Sprint | Status        |
|-----|---------|------------------------------------------------------------|------------------------------------------|--------|---------------|
| US01| cliente | registrar-me com nome unico no broker                      | ser identificado nas mensagens           | 1      | DONE          |
| US02| cliente | enviar mensagem unicast a outro cliente nomeado            | comunicacao ponto-a-ponto                | 1      | DONE          |
| US03| sistema | carimbar mensagens com Lamport em producao/buffer/consumo  | garantir ordem parcial                   | 1      | DONE          |
| US04| auditor | ler logs de producao e consumo                             | conferir entregas e ordem                | 1      | DONE          |
| US05| sistema | armazenar mensagens em buffer identificando produtor       | rastreabilidade                          | 1      | DONE          |
| US06| cliente | criar/subscrever/desinscrever em canais nomeados           | comunicacao em grupo                     | 2      | DONE          |
| US07| cliente | enviar mensagem multicast em um canal                      | publicar a um grupo                      | 2      | DONE          |
| US08| cliente | enviar broadcast a todos os registrados                    | difusao geral                            | 2      | DONE          |
| US09| cliente | consumir mensagens da minha fila (polling)                 | receber o que foi enviado                | 2      | DONE          |
| US10| cliente | cifrar payload com PGP do destinatario                     | confidencialidade ponto-a-ponto          | 3      | TODO          |
| US11| sistema | ter testes unitarios, integracao e E2E executados          | qualidade verificavel                    | 3      | EM ANDAMENTO  |
| US12| usuario | ter README, docs de arquitetura, protocolo e testes        | manutenibilidade                         | 3      | EM ANDAMENTO  |

## Definicao de Pronto (DoD)

Uma user story so e considerada DONE quando:
1. Codigo implementado e revisado.
2. Testes (unitarios e/ou integracao) cobrindo o caminho feliz e ao menos um
   caminho de erro.
3. Suite `pytest -v` verde.
4. Documentacao mencionando o comportamento em `docs/`.
5. Commit no Git com mensagem clara.

## Riscos e dependencias

- **R1**: `python-gnupg` exige `gpg` no PATH. Mitigacao: testar em ambiente
  limpo antes da Sprint 3.
- **R2**: Testes concorrentes podem ser flaky em CI. Mitigacao: timeouts +
  fixtures que aguardam estado estavel.
- **R3**: Rede em testes de integracao usa porta efemera (`port=0`) — sem
  risco de colisao em CI.

## Glossario

- **Unicast**: mensagem direcionada a um cliente nomeado.
- **Multicast**: mensagem direcionada a um canal; entregue a todos os
  subscritores do canal.
- **Broadcast**: mensagem direcionada a todos os clientes registrados,
  exceto o produtor.
- **Lamport clock**: contador logico que estabelece ordem parcial entre
  eventos de processos diferentes.
