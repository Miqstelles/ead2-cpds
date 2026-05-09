# Protocolo de Testes

Documenta a estrategia, os casos cobertos e a saida real da execucao da
suite de testes ao final das Sprints 1, 2 e 3.

## Estrategia

- **Unitarios**: validam classes isoladas (Lamport, Message, Protocol,
  MessageBuffer, LogManager). Sem rede, sem IO de socket.
- **Integracao**: sobem broker em porta efemera (`port=0`) e usam `Client`
  real conectando via TCP em `127.0.0.1`. Cobrem registro, envio e consumo
  unicast/multicast/broadcast E2E.
- **E2E com PGP**: alem do broker em TCP, usam keyrings reais com gpg
  (geracao de pares RSA, exportacao/importacao, cifragem+assinatura,
  decifragem+verificacao). Confirmam **opacidade** do payload no broker.

Toda a suite roda com:

```bash
python3 -m pytest -v
```

## Casos cobertos

### Unitarios (37)

**LamportClock (7):** inicio em zero · tick incrementa · send alias · receive
  aplica `max(local, recebido)+1` · receive negativo levanta · inicial
  negativo levanta · thread safety (8x1000 ticks).

**Message (8):** unicast/multicast exigem target · broadcast zera target ·
  target_type invalido · serializacao round-trip JSON · payload_bytes UTF-8 ·
  producer obrigatorio · lamport negativo invalido.

**Protocol (9):** parse REGISTER · parse SEND com payload · format_register ·
  format_send · format_msg termina com END · **format_msg inclui channel
  para multicast** · **format_msg omite channel quando nao informado** ·
  parse_bool · comando vazio levanta.

**MessageBuffer (10):** register/unregister · register duplicado levanta ·
  unicast entrega apenas ao destino · destino nao-registrado descarta ·
  multicast entrega aos subscritores · broadcast entrega a todos exceto
  produtor · dequeue FIFO · dequeue max_n · dequeue cliente nao-registrado
  levanta · unsubscribe.

**LogManager (3):** criam arquivos com header · log_production CSV correto ·
  log_consumption CSV correto.

### Integracao (28)

**REGISTER (3):** registro unico · duplicado rejeitado (409) · dois
  clientes coexistem.

**UNICAST (7):** chega apenas ao destinatario · destino nao-registrado
  retorna erro · Lamport carimbado em 3 pontos · logs gerados · ordem FIFO ·
  produtor identificado no buffer · consumidor identificado + carimbo no log.

**MULTICAST (5):** entrega apenas aos subscritores · produtor inscrito nao
  recebe a propria mensagem · unsubscribe para de receber · 4 clientes em 2
  canais distintos · `lamport_consumed` estritamente crescente.

**BROADCAST (4):** entrega a todos exceto produtor · log com target=* ·
  cenario com 5 clientes em paralelo · broadcast solitario e' noop.

**CANAIS (5):** subscribe idempotente · unsubscribe noop · canais isolados ·
  nomes alfanumericos com hifen/underscore/ponto · SUBSCRIBE sem REGISTER
  retorna 401.

**PGP E2E (4):** alice cifra+assina, bob decifra+verifica · broker nao
  decifra (payload opaco em log) · ordem FIFO preservada com cifragem ·
  decifra falha sem chave privada.

## Mapeamento user-story -> testes

| US   | Testes que cobrem                                                                       |
|------|----------------------------------------------------------------------------------------|
| US01 | test_register::* (3) + test_buffer::test_register_*                                    |
| US02 | test_unicast::test_unicast_chega_*, test_unicast::test_unicast_para_destino_*, test_buffer::test_unicast_* |
| US03 | test_unicast::test_lamport_carimbado_em_3_pontos, test_lamport::test_receive_*, test_lamport::test_thread_safety |
| US04 | test_unicast::test_logs_*, test_unicast::test_consumidor_identificado_*, test_log_manager::*                  |
| US05 | test_unicast::test_producer_identificado_no_buffer, test_buffer::test_unicast_entrega_apenas_destino          |
| US06 | test_channels::* (5)                                                                                          |
| US07 | test_multicast::* (5)                                                                                         |
| US08 | test_broadcast::* (4)                                                                                         |
| US09 | test_unicast::test_consumidor_recebe_em_ordem_fifo, test_buffer::test_dequeue_*                              |
| US10 | test_crypto_e2e::* (4)                                                                                        |
| US11 | toda a suite (65 testes verdes)                                                                              |
| US12 | docs/* presentes                                                                                              |

## Saida real (final, Sprint 3)

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/miqueiastelles/Documents/ead2-cpds
configfile: pyproject.toml
testpaths: tests
collecting ... collected 65 items

tests/integration/test_broadcast.py::test_broadcast_entrega_a_todos_exceto_produtor PASSED [  1%]
tests/integration/test_broadcast.py::test_broadcast_log_registra_target_type PASSED [  3%]
tests/integration/test_broadcast.py::test_broadcast_com_5_clientes PASSED [  4%]
tests/integration/test_broadcast.py::test_broadcast_para_si_proprio_quando_unico_cliente_e_noop PASSED [  6%]
tests/integration/test_channels.py::test_subscribe_idempotente PASSED    [  7%]
tests/integration/test_channels.py::test_unsubscribe_de_canal_nao_subscrito_e_noop PASSED [  9%]
tests/integration/test_channels.py::test_dois_canais_isolados PASSED     [ 10%]
tests/integration/test_channels.py::test_canal_com_caracteres_validos PASSED [ 12%]
tests/integration/test_channels.py::test_subscribe_antes_de_register_falha PASSED [ 13%]
tests/integration/test_crypto_e2e.py::test_e2e_alice_cifra_bob_decifra PASSED [ 15%]
tests/integration/test_crypto_e2e.py::test_broker_nao_decifra_payload PASSED [ 16%]
tests/integration/test_crypto_e2e.py::test_payload_cifrado_em_unicast_continua_em_ordem_fifo PASSED [ 18%]
tests/integration/test_crypto_e2e.py::test_decifra_falha_sem_chave_privada PASSED [ 20%]
tests/integration/test_multicast.py::test_multicast_entrega_apenas_aos_subscritores PASSED [ 21%]
tests/integration/test_multicast.py::test_multicast_produtor_nao_recebe_a_propria_mensagem_no_canal PASSED [ 23%]
tests/integration/test_multicast.py::test_multicast_unsubscribe_para_de_receber PASSED [ 24%]
tests/integration/test_multicast.py::test_multicast_4_clientes_em_paralelo PASSED [ 26%]
tests/integration/test_multicast.py::test_multicast_lamport_estritamente_crescente_no_consumidor PASSED [ 27%]
tests/integration/test_register.py::test_registro_unico_funciona PASSED  [ 29%]
tests/integration/test_register.py::test_registro_duplicado_e_rejeitado PASSED [ 30%]
tests/integration/test_register.py::test_dois_clientes_diferentes_coexistem PASSED [ 32%]
tests/integration/test_unicast.py::test_unicast_chega_apenas_ao_destinatario PASSED [ 33%]
tests/integration/test_unicast.py::test_unicast_para_destino_nao_registrado_falha PASSED [ 35%]
tests/integration/test_unicast.py::test_lamport_carimbado_em_3_pontos PASSED [ 36%]
tests/integration/test_unicast.py::test_logs_de_producao_e_consumo_registrados PASSED [ 38%]
tests/integration/test_unicast.py::test_consumidor_recebe_em_ordem_fifo PASSED [ 40%]
tests/integration/test_unicast.py::test_producer_identificado_no_buffer PASSED [ 41%]
tests/integration/test_unicast.py::test_consumidor_identificado_e_carimbo_no_log PASSED [ 43%]
tests/unit/test_buffer.py::test_register_e_unregister PASSED             [ 44%]
tests/unit/test_buffer.py::test_register_duplicado_levanta PASSED        [ 46%]
tests/unit/test_buffer.py::test_unicast_entrega_apenas_destino PASSED    [ 47%]
tests/unit/test_buffer.py::test_unicast_destino_nao_registrado_descarta PASSED [ 49%]
tests/unit/test_buffer.py::test_multicast_entrega_aos_subscritores_exceto_produtor PASSED [ 50%]
tests/unit/test_buffer.py::test_broadcast_entrega_a_todos_exceto_produtor PASSED [ 52%]
tests/unit/test_buffer.py::test_dequeue_retorna_em_ordem_fifo PASSED     [ 53%]
tests/unit/test_buffer.py::test_dequeue_max_n PASSED                     [ 55%]
tests/unit/test_buffer.py::test_dequeue_de_cliente_nao_registrado_levanta PASSED [ 56%]
tests/unit/test_buffer.py::test_unsubscribe_para_de_receber PASSED       [ 58%]
tests/unit/test_lamport.py::test_inicio_em_zero PASSED                   [ 60%]
tests/unit/test_lamport.py::test_tick_incrementa PASSED                  [ 61%]
tests/unit/test_lamport.py::test_send_e_alias_de_tick PASSED             [ 63%]
tests/unit/test_lamport.py::test_receive_aplica_max_mais_um PASSED       [ 64%]
tests/unit/test_lamport.py::test_receive_negativo_levanta PASSED         [ 66%]
tests/unit/test_lamport.py::test_inicial_negativo_levanta PASSED         [ 67%]
tests/unit/test_lamport.py::test_thread_safety_increments PASSED         [ 69%]
tests/unit/test_log_manager.py::test_logs_criam_arquivos_com_header PASSED [ 70%]
tests/unit/test_log_manager.py::test_log_production_escreve_linha_csv PASSED [ 72%]
tests/unit/test_log_manager.py::test_log_consumption_escreve_linha_csv PASSED [ 73%]
tests/unit/test_message.py::test_unicast_exige_target PASSED             [ 75%]
tests/unit/test_message.py::test_multicast_exige_target PASSED           [ 76%]
tests/unit/test_message.py::test_broadcast_zera_target PASSED            [ 78%]
tests/unit/test_message.py::test_target_type_invalido PASSED             [ 80%]
tests/unit/test_message.py::test_serializacao_round_trip PASSED          [ 81%]
tests/unit/test_message.py::test_payload_bytes_conta_utf8 PASSED         [ 83%]
tests/unit/test_message.py::test_producer_obrigatorio PASSED             [ 84%]
tests/unit/test_message.py::test_lamport_negativo_invalido PASSED        [ 86%]
tests/unit/test_protocol.py::test_parse_register PASSED                  [ 87%]
tests/unit/test_protocol.py::test_parse_send_com_payload PASSED          [ 89%]
tests/unit/test_protocol.py::test_format_register_termina_com_newline PASSED [ 90%]
tests/unit/test_protocol.py::test_format_send_inclui_payload_em_linha_separada PASSED [ 92%]
tests/unit/test_protocol.py::test_format_msg_termina_com_END PASSED      [ 93%]
tests/unit/test_protocol.py::test_format_msg_inclui_channel_quando_multicast PASSED [ 95%]
tests/unit/test_protocol.py::test_format_msg_omite_channel_quando_nao_informado PASSED [ 96%]
tests/unit/test_protocol.py::test_parse_bool PASSED                      [ 98%]
tests/unit/test_protocol.py::test_parse_command_vazio_levanta PASSED     [100%]

============================= 65 passed in 18.51s ==============================
```

**Resultado: 65 passed em 18,51s.**

## Cenarios manuais (smoke test)

Roteiro reproduzivel para validar fora dos testes automatizados:

1. **Iniciar broker** em terminal A:
   ```bash
   python3 -m mensageria.cli broker --port 9000
   ```
2. **Cliente bob** em terminal B:
   ```bash
   python3 -m mensageria.cli client --name bob --repl
   ```
3. **Cliente alice** em terminal C:
   ```bash
   python3 -m mensageria.cli client --name alice --repl
   ```
4. **Cliente carol** em terminal D:
   ```bash
   python3 -m mensageria.cli client --name carol --repl
   ```
5. Em alice: `send bob ola bob`
6. Em alice: `bcast aviso geral`
7. Em bob: `sub trading`
8. Em carol: `sub trading`
9. Em alice: `cast trading preco subiu`
10. Em bob/carol: `consume`
11. Em terminal E:
   ```bash
   cat logs/production.log
   cat logs/consumption.log
   ```

**Resultado esperado:**
- bob recebe a mensagem unicast, o broadcast e a mensagem multicast.
- carol recebe o broadcast e a mensagem multicast (nao o unicast).
- `production.log` mostra 3 linhas (1 UNICAST, 1 BROADCAST, 1 MULTICAST).
- `consumption.log` mostra 5 linhas (3 entregas para bob + 2 para carol).
- Lamport monotonico crescente em cada cliente individual.
