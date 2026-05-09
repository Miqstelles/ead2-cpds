from __future__ import annotations

import threading

import pytest

from mensageria.lamport import LamportClock


def test_inicio_em_zero():
    c = LamportClock()
    assert c.now() == 0


def test_tick_incrementa():
    c = LamportClock()
    assert c.tick() == 1
    assert c.tick() == 2
    assert c.now() == 2


def test_send_e_alias_de_tick():
    c = LamportClock()
    assert c.send() == 1
    assert c.now() == 1


def test_receive_aplica_max_mais_um():
    c = LamportClock(initial=5)
    # Mensagem com timestamp menor: max(5, 3) + 1 = 6
    assert c.receive(3) == 6
    # Mensagem com timestamp maior: max(6, 20) + 1 = 21
    assert c.receive(20) == 21


def test_receive_negativo_levanta():
    c = LamportClock()
    with pytest.raises(ValueError):
        c.receive(-1)


def test_inicial_negativo_levanta():
    with pytest.raises(ValueError):
        LamportClock(initial=-1)


def test_thread_safety_increments():
    c = LamportClock()
    n_threads = 8
    per_thread = 1000

    def worker():
        for _ in range(per_thread):
            c.tick()

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert c.now() == n_threads * per_thread
