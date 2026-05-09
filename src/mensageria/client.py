"""Cliente de mensageria.

Mantem um socket TCP com o broker, seu proprio relogio Lamport, e oferece
metodos para registrar, enviar (unicast/multicast/broadcast) e consumir.
"""

from __future__ import annotations

import base64
import socket
from typing import List, Optional, Tuple

from . import protocol
from .lamport import LamportClock
from .message import BROADCAST, MULTICAST, UNICAST, Message


class ClientError(Exception):
    pass


class Client:
    """Cliente sincrono baseado em sockets TCP."""

    def __init__(self, name: str, host: str = "127.0.0.1", port: int = 9000) -> None:
        self.name = name
        self.host = host
        self.port = port
        self.clock = LamportClock()
        self._sock: Optional[socket.socket] = None
        self._fp = None  # buffered file-like

    # --- conexao ---

    def connect(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self._sock = s
        self._fp = s.makefile("rwb", buffering=0)

    def close(self) -> None:
        if self._fp is not None:
            try:
                self._fp.close()
            except Exception:
                pass
            self._fp = None
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def __enter__(self) -> "Client":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self.teardown()
        except Exception:
            pass
        self.close()

    # --- comandos ---

    def register(self) -> dict:
        self._send_line(protocol.format_register(self.name))
        status, params = self._read_status()
        if status != 200:
            raise ClientError(f"registro falhou: {status} {params}")
        self.clock.tick()
        return params

    def subscribe(self, channel: str) -> None:
        self._send_line(protocol.format_subscribe(channel))
        status, params = self._read_status()
        if status != 200:
            raise ClientError(f"subscribe falhou: {status} {params}")
        self.clock.tick()

    def unsubscribe(self, channel: str) -> None:
        self._send_line(protocol.format_unsubscribe(channel))
        status, params = self._read_status()
        if status != 200:
            raise ClientError(f"unsubscribe falhou: {status} {params}")
        self.clock.tick()

    def send_unicast(self, target: str, payload: str, encrypted: bool = False) -> dict:
        return self._send(UNICAST, target, payload, encrypted)

    def send_multicast(self, channel: str, payload: str, encrypted: bool = False) -> dict:
        return self._send(MULTICAST, channel, payload, encrypted)

    def send_broadcast(self, payload: str, encrypted: bool = False) -> dict:
        return self._send(BROADCAST, None, payload, encrypted)

    def _send(self, target_type: str, target: Optional[str], payload: str, encrypted: bool) -> dict:
        ts = self.clock.send()
        b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
        self._send_line(
            protocol.format_send(
                target_type=target_type,
                target=target,
                lamport=ts,
                encrypted=encrypted,
                payload_b64=b64,
            )
        )
        status, params = self._read_status()
        if status != 200:
            raise ClientError(f"send falhou: {status} {params}")
        return params

    def consume(self, max_n: Optional[int] = None) -> List[Message]:
        self._send_line(protocol.format_consume(max_n))
        status, params = self._read_status()
        if status != 200:
            raise ClientError(f"consume falhou: {status} {params}")
        count = int(params.get("count", "0"))
        msgs: List[Message] = []
        for _ in range(count):
            msgs.append(self._read_msg())
        return msgs

    def teardown(self) -> None:
        if self._sock is None:
            return
        try:
            self._send_line(protocol.format_teardown())
            self._read_status()
        except (OSError, ClientError):
            pass

    # --- I/O ---

    def _send_line(self, data: str) -> None:
        if self._fp is None:
            raise ClientError("cliente nao conectado")
        self._fp.write(data.encode("utf-8"))

    def _read_line(self) -> str:
        if self._fp is None:
            raise ClientError("cliente nao conectado")
        raw = self._fp.readline()
        if not raw:
            raise ClientError("conexao fechada pelo servidor")
        return raw.decode("utf-8").rstrip("\r\n")

    def _read_status(self) -> Tuple[int, dict]:
        line = self._read_line()
        parts = line.split(maxsplit=2)
        if not parts:
            raise ClientError("resposta vazia")
        try:
            code = int(parts[0])
        except ValueError:
            raise ClientError(f"resposta nao reconhecida: {line}")
        params = {}
        if len(parts) >= 3 and "=" in parts[2]:
            params = protocol.parse_kv(parts[2].split())
        elif len(parts) >= 3:
            params = {"_text": parts[2]}
        return code, params

    def _read_msg(self) -> Message:
        head = self._read_line()
        tokens = head.split()
        if not tokens or tokens[0] != protocol.MSG:
            raise ClientError(f"esperava MSG, recebi {head!r}")
        params = protocol.parse_kv(tokens[1:])
        payload_b64 = self._read_line()
        end = self._read_line()
        if end != protocol.END:
            raise ClientError(f"esperava END, recebi {end!r}")
        payload_text = base64.b64decode(payload_b64.encode("ascii")).decode("utf-8")
        target_type = params["target_type"]
        # Reconstroi target a partir do contexto:
        #   - UNICAST: o destinatario somos nos
        #   - MULTICAST: canal vem em params["channel"]
        #   - BROADCAST: nao tem target especifico
        if target_type == UNICAST:
            target: Optional[str] = self.name
        elif target_type == MULTICAST:
            target = params.get("channel", "<channel>")
        else:
            target = None
        msg = Message(
            producer=params["producer"],
            target_type=target_type,
            target=target,
            payload=payload_text,
            lamport_produced=int(params["lamport_prod"]),
            encrypted=protocol.parse_bool(params.get("encrypted", "false")),
            msg_id=params["msg_id"],
            lamport_buffered=int(params["lamport_buf"]),
        )
        # Atualiza relogio do consumidor: max(local, lamport_buf) + 1
        cons_ts = self.clock.receive(msg.lamport_buffered or 0)
        msg.lamport_consumed = cons_ts
        msg.consumer = self.name
        return msg
