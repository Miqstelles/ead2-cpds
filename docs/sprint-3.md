# Sprint 3 — PGP / Documentacao / Testes E2E

**Periodo:** 1 semana (planejada)
**Sprint Goal:** Habilitar confidencialidade fim-a-fim via PGP (reutilizando o
pacote `pgp_chat` do projeto SGI), entregar documentacao final e fechar a
suite de testes com cenarios E2E cifrados.

## Sprint Backlog

| ID   | User Story                                                           | Estimativa |
|------|----------------------------------------------------------------------|------------|
| US10 | Cifrar payload com PGP do destinatario                               | M          |
| US11 | Testes unitarios, integracao e E2E executados                        | S          |
| US12 | Documentacao completa (README, arquitetura, protocolo, testes)       | S          |

## Descobertas tecnicas

- `pip 21.2.4` (sistema do aluno) nao suporta editable install de pacote
  pyproject.toml-only (PEP 660). Solucao: o `crypto_adapter.py` faz
  bootstrap por **caminho relativo** (`../ead1-sgi/src/`) ou variavel de
  ambiente `PGP_CHAT_PATH`. O usuario nao precisa de `pip install -e ..`.
- O `gpg-agent` em macOS limita o caminho do socket Unix a ~104 chars; por
  isso a fixture de keyrings usa `tempfile.mkdtemp(prefix="msgkr-", dir="/tmp")`
  em vez de `tmp_path` do pytest (mesmo padrao usado no pgp_chat de origem).
- Geracao de par de chaves RSA-2048 leva ~1s; com fixture `scope="module"`
  o conjunto de testes E2E roda em ~5s.

## Daily (resumo)

- D1: planning + verificacao de gpg disponivel + leitura do pgp_chat
- D2: implementacao de `CryptoAdapter` com bootstrap de pgp_chat
- D3: testes E2E (4 casos) — happy path, opacidade no broker, ordem FIFO
  com cifragem, falha sem chave privada
- D4: atualizacao de README, protocolo-de-testes, backlog
- D5: docs/sprint-3.md + tag v1.0.0
- D6: review + retro

## Sprint Review

- **Demos:**
  - `tests/integration/test_crypto_e2e.py::test_e2e_alice_cifra_bob_decifra`:
    alice cifra+assina, envia via mensageria, broker so ve ASCII-armored,
    bob decifra e verifica assinatura.
  - `tests/integration/test_crypto_e2e.py::test_broker_nao_decifra_payload`:
    em `production.log`, o plaintext nao aparece — apenas o ciphertext (e
    `encrypted=true`).
  - Suite total: **65 testes verdes** em 18,65s.
- **Aceito pelo PO:** sim.

## Sprint Retro

**O que foi bem:**
- Reuso direto do `pgp_chat` (uma classe wrapper, ~100 linhas) entregou
  sigilo + autenticacao em um sprint.
- Bootstrap por caminho relativo tornou o projeto portatil — basta clonar
  ambos os repos como diretorios irmaos.
- `scope="module"` na geracao de chaves manteve a suite rapida.

**O que pode melhorar:**
- CLI nao expoe `--encrypt` ainda. Adicionar exigiria gestao de keyrings
  em CLI (passphrase, fingerprint resolvers) — escopo deliberadamente fora
  da Sprint 3 por baixo retorno academico.
- Cobertura de assinatura adulterada nao foi feita (gnupg pode nao retornar
  `valid=False` previsivelmente sem testes longos). Anotado como melhoria
  futura.

## Acao final
- Tag `v1.0.0` na entrega.
- Compartilhar link do GitHub no Moodle: https://github.com/Miqstelles/ead2-cpds
- Resumo de leituras (entrega individual EaD): documento separado fora do
  repositorio (entregar diretamente no AVA).

## Metricas finais

- Linhas de codigo (src): ~800 linhas Python.
- Modulos: 9 (lamport, message, protocol, buffer, log_manager, crypto_adapter, broker, client, cli).
- Testes: **65 verdes** (37 unitarios + 28 integracao).
- Tempo de execucao: 18,65s.
- Reuso de codigo externo: pgp_chat (encrypt_and_sign, decrypt_and_verify, generate_keypair, get_gpg).
