"""Modelo de mensagem trocada entre clientes via broker.

Padroniza o formato (requisito 2 do PDF Mensageria) e e serializavel em JSON
para transito sobre o canal TCP.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Optional


UNICAST = "UNICAST"
MULTICAST = "MULTICAST"
BROADCAST = "BROADCAST"

VALID_TARGET_TYPES = frozenset({UNICAST, MULTICAST, BROADCAST})


def _new_msg_id() -> str:
    return str(uuid.uuid4())


@dataclass
class Message:
    """Mensagem com metadados de Lamport e identificacao de produtor/consumidor."""

    producer: str
    target_type: str
    target: Optional[str]
    payload: str
    lamport_produced: int
    encrypted: bool = False
    msg_id: str = field(default_factory=_new_msg_id)
    lamport_buffered: Optional[int] = None
    lamport_consumed: Optional[int] = None
    consumer: Optional[str] = None

    def __post_init__(self) -> None:
        if self.target_type not in VALID_TARGET_TYPES:
            raise ValueError(
                f"target_type invalido: {self.target_type!r}. "
                f"Esperado um de {sorted(VALID_TARGET_TYPES)}"
            )
        if self.target_type == BROADCAST:
            if self.target not in (None, "", "*"):
                raise ValueError("BROADCAST nao deve ter target especifico")
            self.target = None
        else:
            if not self.target:
                raise ValueError(f"{self.target_type} exige target nao-vazio")
        if not self.producer:
            raise ValueError("producer e obrigatorio")
        if self.lamport_produced < 0:
            raise ValueError("lamport_produced nao pode ser negativo")

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "Message":
        data = json.loads(raw)
        return cls(**data)

    def payload_bytes(self) -> int:
        return len(self.payload.encode("utf-8"))
