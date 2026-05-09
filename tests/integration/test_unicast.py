"""Testes de integracao para envio/consumo unicast (US02, US03, US04, US05).

Cobre tambem:
  - carimbo Lamport em produtor / broker / consumidor
  - presenca de logs production.log e consumption.log
  - identificacao de produtor na mensagem armazenada
  - isolamento entre destinatarios
"""

from __future__ import annotations

import os

import pytest

from mensageria.client import Client, ClientError


def test_unicast_chega_apenas_ao_destinatario(broker):
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b, \
         Client("carol", host=broker.host, port=broker.port) as c:
        a.register()
        b.register()
        c.register()

        a.send_unicast("bob", "ola bob")

        msgs_bob = b.consume()
        msgs_carol = c.consume()

        assert len(msgs_bob) == 1
        assert msgs_bob[0].payload == "ola bob"
        assert msgs_bob[0].producer == "alice"
        assert msgs_carol == []


def test_unicast_para_destino_nao_registrado_falha(broker):
    with Client("alice", host=broker.host, port=broker.port) as a:
        a.register()
        with pytest.raises(ClientError):
            a.send_unicast("ghost", "x")


def test_lamport_carimbado_em_3_pontos(broker):
    """Produtor carimba; broker re-carimba ao bufferizar; consumidor re-carimba ao consumir.
    Os tres carimbos devem estar definidos e em sequencia coerente.
    """
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()

        a.send_unicast("bob", "msg1")

        msgs = b.consume()
        assert len(msgs) == 1
        m = msgs[0]
        assert m.lamport_produced >= 1
        assert m.lamport_buffered is not None
        assert m.lamport_consumed is not None
        # Regra Lamport receive: max(local, msg) + 1 — o consumidor deve estar > buffered
        assert m.lamport_consumed > m.lamport_buffered


def test_logs_de_producao_e_consumo_registrados(broker, tmp_log_dir):
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()

        a.send_unicast("bob", "msg-a")
        a.send_unicast("bob", "msg-b")
        b.consume()  # forca log de consumo

    prod = open(os.path.join(tmp_log_dir, "production.log"), encoding="utf-8").read()
    cons = open(os.path.join(tmp_log_dir, "consumption.log"), encoding="utf-8").read()

    # Header + 2 linhas de producao (uma por send)
    prod_lines = [l for l in prod.strip().split("\n") if l]
    cons_lines = [l for l in cons.strip().split("\n") if l]
    assert len(prod_lines) == 1 + 2  # header + 2 mensagens
    assert len(cons_lines) == 1 + 2  # header + 2 mensagens consumidas
    assert "alice" in prod
    assert "bob" in cons
    assert "UNICAST" in prod


def test_consumidor_recebe_em_ordem_fifo(broker):
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        for i in range(5):
            a.send_unicast("bob", f"m{i}")
        msgs = b.consume()
    assert [m.payload for m in msgs] == ["m0", "m1", "m2", "m3", "m4"]
    # Lamport produzidos crescem monotonicamente para o mesmo produtor
    lps = [m.lamport_produced for m in msgs]
    assert lps == sorted(lps)


def test_producer_identificado_no_buffer(broker):
    """Confere requisito do enunciado: 'mensagem armazenada em message buffer
    identificando o produtor'."""
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        a.send_unicast("bob", "x")
        # Inspeciona o buffer interno do broker antes do consumo
        assert broker.buffer.pending_count("bob") == 1
        msgs = b.consume()
        assert msgs[0].producer == "alice"


def test_consumidor_identificado_e_carimbo_no_log(broker, tmp_log_dir):
    """Confere requisito: 'quando consumida deve identificar o consumidor
    e mais um carimbo logico'."""
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        a.send_unicast("bob", "x")
        b.consume()

    cons = open(os.path.join(tmp_log_dir, "consumption.log"), encoding="utf-8").read()
    last = cons.strip().split("\n")[-1].split(",")
    # CSV: iso_ts, lamport_cons, msg_id, consumer, producer, lamport_prod, lamport_buf
    assert last[3] == "bob"        # consumidor identificado
    assert last[4] == "alice"
    assert int(last[1]) > 0        # lamport_cons (carimbo logico) presente
