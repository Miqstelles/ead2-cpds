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

> **Status:** Sprint 1 entregue (núcleo + unicast). Sprints 2 e 3 a seguir.

## Por que existe

Atende ao trabalho de mensageria do curso, considerando:
- Cap. 17 do Deitel (secoes 17.4 stream sockets, 17.5 datagram, 17.6 multicast).
- O texto "Designing a Large Network-Connected Distributed System" (PDF anexo)
  com componentes do Message Bus: infraestrutura, formato, conjunto de comandos,
  roteador.

## Pre-requisitos

- Python 3.9+
- `pip install -r requirements.txt`

## Como rodar

### Subir o broker

```bash
python3 -m mensageria.cli broker --host 127.0.0.1 --port 9000
```

### Subir clientes (em terminais separados)

```bash
python3 -m mensageria.cli client --name alice --host 127.0.0.1 --port 9000 --repl
python3 -m mensageria.cli client --name bob --host 127.0.0.1 --port 9000 --repl
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
python3 -m mensageria.cli client --name alice --send-unicast bob "ola bob"
python3 -m mensageria.cli client --name bob --consume
```

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

Saida esperada: `45 passed` (Sprint 1).

## Estrutura

```
src/mensageria/
  lamport.py        # LamportClock thread-safe
  message.py        # Message DTO + JSON
  protocol.py       # parser/formatter linha-orientado (estilo RTSP)
  buffer.py         # MessageBuffer (filas por cliente/canal)
  log_manager.py    # production.log + consumption.log
  broker.py         # servidor TCP + registry + roteamento
  client.py         # API cliente
  cli.py            # CLI broker/cliente
tests/
  unit/             # 35 testes
  integration/      # 10 testes
docs/
  arquitetura.md
  protocolo.md
  product-backlog.md
  sprint-1.md
  protocolo-de-testes.md
```

## Documentacao adicional

- [Arquitetura](docs/arquitetura.md)
- [Protocolo](docs/protocolo.md)
- [Product Backlog](docs/product-backlog.md)
- [Sprint 1](docs/sprint-1.md)
- [Protocolo de Testes](docs/protocolo-de-testes.md)
