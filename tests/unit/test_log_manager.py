from __future__ import annotations

import os

from mensageria.log_manager import LogManager
from mensageria.message import UNICAST, Message


def test_logs_criam_arquivos_com_header(tmp_path):
    lm = LogManager(log_dir=str(tmp_path))
    assert os.path.exists(lm.production_path)
    assert os.path.exists(lm.consumption_path)
    prod = lm.read_production()
    cons = lm.read_consumption()
    assert prod.startswith("iso_ts,lamport_prod,lamport_buf")
    assert cons.startswith("iso_ts,lamport_cons,msg_id")


def test_log_production_escreve_linha_csv(tmp_path):
    lm = LogManager(log_dir=str(tmp_path))
    m = Message(producer="alice", target_type=UNICAST, target="bob", payload="oi", lamport_produced=3)
    m.lamport_buffered = 5
    lm.log_production(m)
    content = lm.read_production()
    lines = content.strip().split("\n")
    assert len(lines) == 2  # header + 1 linha
    last = lines[-1].split(",")
    assert last[1] == "3"
    assert last[2] == "5"
    assert last[4] == "alice"
    assert last[5] == "UNICAST"
    assert last[6] == "bob"
    assert last[7] == "false"


def test_log_consumption_escreve_linha_csv(tmp_path):
    lm = LogManager(log_dir=str(tmp_path))
    m = Message(producer="alice", target_type=UNICAST, target="bob", payload="oi", lamport_produced=3)
    m.lamport_buffered = 5
    lm.log_consumption(m, consumer="bob", lamport_consumed=8)
    lines = lm.read_consumption().strip().split("\n")
    assert len(lines) == 2
    last = lines[-1].split(",")
    assert last[1] == "8"
    assert last[3] == "bob"
    assert last[4] == "alice"
    assert last[5] == "3"
    assert last[6] == "5"
