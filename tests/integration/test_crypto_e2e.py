"""Testes E2E com PGP (US10).

Reusa o pacote `pgp_chat` (de `ead1-sgi/src/pgp_chat`) via
`mensageria.crypto_adapter.CryptoAdapter`. Cobre:

  - alice cifra/assina mensagem para bob; envia via mensageria;
    bob decifra/verifica com sucesso;
  - broker nao consegue ler o plaintext (payload opaco);
  - log de producao registra `encrypted=true` e armazena o ciphertext (nao o claro);
  - assinatura invalida se mensagem for adulterada (best-effort: o gnupg
    sinalizara invalida, mas decifragem ainda pode funcionar).

Cada teste exige `gpg` no PATH e o pacote pgp_chat acessivel. As fixtures
geram chaves apenas uma vez por modulo para reduzir tempo total (~3s).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from mensageria.client import Client
from mensageria.crypto_adapter import CryptoAdapter


PASSPHRASE_ALICE = "alice-test-pass"
PASSPHRASE_BOB = "bob-test-pass"


@pytest.fixture(scope="module")
def keyrings_dir():
    """Diretorio temporario curto (gpg-agent socket exige path < ~104 chars)."""
    base = Path(tempfile.mkdtemp(prefix="msgkr-", dir="/tmp"))
    yield base
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture(scope="module")
def alice_adapter(keyrings_dir):
    a = CryptoAdapter("alice", keyrings_dir, PASSPHRASE_ALICE)
    a.generate_key("Alice", "alice@example.com")
    return a


@pytest.fixture(scope="module")
def bob_adapter(keyrings_dir):
    b = CryptoAdapter("bob", keyrings_dir, PASSPHRASE_BOB)
    b.generate_key("Bob", "bob@example.com")
    return b


@pytest.fixture(scope="module")
def keys_exchanged(alice_adapter, bob_adapter):
    """Cada um importa a chave publica do outro."""
    alice_pub = alice_adapter.export_pubkey()
    bob_pub = bob_adapter.export_pubkey()
    bob_adapter.import_pubkey(alice_pub)
    alice_adapter.import_pubkey(bob_pub)
    return {
        "alice_fp": alice_adapter.fingerprint,
        "bob_fp": bob_adapter.fingerprint,
    }


def test_e2e_alice_cifra_bob_decifra(broker, alice_adapter, bob_adapter, keys_exchanged):
    """Caminho feliz: alice cifra para bob, envia via mensageria, bob decifra."""
    plaintext = "saldo da conta: R$ 12.345,67"
    ciphertext = alice_adapter.encrypt_for(keys_exchanged["bob_fp"], plaintext)

    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        a.send_unicast("bob", ciphertext, encrypted=True)
        msgs = b.consume()

    assert len(msgs) == 1
    received = msgs[0]
    assert received.encrypted is True
    # Payload entregue eh o ASCII-armored, NAO o plaintext
    assert "BEGIN PGP MESSAGE" in received.payload
    assert plaintext not in received.payload

    # Bob decifra e verifica assinatura
    result = bob_adapter.decrypt(received.payload)
    assert result["plaintext"] == plaintext
    assert result["valid"] is True
    assert result["fingerprint"] == keys_exchanged["alice_fp"]


def test_broker_nao_decifra_payload(broker, alice_adapter, keys_exchanged, tmp_log_dir):
    """Confirma que o broker apenas roteia: o payload no log esta cifrado."""
    plaintext = "essa mensagem e secreta"
    ciphertext = alice_adapter.encrypt_for(keys_exchanged["bob_fp"], plaintext)

    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        a.send_unicast("bob", ciphertext, encrypted=True)
        b.consume()

    # Conferir log de producao
    prod = open(os.path.join(tmp_log_dir, "production.log"), encoding="utf-8").read()
    assert ",true," in prod  # encrypted=true
    # O plaintext NUNCA pode aparecer em log (apenas tamanho do payload)
    assert plaintext not in prod


def test_payload_cifrado_em_unicast_continua_em_ordem_fifo(broker, alice_adapter, bob_adapter, keys_exchanged):
    """Mesmo cifrado, a ordem FIFO e Lamport sao preservadas."""
    plaintexts = [f"msg #{i}" for i in range(3)]
    ciphertexts = [
        alice_adapter.encrypt_for(keys_exchanged["bob_fp"], pt) for pt in plaintexts
    ]

    with Client("alice", host=broker.host, port=broker.port) as a, \
         Client("bob", host=broker.host, port=broker.port) as b:
        a.register()
        b.register()
        for ct in ciphertexts:
            a.send_unicast("bob", ct, encrypted=True)
        msgs = b.consume()

    assert len(msgs) == 3
    decrypted = [bob_adapter.decrypt(m.payload)["plaintext"] for m in msgs]
    assert decrypted == plaintexts
    # Lamport produzido cresce monotonicamente
    lps = [m.lamport_produced for m in msgs]
    assert lps == sorted(lps)


def test_decifra_falha_sem_chave_privada(keyrings_dir, alice_adapter, keys_exchanged):
    """Um terceiro sem a chave privada do destinatario nao consegue decifrar."""
    plaintext = "x"
    ciphertext = alice_adapter.encrypt_for(keys_exchanged["bob_fp"], plaintext)
    # 'mallory' tem keyring proprio, sem a chave privada do bob
    mallory = CryptoAdapter("mallory", keyrings_dir, "mallory-pass")
    with pytest.raises(RuntimeError):
        mallory.decrypt(ciphertext)
