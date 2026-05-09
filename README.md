# Mensageria — Sistema Distribuido com Lamport Clocks

Solucao de mensageria distribuida (Message Bus) implementada em Python 3 sobre
sockets TCP, com:

- Relogio logico de Lamport carimbando cada mensagem em **3 pontos** (produtor,
  broker, consumidor).
- **Message buffer** que armazena mensagens identificando o produtor; ao consumir
  registra o consumidor com novo carimbo logico.
- **Log simples** (arquivos texto, nao DB) de producao e consumo para conferencia.
- Suporte a **unicast**, **multicast** (canais) e **broadcast**.
- **Nomeacao** de clientes e canais.
- Integracao opcional com **PGP** (reuso do projeto `ead1-sgi/src/pgp_chat`) na
  Sprint 3.

> **Status:** Sprints 1, 2 e 3 entregues. Versao **v1.0.0**.

## Por que existe

Atende ao trabalho de mensageria do curso, considerando:
- Cap. 17 do Deitel (secoes 17.4 stream sockets, 17.5 datagram, 17.6 multicast).
- O texto "Designing a Large Network-Connected Distributed System" (PDF anexo)
  com componentes do Message Bus: infraestrutura, formato, conjunto de comandos,
  roteador.

## Pre-requisitos

- Python 3.9+
- `gpg` (GnuPG) no PATH — apenas para os testes E2E com PGP
  (`brew install gnupg` no macOS, `apt install gnupg` no Debian/Ubuntu).
- `pip install -r requirements.txt`
- O pacote `pgp_chat` do projeto irmao [`ead1-sgi`](../ead1-sgi/) e
  localizado automaticamente pelo `crypto_adapter` (esperado em
  `../ead1-sgi/src/pgp_chat/`). Como alternativa, defina
  `PGP_CHAT_PATH` apontando para o diretorio `src` que contem o pacote.

## Como rodar

O pacote usa **layout src/** (boa pratica), entao Python precisa saber onde
encontrar o modulo `mensageria`. Use uma das duas formas:

**Opcao A — exportar PYTHONPATH (sem instalar nada):**
```bash
export PYTHONPATH=src
python3 -m mensageria.cli broker --host 127.0.0.1 --port 9000
```

Ou inline em cada chamada:
```bash
PYTHONPATH=src python3 -m mensageria.cli broker --host 127.0.0.1 --port 9000
```

**Opcao B — instalar o pacote em modo editavel:**
```bash
pip install -e .
mensageria broker --host 127.0.0.1 --port 9000
```

(Opcao B usa o entry point `mensageria` definido em `pyproject.toml`.)

### Subir clientes (em terminais separados)

```bash
PYTHONPATH=src python3 -m mensageria.cli client --name alice --host 127.0.0.1 --port 9000 --repl
PYTHONPATH=src python3 -m mensageria.cli client --name bob   --host 127.0.0.1 --port 9000 --repl
```

No REPL do cliente:

```
alice> send bob ola bob
alice> bcast geral

bob> consume
  [1->2->3] alice UNICAST: ola bob
```

### Ou modo nao-interativo

```bash
PYTHONPATH=src python3 -m mensageria.cli client --name alice --send-unicast bob "ola bob"
PYTHONPATH=src python3 -m mensageria.cli client --name bob --consume
```

### Envio cifrado (PGP fim-a-fim)

A CLI nao expoe `--encrypt` na v1.0.0; o uso programatico via biblioteca
e o seguinte (vide `tests/integration/test_crypto_e2e.py` para o padrao
completo):

```python
from mensageria.client import Client
from mensageria.crypto_adapter import CryptoAdapter

# Setup uma unica vez por usuario
alice = CryptoAdapter("alice", "/tmp/keyrings", "alice-pass")
alice_fp = alice.generate_key("Alice", "alice@example.com")
bob = CryptoAdapter("bob", "/tmp/keyrings", "bob-pass")
bob_fp = bob.generate_key("Bob", "bob@example.com")

# Trocar chaves publicas
alice.import_pubkey(bob.export_pubkey())
bob.import_pubkey(alice.export_pubkey())

# Alice cifra e envia
ciphertext = alice.encrypt_for(bob_fp, "saldo R$ 12.345,67")
with Client("alice") as a:
    a.register()
    a.send_unicast("bob", ciphertext, encrypted=True)

# Bob recebe e decifra
with Client("bob") as b:
    b.register()
    msg = b.consume()[0]
    result = bob.decrypt(msg.payload)
    print(result["plaintext"])  # "saldo R$ 12.345,67"
    print(result["valid"])       # True (assinatura conferida)
```

O **broker nao decifra**: o payload e roteado opaco em ASCII-armored, e
o `production.log` registra apenas `encrypted=true` e o tamanho do
ciphertext — nao o plaintext.

## Conferindo logs

```bash
cat logs/production.log
cat logs/consumption.log
```

Formato CSV (header + linhas):

```
iso_ts,lamport_prod,lamport_buf,msg_id,producer,target_type,target,encrypted,payload_bytes
2026-05-09T14:30:01,5,7,abc-123,alice,UNICAST,bob,false,2048
```

## Rodando os testes

```bash
python3 -m pytest -v
```

Saida esperada: `65 passed` (Sprints 1+2+3).

## Estrutura

```
src/mensageria/
  lamport.py        # LamportClock thread-safe
  message.py        # Message DTO + JSON
  protocol.py       # parser/formatter linha-orientado (estilo RTSP)
  buffer.py         # MessageBuffer (filas por cliente/canal)
  log_manager.py    # production.log + consumption.log
  crypto_adapter.py # wrapper PGP (reuso de pgp_chat de ead1-sgi)
  broker.py         # servidor TCP + registry + roteamento
  client.py         # API cliente
  cli.py            # CLI broker/cliente
tests/
  unit/             # 37 testes
  integration/      # 28 testes (registro, unicast, multicast, broadcast, canais, PGP E2E)
docs/
  arquitetura.md
  protocolo.md
  product-backlog.md
  sprint-1.md
  sprint-2.md
  sprint-3.md
  protocolo-de-testes.md
```

## Documentacao adicional

- [Arquitetura](docs/arquitetura.md)
- [Protocolo](docs/protocolo.md)
- [Product Backlog](docs/product-backlog.md)
- [Sprint 1](docs/sprint-1.md)
- [Sprint 2](docs/sprint-2.md)
- [Sprint 3](docs/sprint-3.md)
- [Protocolo de Testes](docs/protocolo-de-testes.md)
