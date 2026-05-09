"""Logs simples (arquivos texto, nao DB) de producao e consumo.

Formato CSV append-only para conferencia:

  production.log:
    iso_ts,lamport_prod,lamport_buf,msg_id,producer,target_type,target,encrypted,payload_bytes

  consumption.log:
    iso_ts,lamport_cons,msg_id,consumer,producer,lamport_prod,lamport_buf
"""

from __future__ import annotations

import os
import threading
from datetime import datetime
from typing import Optional

from .message import Message


PRODUCTION_HEADER = (
    "iso_ts,lamport_prod,lamport_buf,msg_id,producer,target_type,target,encrypted,payload_bytes\n"
)
CONSUMPTION_HEADER = "iso_ts,lamport_cons,msg_id,consumer,producer,lamport_prod,lamport_buf\n"


class LogManager:
    """Gerencia escrita atomica de logs de producao e consumo."""

    def __init__(self, log_dir: str = "logs") -> None:
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.production_path = os.path.join(self.log_dir, "production.log")
        self.consumption_path = os.path.join(self.log_dir, "consumption.log")
        self._lock = threading.Lock()
        self._ensure_header(self.production_path, PRODUCTION_HEADER)
        self._ensure_header(self.consumption_path, CONSUMPTION_HEADER)

    @staticmethod
    def _ensure_header(path: str, header: str) -> None:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(header)

    @staticmethod
    def _iso_now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def log_production(self, msg: Message) -> None:
        if msg.lamport_buffered is None:
            raise ValueError("lamport_buffered deve estar definido antes do log de producao")
        target = msg.target if msg.target is not None else "*"
        line = (
            f"{self._iso_now()},{msg.lamport_produced},{msg.lamport_buffered},"
            f"{msg.msg_id},{msg.producer},{msg.target_type},{target},"
            f"{str(msg.encrypted).lower()},{msg.payload_bytes()}\n"
        )
        with self._lock:
            with open(self.production_path, "a", encoding="utf-8") as f:
                f.write(line)

    def log_consumption(self, msg: Message, consumer: str, lamport_consumed: int) -> None:
        line = (
            f"{self._iso_now()},{lamport_consumed},{msg.msg_id},{consumer},"
            f"{msg.producer},{msg.lamport_produced},{msg.lamport_buffered}\n"
        )
        with self._lock:
            with open(self.consumption_path, "a", encoding="utf-8") as f:
                f.write(line)

    def read_production(self) -> str:
        with open(self.production_path, "r", encoding="utf-8") as f:
            return f.read()

    def read_consumption(self) -> str:
        with open(self.consumption_path, "r", encoding="utf-8") as f:
            return f.read()
