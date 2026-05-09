from __future__ import annotations

import json

import pytest

from mensageria.message import BROADCAST, MULTICAST, UNICAST, Message


def test_unicast_exige_target():
    with pytest.raises(ValueError):
        Message(producer="alice", target_type=UNICAST, target=None, payload="oi", lamport_produced=1)


def test_multicast_exige_target():
    with pytest.raises(ValueError):
        Message(producer="alice", target_type=MULTICAST, target="", payload="oi", lamport_produced=1)


def test_broadcast_zera_target():
    m = Message(producer="alice", target_type=BROADCAST, target="*", payload="oi", lamport_produced=1)
    assert m.target is None


def test_target_type_invalido():
    with pytest.raises(ValueError):
        Message(producer="alice", target_type="ANYCAST", target="bob", payload="oi", lamport_produced=1)


def test_serializacao_round_trip():
    m = Message(
        producer="alice",
        target_type=UNICAST,
        target="bob",
        payload="ola",
        lamport_produced=3,
        encrypted=False,
    )
    raw = m.to_json()
    data = json.loads(raw)
    assert data["producer"] == "alice"
    assert data["target"] == "bob"
    m2 = Message.from_json(raw)
    assert m2.msg_id == m.msg_id
    assert m2.payload == "ola"


def test_payload_bytes_conta_utf8():
    m = Message(producer="a", target_type=UNICAST, target="b", payload="ç", lamport_produced=1)
    # 'ç' em UTF-8 = 2 bytes
    assert m.payload_bytes() == 2


def test_producer_obrigatorio():
    with pytest.raises(ValueError):
        Message(producer="", target_type=UNICAST, target="b", payload="x", lamport_produced=1)


def test_lamport_negativo_invalido():
    with pytest.raises(ValueError):
        Message(producer="a", target_type=UNICAST, target="b", payload="x", lamport_produced=-1)
