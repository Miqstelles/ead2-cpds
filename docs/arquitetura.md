# Arquitetura

## Visao geral

```
   +-------+     TCP     +---------------------+     TCP     +-------+
   |Client |<----------->|       Broker        |<----------->|Client |
   | alice |  controle   |  (Message Bus)      |  controle   |  bob  |
   +-------+   + dados   |                     |   + dados   +-------+
                         |  - clients_registry |
   +-------+     TCP     |  - channels_registry|     TCP     +-------+
   |Client |<----------->|  - MessageBuffer    |<----------->|Client |
   | carol |             |  - LamportClock     |             | dave  |
   +-------+             |  - LogManager       |             +-------+
                         +---------------------+
```

Broker centralizado, **uma instancia por processo**. Cada cliente abre conexao
TCP persistente. O canal serve tanto para comandos (REGISTER, SEND, etc.)
quanto para entrega das mensagens via CONSUME (resposta multi-linha).

## Componentes (mapeamento ao PDF)

| Componente PDF                   | Implementacao                                  |
|----------------------------------|------------------------------------------------|
| Infraestrutura de mensagens      | `Broker` + sockets TCP + `MessageBuffer`       |
| Formato da mensagem              | `Message` (DTO JSON serializavel)              |
| Conjunto de comandos             | `protocol.py` (REGISTER, SEND, CONSUME, ...)   |
| Roteador de mensagem             | `Broker._handle_send` + `MessageBuffer.enqueue`|

## Mapeamento ao Cap. 17 Deitel

| Topico                        | Onde aparece                                 |
|-------------------------------|----------------------------------------------|
| 17.4 Stream sockets / TCP     | `broker.py`, `client.py`                     |
| 17.5 Datagram (UDP)           | discutido aqui (escolha por TCP no MVP)      |
| 17.6 Multicast                | fan-out na aplicacao em `MessageBuffer`      |

**Por que TCP e nao UDP?** No exemplo RTSP/RTP de aula, o controle e TCP
(RTSP) e a entrega e UDP (RTP). Para mensageria, **ordem e confiabilidade**
sao mais importantes do que latencia minima, entao usamos TCP em ambos os
papeis. UDP pode ser introduzido em uma evolucao futura para entrega de
mensagens "fire-and-forget" em cenarios de alta taxa.

**Por que multicast logico (fan-out) e nao IP multicast?** O broker centralizado
ja conhece os subscritores; replicar para cada um via TCP e mais simples e nao
exige configuracao de rede (224.x.x.x). Aderente a figura "one-to-many" do PDF.

## Relogio logico de Lamport (Lamport, 1978)

Tres relogios independentes:

1. **Cliente (produtor)**: incrementa antes de enviar (`send()`); o timestamp
   embarcado na mensagem e `lamport_produced`.
2. **Broker**: ao receber mensagem, aplica `receive(lamport_produced)` =
   `max(local, recebido) + 1` no seu proprio relogio. O resultado vira
   `lamport_buffered` e e gravado no buffer + log.
3. **Cliente (consumidor)**: ao consumir, aplica `receive(lamport_buffered)`
   no seu proprio relogio. O resultado e `lamport_consumed` e e gravado no log
   de consumo.

Garantia: **ordem causal parcial**. Se evento A causa evento B (mesmo agente, ou
A eh send e B eh receive), entao `L(A) < L(B)`.

## Modelo de dados

```python
@dataclass
class Message:
    msg_id: str                 # uuid4
    producer: str               # nome do cliente produtor
    target_type: str            # UNICAST | MULTICAST | BROADCAST
    target: Optional[str]       # nome do consumidor / canal / None p/ broadcast
    payload: str                # texto plano (ou ASCII-armored se encrypted)
    encrypted: bool
    lamport_produced: int       # carimbo logico no produtor
    lamport_buffered: int|None  # carimbo no broker
    lamport_consumed: int|None  # carimbo no consumidor
    consumer: str|None
```

## Fluxo de uma mensagem unicast

```
alice.clock = 0
alice.send_unicast(bob, "oi"):
  ts_p = alice.clock.send()     # alice.clock = 1, ts_p = 1
  envia SEND lamport=1 payload=base64("oi")
                                          broker.clock = 0
                                          recebe SEND ts_p=1
                                          ts_b = broker.clock.receive(1) = max(0,1)+1 = 2
                                          msg.lamport_buffered = 2
                                          buffer.enqueue(msg)  # bob.queue += [msg]
                                          log_production(msg)
                                          responde 200 OK msg_id=... lamport_buf=2

bob.clock = 0
bob.consume():
  envia CONSUME
                                          dequeue bob.queue -> [msg]
                                          ts_c_broker = broker.clock.receive(2) = 3  (registro)
                                          log_consumption(msg, bob, 3)
                                          envia MSG ... lamport_buf=2 ... payload
  recebe MSG ... lamport_buf=2
  ts_c = bob.clock.receive(2) = 3
  msg.lamport_consumed = 3
```

## Threading e seguranca

- `Broker._accept_loop` em thread daemon dedicada.
- Cada conexao em `_handle_session` em thread propria (modelo "thread per connection").
- `MessageBuffer` protegido por `threading.RLock`.
- `LamportClock` protegido por `threading.Lock`.
- `LogManager` serializa escritas com `threading.Lock`.
- Teste `test_thread_safety_increments` valida concorrencia de 8 threads x 1000 ticks.

## Decisoes de projeto

- **Linha-orientado** (vs binario): mais legivel para depuracao e alinhado ao
  estilo RTSP do material de aula.
- **base64** no payload: evita conflitos com newline no protocolo de linha.
- **Conexao persistente**: simplifica sessao (broker sabe quem e quem) e
  permite que CONSUME entregue varias MSGs em sequencia.
- **Broker descobre porta efemera quando port=0**: util em testes.

## Camada de criptografia (Sprint 3)

`mensageria.crypto_adapter.CryptoAdapter` encapsula o pacote `pgp_chat` do
projeto irmao [`ead1-sgi`](../../ead1-sgi/). Reusa diretamente:

- `pgp_chat.keys.generate_keypair`
- `pgp_chat.keys.export_public_key` / `import_public_key`
- `pgp_chat.messages.encrypt_and_sign`
- `pgp_chat.messages.decrypt_and_verify`
- `pgp_chat.storage.get_gpg`

**Localizacao do pgp_chat** (no `crypto_adapter._bootstrap_pgp_chat`):
1. `import pgp_chat` (caso instalado);
2. variavel `PGP_CHAT_PATH`;
3. caminho relativo `../ead1-sgi/src/` (default para o ambiente do aluno).

**Quem cifra/decifra:** apenas remetente e destinatario. O **broker repassa
o payload opaco** em ASCII-armored (`-----BEGIN PGP MESSAGE-----...`).
O `production.log` registra `encrypted=true` e o tamanho do ciphertext, mas
nunca o plaintext. Verificado pelo teste
`test_crypto_e2e::test_broker_nao_decifra_payload`.

## Trabalhos futuros

- UDP para entrega "fire-and-forget" (paralelo ao TCP de controle).
- Replicacao de broker para tolerancia a falhas.
- CLI com `--encrypt` (gestao integrada de keyrings).
- Multicast IP (224.x.x.x) como alternativa ao fan-out via TCP.
