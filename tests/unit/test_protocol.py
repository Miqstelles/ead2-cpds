from __future__ import annotations

import pytest

from mensageria import protocol


def test_parse_register():
    cmd = protocol.parse_command("REGISTER name=alice")
    assert cmd.verb == "REGISTER"
    assert cmd.params == {"name": "alice"}
    assert cmd.payload is None


def test_parse_send_com_payload():
    cmd = protocol.parse_command(
        "SEND target_type=UNICAST target=bob lamport=3 encrypted=false",
        payload_line="aGVsbG8=",
    )
    assert cmd.verb == "SEND"
    assert cmd.params["target_type"] == "UNICAST"
    assert cmd.params["target"] == "bob"
    assert cmd.params["lamport"] == "3"
    assert cmd.payload == "aGVsbG8="


def test_format_register_termina_com_newline():
    s = protocol.format_register("alice")
    assert s.endswith("\n")
    assert "REGISTER" in s
    assert "name=alice" in s


def test_format_send_inclui_payload_em_linha_separada():
    s = protocol.format_send("UNICAST", "bob", 1, False, "Zg==")
    lines = s.strip().split("\n")
    assert len(lines) == 2
    assert lines[0].startswith("SEND")
    assert lines[1] == "Zg=="


def test_format_msg_termina_com_END():
    s = protocol.format_msg(
        msg_id="abc",
        producer="alice",
        target_type="UNICAST",
        lamport_prod=1,
        lamport_buf=2,
        encrypted=False,
        payload_b64="Zg==",
    )
    assert s.endswith("END\n")


def test_format_msg_inclui_channel_quando_multicast():
    s = protocol.format_msg(
        msg_id="abc",
        producer="alice",
        target_type="MULTICAST",
        lamport_prod=1,
        lamport_buf=2,
        encrypted=False,
        payload_b64="Zg==",
        channel="trading",
    )
    assert "channel=trading" in s


def test_format_msg_omite_channel_quando_nao_informado():
    s = protocol.format_msg(
        msg_id="abc",
        producer="alice",
        target_type="UNICAST",
        lamport_prod=1,
        lamport_buf=2,
        encrypted=False,
        payload_b64="Zg==",
    )
    assert "channel=" not in s


def test_parse_bool():
    assert protocol.parse_bool("true") is True
    assert protocol.parse_bool("True") is True
    assert protocol.parse_bool("1") is True
    assert protocol.parse_bool("false") is False
    assert protocol.parse_bool("0") is False


def test_parse_command_vazio_levanta():
    with pytest.raises(ValueError):
        protocol.parse_command("")
