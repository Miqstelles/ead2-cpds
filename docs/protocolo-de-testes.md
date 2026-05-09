# Protocolo de Testes

Documenta a estrategia, os casos cobertos e a saida real da execucao da
suite de testes ao final da Sprint 1.

## Estrategia

- **Unitarios**: validam classes isoladas (Lamport, Message, Protocol,
  MessageBuffer, LogManager). Sem rede, sem IO de socket.
- **Integracao**: sobem broker em porta efemera (`port=0`) e usam
  `Client` real conectando via TCP em `127.0.0.1`. Cobrem registro,
  envio e consumo unicast E2E, alem de validar logs e Lamport.

Toda a suite roda com:

```bash
python3 -m pytest -v
```

## Casos cobertos na Sprint 1

### Unitarios (35)

**LamportClock (7):**
- inicio em zero
- tick incrementa
- send e alias de tick
- receive aplica `max(local, recebido) + 1`
- receive negativo levanta `ValueError`
- inicial negativo levanta `ValueError`
- thread safety (8 threads x 1000 ticks => valor final correto)

**Message (8):**
- unicast/multicast exigem target
- broadcast zera target ("*" -> None)
- target_type invalido levanta
- serializacao round-trip JSON
- payload_bytes conta corretamente UTF-8
- producer obrigatorio
- lamport negativo invalido

**Protocol (7):**
- parse REGISTER
- parse SEND com payload em linha subsequente
- format_register termina com newline
- format_send inclui payload em linha separada
- format_msg termina com `END\n`
- parse_bool aceita variantes
- comando vazio levanta `ValueError`

**MessageBuffer (10):**
- register/unregister
- register duplicado levanta
- unicast entrega apenas ao destino
- unicast para destino nao-registrado descarta
- multicast entrega aos subscritores (exceto produtor)
- broadcast entrega a todos exceto produtor
- dequeue em ordem FIFO
- dequeue com `max_n`
- dequeue de cliente nao registrado levanta
- unsubscribe para de receber

**LogManager (3):**
- logs criam arquivos com header
- log_production escreve linha CSV correta
- log_consumption escreve linha CSV correta

### Integracao (10)

**REGISTER (3):**
- registro unico funciona
- registro duplicado e rejeitado (409 NAME_TAKEN)
- dois clientes diferentes coexistem

**UNICAST (7):**
- chega apenas ao destinatario (carol nao recebe)
- destino nao registrado retorna erro
- Lamport carimbado em produtor / broker / consumidor
- logs de producao e consumo registrados
- consumidor recebe em ordem FIFO
- produtor identificado no buffer
- consumidor identificado + carimbo logico no log

## Mapeamento user-story -> testes

| US   | Testes que cobrem                                                                     |
|------|--------------------------------------------------------------------------------------|
| US01 | test_registro_unico_funciona, test_registro_duplicado_e_rejeitado, test_dois_clientes_diferentes_coexistem, test_register_duplicado_levanta |
| US02 | test_unicast_chega_apenas_ao_destinatario, test_unicast_para_destino_nao_registrado_falha, test_unicast_entrega_apenas_destino |
| US03 | test_lamport_carimbado_em_3_pontos, test_receive_aplica_max_mais_um, test_thread_safety_increments |
| US04 | test_logs_de_producao_e_consumo_registrados, test_consumidor_identificado_e_carimbo_no_log, test_log_production_escreve_linha_csv, test_log_consumption_escreve_linha_csv |
| US05 | test_producer_identificado_no_buffer, test_unicast_entrega_apenas_destino |
| US09 | test_consumidor_recebe_em_ordem_fifo, test_dequeue_retorna_em_ordem_fifo, test_dequeue_max_n |

## Saida real (Sprint 1)

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Applications/Xcode.app/Contents/Developer/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/miqueiastelles/Documents/ead2-cpds
configfile: pyproject.toml
testpaths: tests
collecting ... collected 45 items

tests/integration/test_register.py::test_registro_unico_funciona PASSED  [  2%]
tests/integration/test_register.py::test_registro_duplicado_e_rejeitado PASSED [  4%]
tests/integration/test_register.py::test_dois_clientes_diferentes_coexistem PASSED [  6%]
tests/integration/test_unicast.py::test_unicast_chega_apenas_ao_destinatario PASSED [  8%]
tests/integration/test_unicast.py::test_unicast_para_destino_nao_registrado_falha PASSED [ 11%]
tests/integration/test_unicast.py::test_lamport_carimbado_em_3_pontos PASSED [ 13%]
tests/integration/test_unicast.py::test_logs_de_producao_e_consumo_registrados PASSED [ 15%]
tests/integration/test_unicast.py::test_consumidor_recebe_em_ordem_fifo PASSED [ 17%]
tests/integration/test_unicast.py::test_producer_identificado_no_buffer PASSED [ 20%]
tests/integration/test_unicast.py::test_consumidor_identificado_e_carimbo_no_log PASSED [ 22%]
tests/unit/test_buffer.py::test_register_e_unregister PASSED             [ 24%]
tests/unit/test_buffer.py::test_register_duplicado_levanta PASSED        [ 26%]
tests/unit/test_buffer.py::test_unicast_entrega_apenas_destino PASSED    [ 28%]
tests/unit/test_buffer.py::test_unicast_destino_nao_registrado_descarta PASSED [ 31%]
tests/unit/test_buffer.py::test_multicast_entrega_aos_subscritores_exceto_produtor PASSED [ 33%]
tests/unit/test_buffer.py::test_broadcast_entrega_a_todos_exceto_produtor PASSED [ 35%]
tests/unit/test_buffer.py::test_dequeue_retorna_em_ordem_fifo PASSED     [ 37%]
tests/unit/test_buffer.py::test_dequeue_max_n PASSED                     [ 40%]
tests/unit/test_buffer.py::test_dequeue_de_cliente_nao_registrado_levanta PASSED [ 42%]
tests/unit/test_buffer.py::test_unsubscribe_para_de_receber PASSED       [ 44%]
tests/unit/test_lamport.py::test_inicio_em_zero PASSED                   [ 46%]
tests/unit/test_lamport.py::test_tick_incrementa PASSED                  [ 48%]
tests/unit/test_lamport.py::test_send_e_alias_de_tick PASSED             [ 51%]
tests/unit/test_lamport.py::test_receive_aplica_max_mais_um PASSED       [ 53%]
tests/unit/test_lamport.py::test_receive_negativo_levanta PASSED         [ 55%]
tests/unit/test_lamport.py::test_inicial_negativo_levanta PASSED         [ 57%]
tests/unit/test_lamport.py::test_thread_safety_increments PASSED         [ 60%]
tests/unit/test_log_manager.py::test_logs_criam_arquivos_com_header PASSED [ 62%]
tests/unit/test_log_manager.py::test_log_production_escreve_linha_csv PASSED [ 64%]
tests/unit/test_log_manager.py::test_log_consumption_escreve_linha_csv PASSED [ 66%]
tests/unit/test_message.py::test_unicast_exige_target PASSED             [ 68%]
tests/unit/test_message.py::test_multicast_exige_target PASSED           [ 71%]
tests/unit/test_message.py::test_broadcast_zera_target PASSED            [ 73%]
tests/unit/test_message.py::test_target_type_invalido PASSED             [ 75%]
tests/unit/test_message.py::test_serializacao_round_trip PASSED          [ 77%]
tests/unit/test_message.py::test_payload_bytes_conta_utf8 PASSED         [ 80%]
tests/unit/test_message.py::test_producer_obrigatorio PASSED             [ 82%]
tests/unit/test_message.py::test_lamport_negativo_invalido PASSED        [ 84%]
tests/unit/test_protocol.py::test_parse_register PASSED                  [ 86%]
tests/unit/test_protocol.py::test_parse_send_com_payload PASSED          [ 88%]
tests/unit/test_protocol.py::test_format_register_termina_com_newline PASSED [ 91%]
tests/unit/test_protocol.py::test_format_send_inclui_payload_em_linha_separada PASSED [ 93%]
tests/unit/test_protocol.py::test_format_msg_termina_com_END PASSED      [ 95%]
tests/unit/test_protocol.py::test_parse_bool PASSED                      [ 97%]
tests/unit/test_protocol.py::test_parse_command_vazio_levanta PASSED     [100%]

============================== 45 passed in 5.64s ==============================
```

**Resultado: 45 passed em 5.64s.**

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
4. Em alice:
   ```
   alice> send bob ola bob
   ```
5. Em bob:
   ```
   bob> consume
   ```
6. Em terminal D:
   ```bash
   cat logs/production.log
   cat logs/consumption.log
   ```

**Resultado esperado:**
- `production.log` mostra 1 linha alice/UNICAST/bob com `lamport_prod` e `lamport_buf` definidos.
- `consumption.log` mostra 1 linha bob/alice com `lamport_cons` > `lamport_buf`.

## Cobertura de Sprints futuras

A Sprint 2 adicionara casos para multicast, broadcast e canais. A Sprint 3
adicionara casos E2E com PGP (verificacao de opacidade do payload no
broker e correta cifra/decifra entre alice e bob).
