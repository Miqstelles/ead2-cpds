"""Testes de integracao para multicast (US06, US07).

Cobre:
  - subscribe / unsubscribe em canais nomeados
  - multicast entrega aos subscritores e nao a quem nao esta inscrito
  - produtor inscrito no proprio canal nao recebe a propria mensagem
  - canal vem preservado no MSG entregue ao consumidor (Sprint 2)
  - cenario com 3+ clientes em paralelo
"""

from __future__ import annotations

from mensageria.client import Client


def test_multicast_entrega_apenas_aos_subscritores(broker):
    """3 clientes registrados; 2 inscritos no canal 'trading'.
    O nao-inscrito nao deve receber a mensagem."""
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b, \
         Client("carol", host=broker.host, port=broker.port) as c:
        a.register()
        b.register()
        c.register()

        b.subscribe("trading")
        c.subscribe("trading")
        # alice nao subscreve

        a.send_multicast("trading", "preco subiu")

        msgs_b = b.consume()
        msgs_c = c.consume()
        msgs_a = a.consume()

    assert len(msgs_b) == 1
    assert len(msgs_c) == 1
    assert msgs_a == []
    assert msgs_b[0].payload == "preco subiu"
    assert msgs_b[0].producer == "alice"
    assert msgs_b[0].target_type == "MULTICAST"
    assert msgs_b[0].target == "trading"  # canal preservado no MSG (Sprint 2)


def test_multicast_produtor_nao_recebe_a_propria_mensagem_no_canal(broker):
    """Produtor pode estar inscrito no canal mas nao recebe sua propria mensagem."""
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        a.subscribe("ch")
        b.subscribe("ch")
        a.send_multicast("ch", "hello")
        msgs_a = a.consume()
        msgs_b = b.consume()
    assert msgs_a == []
    assert len(msgs_b) == 1


def test_multicast_unsubscribe_para_de_receber(broker):
    """Cliente que se desinscreve para de receber mensagens do canal."""
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        b.subscribe("news")

        a.send_multicast("news", "primeira")
        first = b.consume()
        assert len(first) == 1

        b.unsubscribe("news")
        a.send_multicast("news", "segunda")
        second = b.consume()
    assert second == []


def test_multicast_4_clientes_em_paralelo(broker):
    """Cenario com 4 clientes: 1 produtor, 3 consumidores em 2 canais distintos."""
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b, \
         Client("carol", host=broker.host, port=broker.port) as c, \
         Client("dave", host=broker.host, port=broker.port) as d:
        for cl in (a, b, c, d):
            cl.register()
        b.subscribe("ch1")
        c.subscribe("ch1")
        d.subscribe("ch2")
        a.send_multicast("ch1", "para-bob-e-carol")
        a.send_multicast("ch2", "para-dave")

        m_b = b.consume()
        m_c = c.consume()
        m_d = d.consume()

    assert [m.payload for m in m_b] == ["para-bob-e-carol"]
    assert [m.payload for m in m_c] == ["para-bob-e-carol"]
    assert [m.payload for m in m_d] == ["para-dave"]
    # Mesmo conteudo entregue a bob e carol => mesmo msg_id (mesma mensagem original)
    assert m_b[0].msg_id == m_c[0].msg_id


def test_multicast_lamport_estritamente_crescente_no_consumidor(broker):
    """Cinco mensagens em sequencia produzidas por alice; bob (subscritor)
    deve consumir com lamport_consumed estritamente crescente."""
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        b.subscribe("k")
        for i in range(5):
            a.send_multicast("k", f"m{i}")
        msgs = b.consume()
    cons = [m.lamport_consumed for m in msgs]
    assert cons == sorted(cons)
    assert len(set(cons)) == len(cons)  # estritamente crescente (sem repeticoes)
