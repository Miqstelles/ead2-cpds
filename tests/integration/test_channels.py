"""Testes de integracao para nomeacao e gestao de canais (US06).

Cobre:
  - subscribe pode ser chamado multiplas vezes sem efeito colateral (idempotente)
  - unsubscribe em canal nao subscrito nao falha
  - dois canais distintos sao isolados
  - nome de canal arbitrario (alfanumerico, com hifen, com underscore)
"""

from __future__ import annotations

from mensageria.client import Client


def test_subscribe_idempotente(broker):
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        b.subscribe("ch")
        b.subscribe("ch")  # nao deve falhar
        a.send_multicast("ch", "x")
        msgs = b.consume()
    assert len(msgs) == 1


def test_unsubscribe_de_canal_nao_subscrito_e_noop(broker):
    with Client("alice", host=broker.host, port=broker.port) as a:
        a.register()
        a.unsubscribe("inexistente")  # nao deve falhar


def test_dois_canais_isolados(broker):
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b, \
         Client("carol", host=broker.host, port=broker.port) as c:
        a.register()
        b.register()
        c.register()
        b.subscribe("ch-a")
        c.subscribe("ch-b")
        a.send_multicast("ch-a", "para-bob")
        a.send_multicast("ch-b", "para-carol")
        m_b = b.consume()
        m_c = c.consume()
    assert [m.payload for m in m_b] == ["para-bob"]
    assert [m.payload for m in m_c] == ["para-carol"]


def test_canal_com_caracteres_validos(broker):
    """Nome de canal aceita alfanumerico, hifen, underscore, ponto."""
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        for ch in ("ch_1", "ch-2", "ch.3", "Ch4"):
            b.subscribe(ch)
            a.send_multicast(ch, ch)
        msgs = b.consume()
    payloads = sorted(m.payload for m in msgs)
    assert payloads == ["Ch4", "ch-2", "ch.3", "ch_1"]


def test_subscribe_antes_de_register_falha(broker):
    """SUBSCRIBE sem REGISTER previo deve retornar 401."""
    from mensageria.client import ClientError

    import pytest

    with Client("ghost", host=broker.host, port=broker.port) as g:
        with pytest.raises(ClientError):
            g.subscribe("ch")
