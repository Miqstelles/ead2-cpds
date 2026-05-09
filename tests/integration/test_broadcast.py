"""Testes de integracao para broadcast (US08).

Cobre:
  - broadcast entrega a todos os clientes registrados, exceto o produtor
  - cliente recem-registrado depois do broadcast nao recebe (apenas os que
    estavam registrados no momento do envio recebem)
  - logs registram BROADCAST como target_type
"""

from __future__ import annotations

import os

from mensageria.client import Client


def test_broadcast_entrega_a_todos_exceto_produtor(broker):
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b, \
         Client("carol", host=broker.host, port=broker.port) as c:
        a.register()
        b.register()
        c.register()

        a.send_broadcast("aviso geral")

        msgs_a = a.consume()
        msgs_b = b.consume()
        msgs_c = c.consume()

    assert msgs_a == []
    assert len(msgs_b) == 1 and msgs_b[0].payload == "aviso geral"
    assert len(msgs_c) == 1 and msgs_c[0].payload == "aviso geral"
    assert msgs_b[0].target_type == "BROADCAST"
    assert msgs_b[0].target is None


def test_broadcast_log_registra_target_type(broker, tmp_log_dir):
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        a.send_broadcast("alo")
        b.consume()

    prod = open(os.path.join(tmp_log_dir, "production.log"), encoding="utf-8").read()
    assert "BROADCAST" in prod
    # target em broadcast e gravado como '*'
    assert ",BROADCAST,*," in prod


def test_broadcast_com_5_clientes(broker):
    """Confirma fan-out para varios destinatarios em uma unica chamada."""
    names = ["alice", "bob", "carol", "dave", "eve"]
    clients = [Client(n, host=broker.host, port=broker.port) for n in names]
    try:
        for cl in clients:
            cl.connect()
            cl.register()
        producer = clients[0]
        producer.send_broadcast("hello-all")
        # Cada um dos demais consome 1 mensagem; o produtor consome 0
        consumed = [cl.consume() for cl in clients]
    finally:
        for cl in clients:
            try:
                cl.teardown()
            except Exception:
                pass
            cl.close()

    assert consumed[0] == []  # produtor nao recebe
    for got in consumed[1:]:
        assert len(got) == 1
        assert got[0].payload == "hello-all"
        assert got[0].producer == "alice"


def test_broadcast_para_si_proprio_quando_unico_cliente_e_noop(broker):
    """Se nao existe ninguem alem do produtor, broadcast nao entrega a ninguem."""
    with Client("alice", host=broker.host, port=broker.port) as a:
        a.register()
        a.send_broadcast("perdido no vazio")
        msgs = a.consume()
    assert msgs == []
