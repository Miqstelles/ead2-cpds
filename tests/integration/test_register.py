"""Testes de integracao para REGISTER (US01).

Sobe um broker em porta efemera e conecta clientes reais via TCP.
"""

from __future__ import annotations

import pytest

from mensageria.client import Client, ClientError


def test_registro_unico_funciona(broker):
    with Client("alice", host=broker.host, port=broker.port) as c:
        params = c.register()
        assert params["name"] == "alice"


def test_registro_duplicado_e_rejeitado(broker):
    with Client("alice", host=broker.host, port=broker.port) as c1:
        c1.register()
        with Client("alice", host=broker.host, port=broker.port) as c2:
            with pytest.raises(ClientError) as exc:
                c2.register()
            assert "NAME_TAKEN" in str(exc.value) or "409" in str(exc.value)


def test_dois_clientes_diferentes_coexistem(broker):
    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        # Sem excecoes -> sucesso. Confirma no broker.
        assert sorted(broker.buffer.list_clients()) == ["alice", "bob"]
