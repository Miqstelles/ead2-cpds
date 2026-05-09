"""Relogio logico de Lamport.

Cada processo (produtor, broker, consumidor) mantem seu proprio relogio.
Regras (Lamport, 1978):
  - Evento local: L = L + 1
  - Send: L = L + 1; envia mensagem com timestamp = L
  - Receive: L = max(L, L_msg) + 1
"""

from __future__ import annotations

import threading


class LamportClock:
    """Relogio logico de Lamport thread-safe."""

    def __init__(self, initial: int = 0) -> None:
        if initial < 0:
            raise ValueError("Relogio inicial nao pode ser negativo")
        self._value = initial
        self._lock = threading.Lock()

    def tick(self) -> int:
        """Incrementa para evento local e retorna o novo valor."""
        with self._lock:
            self._value += 1
            return self._value

    def send(self) -> int:
        """Incrementa antes de enviar uma mensagem; retorna timestamp a embarcar."""
        return self.tick()

    def receive(self, received_ts: int) -> int:
        """Atualiza relogio ao receber mensagem: max(local, recebido) + 1."""
        if received_ts < 0:
            raise ValueError("Timestamp recebido nao pode ser negativo")
        with self._lock:
            self._value = max(self._value, received_ts) + 1
            return self._value

    def now(self) -> int:
        """Le o valor atual sem alterar."""
        with self._lock:
            return self._value
