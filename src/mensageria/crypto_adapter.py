"""Adaptador de criptografia que reutiliza o pacote `pgp_chat` do projeto SGI.

Reuso direto das classes/funcoes implementadas em
`/Users/miqueiastelles/Documents/ead1-sgi/src/pgp_chat/`
(geracao de chaves, exportacao/importacao, cifra+assinatura, decifra+verificacao).

A localizacao do pgp_chat e descoberta na seguinte ordem:
  1. `import pgp_chat` (caso instalado via `pip install -e ../ead1-sgi`).
  2. Caminho relativo `../ead1-sgi/src/` em relacao a este arquivo (default
     para o ambiente do aluno em /Users/miqueiastelles/Documents/).
  3. Variavel de ambiente PGP_CHAT_PATH apontando para o diretorio `src`.

A classe `CryptoAdapter` encapsula:
  - keyring isolado por usuario (vide `pgp_chat.storage.get_gpg`)
  - geracao de par de chaves (RSA 2048 por padrao)
  - cifra e assinatura para um destinatario
  - decifra e verificacao da assinatura
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def _bootstrap_pgp_chat() -> None:
    """Garante que `pgp_chat` esta importavel."""
    try:
        import pgp_chat  # noqa: F401
        return
    except ImportError:
        pass
    # Tentativa por variavel de ambiente
    env = os.environ.get("PGP_CHAT_PATH")
    if env and os.path.isdir(env):
        sys.path.insert(0, env)
        return
    # Tentativa por caminho relativo padrao do ambiente do aluno
    here = Path(__file__).resolve()
    candidate = here.parents[3] / "ead1-sgi" / "src"
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))
        return
    raise ImportError(
        "Nao foi possivel localizar o pacote pgp_chat. "
        "Garanta que o projeto ead1-sgi esta em um diretorio irmao "
        "ou defina a variavel PGP_CHAT_PATH apontando para .../ead1-sgi/src"
    )


_bootstrap_pgp_chat()

from pgp_chat.keys import (  # noqa: E402
    export_public_key,
    generate_keypair,
    import_public_key,
)
from pgp_chat.messages import decrypt_and_verify, encrypt_and_sign  # noqa: E402
from pgp_chat.storage import get_gpg  # noqa: E402


class CryptoAdapter:
    """Encapsula um keyring PGP por usuario e operacoes de cifra/decifra.

    O broker, por design, NAO recebe instancias de CryptoAdapter — ele apenas
    repassa o payload em ASCII-armored. Apenas remetente e destinatario
    cifram/decifram.
    """

    def __init__(self, user: str, base_dir: str | os.PathLike, passphrase: str) -> None:
        self.user = user
        self.base_dir = str(base_dir)
        self.passphrase = passphrase
        self.gpg = get_gpg(user, self.base_dir)
        self.fingerprint: Optional[str] = None

    # --- chaves ---

    def generate_key(self, name: str, email: str, key_length: int = 2048) -> str:
        """Gera par RSA e armazena fingerprint no proprio adapter."""
        self.fingerprint = generate_keypair(
            self.gpg,
            name=name,
            email=email,
            passphrase=self.passphrase,
            key_length=key_length,
        )
        return self.fingerprint

    def export_pubkey(self) -> str:
        if not self.fingerprint:
            raise RuntimeError("Nenhuma chave gerada para este adapter")
        return export_public_key(self.gpg, self.fingerprint)

    def import_pubkey(self, armored: str) -> str:
        result = import_public_key(self.gpg, armored)
        fps = result.get("fingerprints") or []
        if not fps:
            raise RuntimeError("Importacao de chave publica retornou vazia")
        return fps[0]

    # --- cifra / decifra ---

    def encrypt_for(self, recipient_fp: str, plaintext: str) -> str:
        """Cifra+assina plaintext para um destinatario; retorna ASCII-armored (.asc)."""
        if not self.fingerprint:
            raise RuntimeError("Adapter sem chave propria para assinatura")
        return encrypt_and_sign(
            gpg_sender=self.gpg,
            message=plaintext,
            recipient_fp=recipient_fp,
            signer_fp=self.fingerprint,
            passphrase=self.passphrase,
        )

    def decrypt(self, ciphertext: str) -> dict:
        """Decifra e verifica assinatura.

        Retorna dict com 'plaintext', 'valid', 'fingerprint', 'username'.
        """
        return decrypt_and_verify(
            gpg_recipient=self.gpg,
            ciphertext=ciphertext,
            passphrase=self.passphrase,
        )
