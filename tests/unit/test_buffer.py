from __future__ import annotations

import pytest

from mensageria.buffer import MessageBuffer
from mensageria.message import BROADCAST, MULTICAST, UNICAST, Message


def make_msg(producer, target_type, target, lamport=1):
    return Message(
        producer=producer,
        target_type=target_type,
        target=target,
        payload="x",
        lamport_produced=lamport,
    )


def test_register_e_unregister():
    b = MessageBuffer()
    b.register_client("alice")
    assert b.is_registered("alice")
    assert b.list_clients() == ["alice"]
    b.unregister_client("alice")
    assert not b.is_registered("alice")


def test_register_duplicado_levanta():
    b = MessageBuffer()
    b.register_client("alice")
    with pytest.raises(ValueError):
        b.register_client("alice")


def test_unicast_entrega_apenas_destino():
    b = MessageBuffer()
    b.register_client("alice")
    b.register_client("bob")
    b.register_client("carol")
    msg = make_msg("alice", UNICAST, "bob")
    recipients = b.enqueue(msg)
    assert recipients == ["bob"]
    assert b.pending_count("bob") == 1
    assert b.pending_count("carol") == 0


def test_unicast_destino_nao_registrado_descarta():
    b = MessageBuffer()
    b.register_client("alice")
    msg = make_msg("alice", UNICAST, "ghost")
    assert b.enqueue(msg) == []


def test_multicast_entrega_aos_subscritores_exceto_produtor():
    b = MessageBuffer()
    b.register_client("alice")
    b.register_client("bob")
    b.register_client("carol")
    b.subscribe("bob", "trading")
    b.subscribe("carol", "trading")
    b.subscribe("alice", "trading")  # produtor tambem inscrito; nao recebe copia
    msg = make_msg("alice", MULTICAST, "trading")
    recipients = b.enqueue(msg)
    assert sorted(recipients) == ["bob", "carol"]
    assert b.pending_count("alice") == 0
    assert b.pending_count("bob") == 1
    assert b.pending_count("carol") == 1


def test_broadcast_entrega_a_todos_exceto_produtor():
    b = MessageBuffer()
    for n in ("alice", "bob", "carol"):
        b.register_client(n)
    msg = make_msg("alice", BROADCAST, None)
    recipients = b.enqueue(msg)
    assert sorted(recipients) == ["bob", "carol"]
    assert b.pending_count("alice") == 0


def test_dequeue_retorna_em_ordem_fifo():
    b = MessageBuffer()
    b.register_client("alice")
    b.register_client("bob")
    m1 = make_msg("alice", UNICAST, "bob", lamport=1)
    m2 = make_msg("alice", UNICAST, "bob", lamport=2)
    m3 = make_msg("alice", UNICAST, "bob", lamport=3)
    b.enqueue(m1)
    b.enqueue(m2)
    b.enqueue(m3)
    out = b.dequeue("bob")
    assert [m.lamport_produced for m in out] == [1, 2, 3]
    assert b.pending_count("bob") == 0


def test_dequeue_max_n():
    b = MessageBuffer()
    b.register_client("alice")
    b.register_client("bob")
    for i in range(5):
        b.enqueue(make_msg("alice", UNICAST, "bob", lamport=i + 1))
    out = b.dequeue("bob", max_n=2)
    assert len(out) == 2
    assert b.pending_count("bob") == 3


def test_dequeue_de_cliente_nao_registrado_levanta():
    b = MessageBuffer()
    with pytest.raises(ValueError):
        b.dequeue("ghost")


def test_unsubscribe_para_de_receber():
    b = MessageBuffer()
    b.register_client("alice")
    b.register_client("bob")
    b.subscribe("bob", "ch")
    b.unsubscribe("bob", "ch")
    msg = make_msg("alice", MULTICAST, "ch")
    assert b.enqueue(msg) == []
