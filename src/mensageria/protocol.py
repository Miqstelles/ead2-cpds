"""Protocolo de aplicacao linha-orientado entre cliente e broker.

Formato dos comandos (cada comando inicia em uma linha de cabecalho;
quando ha payload binario, ele segue em uma unica linha codificada base64).

  REGISTER name=<str>
  SUBSCRIBE channel=<str>
  UNSUBSCRIBE channel=<str>
  SEND target_type=<UNICAST|MULTICAST|BROADCAST> target=<str|*> lamport=<int> encrypted=<true|false>
  <payload-base64-em-uma-linha>
  CONSUME [max=<int>]
  TEARDOWN

Respostas do broker sao texto plano:

  200 OK [k=v ...]
  4XX/5XX <descricao>

Para entrega de mensagem ao consumidor (apos CONSUME):

  MSG msg_id=<uuid> producer=<str> target_type=<...> lamport_prod=<int> lamport_buf=<int> encrypted=<bool>
  <payload-base64>
  END

A escolha por linha-orientado segue o estilo RTSP visto em aula
(Client.py / ServerWorker.py do material RTP/RTSP) e simplifica parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


REGISTER = "REGISTER"
SUBSCRIBE = "SUBSCRIBE"
UNSUBSCRIBE = "UNSUBSCRIBE"
SEND = "SEND"
CONSUME = "CONSUME"
TEARDOWN = "TEARDOWN"
MSG = "MSG"
END = "END"

LINE_SEP = "\n"


@dataclass
class Command:
    """Representa um comando parseado vindo do cliente."""

    verb: str
    params: dict
    payload: Optional[str] = None  # base64 em uma linha, quando aplicavel


def parse_kv(tokens: list) -> dict:
    """Converte tokens 'k=v' em dict; ignora tokens sem '='."""
    out = {}
    for tok in tokens:
        if "=" in tok:
            k, _, v = tok.partition("=")
            out[k] = v
    return out


def parse_command(header_line: str, payload_line: Optional[str] = None) -> Command:
    """Parseia uma linha de cabecalho de comando.

    header_line: ex. 'SEND target_type=UNICAST target=bob lamport=3 encrypted=false'
    payload_line: linha imediatamente subsequente, presente quando o verbo e SEND
    """
    tokens = header_line.strip().split()
    if not tokens:
        raise ValueError("Comando vazio")
    verb = tokens[0].upper()
    params = parse_kv(tokens[1:])
    payload = payload_line.strip() if payload_line is not None else None
    return Command(verb=verb, params=params, payload=payload)


def format_register(name: str) -> str:
    return f"{REGISTER} name={name}{LINE_SEP}"


def format_subscribe(channel: str) -> str:
    return f"{SUBSCRIBE} channel={channel}{LINE_SEP}"


def format_unsubscribe(channel: str) -> str:
    return f"{UNSUBSCRIBE} channel={channel}{LINE_SEP}"


def format_send(target_type: str, target: Optional[str], lamport: int, encrypted: bool, payload_b64: str) -> str:
    tgt = target if target else "*"
    enc = "true" if encrypted else "false"
    head = f"{SEND} target_type={target_type} target={tgt} lamport={lamport} encrypted={enc}"
    return f"{head}{LINE_SEP}{payload_b64}{LINE_SEP}"


def format_consume(max_n: Optional[int] = None) -> str:
    if max_n is None:
        return f"{CONSUME}{LINE_SEP}"
    return f"{CONSUME} max={max_n}{LINE_SEP}"


def format_teardown() -> str:
    return f"{TEARDOWN}{LINE_SEP}"


def format_ok(**kv) -> str:
    extras = " ".join(f"{k}={v}" for k, v in kv.items())
    return f"200 OK{(' ' + extras) if extras else ''}{LINE_SEP}"


def format_error(code: int, description: str) -> str:
    return f"{code} {description}{LINE_SEP}"


def format_msg(
    msg_id: str,
    producer: str,
    target_type: str,
    lamport_prod: int,
    lamport_buf: int,
    encrypted: bool,
    payload_b64: str,
    channel: Optional[str] = None,
) -> str:
    enc = "true" if encrypted else "false"
    parts = [
        f"msg_id={msg_id}",
        f"producer={producer}",
        f"target_type={target_type}",
        f"lamport_prod={lamport_prod}",
        f"lamport_buf={lamport_buf}",
        f"encrypted={enc}",
    ]
    if channel:
        parts.append(f"channel={channel}")
    head = f"{MSG} " + " ".join(parts)
    return f"{head}{LINE_SEP}{payload_b64}{LINE_SEP}{END}{LINE_SEP}"


def parse_bool(s: str) -> bool:
    return s.lower() in ("true", "1", "yes")
