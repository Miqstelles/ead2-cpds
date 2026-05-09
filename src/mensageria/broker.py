"""Broker (Message Bus) centralizado.

Aceita conexoes TCP, mantem registro de clientes e canais, roteia mensagens
e mantem seu proprio relogio Lamport. Suporta unicast, multicast e broadcast.

A cada conexao corresponde uma sessao identificada pelo nome do cliente
apos REGISTER. O broker reaproveita o socket TCP da sessao para entregar
mensagens (push) sempre que CONSUME e enviado, em estilo similar ao
servidor RTSP visto em aula.
"""

from __future__ import annotations

import base64
import socket
import threading
from typing import Dict, Optional, Tuple

from . import protocol
from .buffer import MessageBuffer
from .lamport import LamportClock
from .log_manager import LogManager
from .message import BROADCAST, MULTICAST, UNICAST, Message


class Broker:
    """Servidor TCP que faz papel de Message Bus."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000, log_dir: str = "logs") -> None:
        self.host = host
        self.port = port
        self.buffer = MessageBuffer()
        self.clock = LamportClock()
        self.log_manager = LogManager(log_dir=log_dir)
        self._server_socket: Optional[socket.socket] = None
        self._stop_event = threading.Event()
        self._sessions_lock = threading.Lock()
        self._sessions: Dict[str, socket.socket] = {}  # name -> socket
        self._threads: list = []

    # --- ciclo de vida ---

    def start(self) -> Tuple[str, int]:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(8)
        srv.settimeout(0.5)
        self._server_socket = srv
        host, port = srv.getsockname()
        self.host, self.port = host, port
        accept_thread = threading.Thread(target=self._accept_loop, name="broker-accept", daemon=True)
        accept_thread.start()
        self._threads.append(accept_thread)
        return host, port

    def stop(self) -> None:
        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
        with self._sessions_lock:
            for sock in self._sessions.values():
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    sock.close()
                except OSError:
                    pass
            self._sessions.clear()
        for t in self._threads:
            t.join(timeout=1.0)

    # --- loops de aceitacao e atendimento ---

    def _accept_loop(self) -> None:
        assert self._server_socket is not None
        while not self._stop_event.is_set():
            try:
                conn, _addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(target=self._handle_session, args=(conn,), daemon=True)
            t.start()
            self._threads.append(t)

    def _handle_session(self, conn: socket.socket) -> None:
        client_name: Optional[str] = None
        f = conn.makefile("rwb", buffering=0)
        try:
            while not self._stop_event.is_set():
                header = f.readline()
                if not header:
                    break
                header_line = header.decode("utf-8").rstrip("\r\n")
                if not header_line:
                    continue
                verb = header_line.split(maxsplit=1)[0].upper()
                payload_line: Optional[str] = None
                if verb == protocol.SEND:
                    p = f.readline()
                    if not p:
                        break
                    payload_line = p.decode("utf-8").rstrip("\r\n")
                cmd = protocol.parse_command(header_line, payload_line)

                response, new_name = self._dispatch(cmd, conn, client_name)
                if new_name is not None:
                    client_name = new_name
                if response:
                    f.write(response.encode("utf-8"))
                if cmd.verb == protocol.TEARDOWN:
                    break
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            if client_name:
                with self._sessions_lock:
                    self._sessions.pop(client_name, None)
                self.buffer.unregister_client(client_name)
            try:
                f.close()
            except Exception:
                pass
            try:
                conn.close()
            except OSError:
                pass

    # --- dispatcher de comandos ---

    def _dispatch(self, cmd: protocol.Command, conn: socket.socket, current_name: Optional[str]) -> Tuple[str, Optional[str]]:
        verb = cmd.verb

        if verb == protocol.REGISTER:
            return self._handle_register(cmd, conn, current_name)
        if verb == protocol.SUBSCRIBE:
            return self._handle_subscribe(cmd, current_name)
        if verb == protocol.UNSUBSCRIBE:
            return self._handle_unsubscribe(cmd, current_name)
        if verb == protocol.SEND:
            return self._handle_send(cmd, current_name)
        if verb == protocol.CONSUME:
            return self._handle_consume(cmd, current_name)
        if verb == protocol.TEARDOWN:
            return (protocol.format_ok(), current_name)
        return (protocol.format_error(400, f"verbo desconhecido: {verb}"), current_name)

    def _handle_register(self, cmd: protocol.Command, conn: socket.socket, current_name: Optional[str]) -> Tuple[str, Optional[str]]:
        name = cmd.params.get("name")
        if not name:
            return (protocol.format_error(400, "nome obrigatorio"), current_name)
        try:
            self.buffer.register_client(name)
        except ValueError:
            return (protocol.format_error(409, "NAME_TAKEN"), current_name)
        with self._sessions_lock:
            self._sessions[name] = conn
        self.clock.tick()
        return (protocol.format_ok(name=name, lamport=self.clock.now()), name)

    def _handle_subscribe(self, cmd: protocol.Command, current_name: Optional[str]) -> Tuple[str, Optional[str]]:
        if not current_name:
            return (protocol.format_error(401, "nao registrado"), current_name)
        channel = cmd.params.get("channel")
        if not channel:
            return (protocol.format_error(400, "channel obrigatorio"), current_name)
        self.buffer.subscribe(current_name, channel)
        return (protocol.format_ok(channel=channel), current_name)

    def _handle_unsubscribe(self, cmd: protocol.Command, current_name: Optional[str]) -> Tuple[str, Optional[str]]:
        if not current_name:
            return (protocol.format_error(401, "nao registrado"), current_name)
        channel = cmd.params.get("channel")
        if not channel:
            return (protocol.format_error(400, "channel obrigatorio"), current_name)
        self.buffer.unsubscribe(current_name, channel)
        return (protocol.format_ok(channel=channel), current_name)

    def _handle_send(self, cmd: protocol.Command, current_name: Optional[str]) -> Tuple[str, Optional[str]]:
        if not current_name:
            return (protocol.format_error(401, "nao registrado"), current_name)
        try:
            target_type = cmd.params["target_type"].upper()
            target_param = cmd.params.get("target", "*")
            lamport_prod = int(cmd.params["lamport"])
            encrypted = protocol.parse_bool(cmd.params.get("encrypted", "false"))
        except (KeyError, ValueError) as e:
            return (protocol.format_error(400, f"parametros invalidos: {e}"), current_name)

        if cmd.payload is None:
            return (protocol.format_error(400, "payload ausente"), current_name)
        try:
            payload_text = base64.b64decode(cmd.payload.encode("ascii")).decode("utf-8")
        except Exception:
            return (protocol.format_error(400, "payload base64 invalido"), current_name)

        target: Optional[str]
        if target_type == BROADCAST:
            target = None
        else:
            if not target_param or target_param == "*":
                return (protocol.format_error(400, "target obrigatorio"), current_name)
            target = target_param

        try:
            msg = Message(
                producer=current_name,
                target_type=target_type,
                target=target,
                payload=payload_text,
                lamport_produced=lamport_prod,
                encrypted=encrypted,
            )
        except ValueError as e:
            return (protocol.format_error(400, str(e)), current_name)

        new_clock = self.clock.receive(lamport_prod)
        msg.lamport_buffered = new_clock

        if target_type == UNICAST and not self.buffer.is_registered(target):  # type: ignore[arg-type]
            return (protocol.format_error(404, "destinatario nao registrado"), current_name)

        self.buffer.enqueue(msg)
        self.log_manager.log_production(msg)
        return (protocol.format_ok(msg_id=msg.msg_id, lamport_buf=new_clock), current_name)

    def _handle_consume(self, cmd: protocol.Command, current_name: Optional[str]) -> Tuple[str, Optional[str]]:
        if not current_name:
            return (protocol.format_error(401, "nao registrado"), current_name)
        max_n: Optional[int] = None
        if "max" in cmd.params:
            try:
                max_n = int(cmd.params["max"])
            except ValueError:
                return (protocol.format_error(400, "max invalido"), current_name)

        msgs = self.buffer.dequeue(current_name, max_n=max_n)
        out_lines: list = [protocol.format_ok(count=len(msgs))]
        # Carimbar com o lamport do consumidor antes de enviar (server-side
        # tambem registra para audit; consumidor pode atualizar seu proprio relogio)
        for m in msgs:
            cons_ts = self.clock.receive(m.lamport_buffered or 0)
            self.log_manager.log_consumption(m, current_name, cons_ts)
            payload_b64 = base64.b64encode(m.payload.encode("utf-8")).decode("ascii")
            channel = m.target if m.target_type == MULTICAST else None
            out_lines.append(
                protocol.format_msg(
                    msg_id=m.msg_id,
                    producer=m.producer,
                    target_type=m.target_type,
                    lamport_prod=m.lamport_produced,
                    lamport_buf=m.lamport_buffered or 0,
                    encrypted=m.encrypted,
                    payload_b64=payload_b64,
                    channel=channel,
                )
            )
        return ("".join(out_lines), current_name)
