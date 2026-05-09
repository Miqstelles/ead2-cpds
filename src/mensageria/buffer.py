"""Message buffer com filas por cliente (unicast) e por canal (multicast).

Identifica o produtor em cada mensagem (requisito do enunciado) e mantem
ordem FIFO de chegada por destinatario para o consumo.
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional

from .message import BROADCAST, MULTICAST, UNICAST, Message


class MessageBuffer:
    """Buffer com filas independentes por cliente registrado.

    Estrutura interna:
      _client_queues: nome_cliente -> deque[Message]
      _channels:      canal -> set(nome_cliente)
      _clients:       set(nome_cliente)
    """

    def __init__(self) -> None:
        self._client_queues: Dict[str, deque] = defaultdict(deque)
        self._channels: Dict[str, set] = defaultdict(set)
        self._clients: set = set()
        self._lock = threading.RLock()

    # --- registro de clientes / canais ---

    def register_client(self, name: str) -> None:
        with self._lock:
            if name in self._clients:
                raise ValueError(f"cliente '{name}' ja registrado")
            self._clients.add(name)
            _ = self._client_queues[name]  # cria deque vazio

    def unregister_client(self, name: str) -> None:
        with self._lock:
            self._clients.discard(name)
            self._client_queues.pop(name, None)
            for subs in self._channels.values():
                subs.discard(name)

    def is_registered(self, name: str) -> bool:
        with self._lock:
            return name in self._clients

    def list_clients(self) -> List[str]:
        with self._lock:
            return sorted(self._clients)

    def subscribe(self, client: str, channel: str) -> None:
        with self._lock:
            if client not in self._clients:
                raise ValueError(f"cliente '{client}' nao registrado")
            self._channels[channel].add(client)

    def unsubscribe(self, client: str, channel: str) -> None:
        with self._lock:
            self._channels.get(channel, set()).discard(client)

    def subscribers(self, channel: str) -> List[str]:
        with self._lock:
            return sorted(self._channels.get(channel, set()))

    # --- enfileirar / desenfileirar ---

    def enqueue(self, msg: Message) -> List[str]:
        """Despacha mensagem para as filas dos destinatarios apropriados.

        Retorna a lista de nomes de clientes que receberam copia (para log).
        """
        with self._lock:
            recipients: List[str] = []
            if msg.target_type == UNICAST:
                if msg.target in self._clients:
                    self._client_queues[msg.target].append(msg)
                    recipients.append(msg.target)
            elif msg.target_type == MULTICAST:
                for sub in self._channels.get(msg.target, set()):
                    if sub == msg.producer:
                        continue
                    self._client_queues[sub].append(msg)
                    recipients.append(sub)
            elif msg.target_type == BROADCAST:
                for client in self._clients:
                    if client == msg.producer:
                        continue
                    self._client_queues[client].append(msg)
                    recipients.append(client)
            return recipients

    def dequeue(self, client: str, max_n: Optional[int] = None) -> List[Message]:
        with self._lock:
            if client not in self._clients:
                raise ValueError(f"cliente '{client}' nao registrado")
            q = self._client_queues[client]
            n = len(q) if max_n is None else min(max_n, len(q))
            out: List[Message] = []
            for _ in range(n):
                out.append(q.popleft())
            return out

    def pending_count(self, client: str) -> int:
        with self._lock:
            return len(self._client_queues.get(client, deque()))
