"""Fixtures compartilhadas pelos testes de integracao."""

from __future__ import annotations

import os
import sys
import time

import pytest

# Garante que src/ esta no PYTHONPATH para `import mensageria`
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from mensageria.broker import Broker  # noqa: E402


@pytest.fixture()
def tmp_log_dir(tmp_path):
    d = tmp_path / "logs"
    d.mkdir()
    return str(d)


@pytest.fixture()
def broker(tmp_log_dir):
    """Sobe um broker em porta efemera (port=0) e o derruba ao fim do teste."""
    b = Broker(host="127.0.0.1", port=0, log_dir=tmp_log_dir)
    host, port = b.start()
    # Pequeno aguardo para garantir que o accept_loop ja esta rodando
    time.sleep(0.05)
    yield b
    b.stop()
