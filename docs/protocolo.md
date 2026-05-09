# Protocolo de Aplicacao

Protocolo linha-orientado (cada mensagem termina com `\n`), inspirado em
RTSP. O cliente abre uma conexao TCP, envia comandos texto e recebe
respostas texto. Comandos com payload (apenas SEND) tem o payload em
**uma unica linha** codificada em **base64** (UTF-8 -> bytes -> base64).

## Comandos cliente -> broker

```
REGISTER name=<str>
SUBSCRIBE channel=<str>
UNSUBSCRIBE channel=<str>
SEND target_type=<UNICAST|MULTICAST|BROADCAST> target=<str|*> lamport=<int> encrypted=<true|false>
<payload-base64>
CONSUME [max=<int>]
TEARDOWN
```

## Respostas broker -> cliente

```
200 OK [k1=v1 k2=v2 ...]
4XX <descricao>            ex.: 400 parametros invalidos, 401 nao registrado, 404 destinatario nao registrado, 409 NAME_TAKEN
5XX <descricao>
```

## Entrega de mensagem (resposta a CONSUME)

Apos a linha `200 OK count=<n>`, o broker envia `<n>` blocos:

```
MSG msg_id=<uuid> producer=<str> target_type=<UNICAST|MULTICAST|BROADCAST> lamport_prod=<int> lamport_buf=<int> encrypted=<bool>
<payload-base64>
END
```

## Estados de uma sessao

```
                +-------+
                | INIT  |---REGISTER name=alice (200 OK)----+
                +-------+                                   |
                                                            v
                                                       +---------+
                       SEND, CONSUME, SUBSCRIBE,       | READY   |
                       UNSUBSCRIBE: voltam a READY     +---------+
                                                            |
                                                       TEARDOWN
                                                            |
                                                            v
                                                       +---------+
                                                       | CLOSED  |
                                                       +---------+
```

`REGISTER` deve ser o primeiro comando. Os demais retornam `401` ate que a
sessao tenha um nome associado.

## Exemplo de transcricao (unicast)

```
> REGISTER name=alice
< 200 OK name=alice lamport=1
> SEND target_type=UNICAST target=bob lamport=1 encrypted=false
> b2xhIGJvYg==
< 200 OK msg_id=2c4a... lamport_buf=2
> TEARDOWN
< 200 OK
```

```
> REGISTER name=bob
< 200 OK name=bob lamport=1
> CONSUME
< 200 OK count=1
< MSG msg_id=2c4a... producer=alice target_type=UNICAST lamport_prod=1 lamport_buf=2 encrypted=false
< b2xhIGJvYg==
< END
> TEARDOWN
< 200 OK
```

## Codigos de erro

| Codigo | Quando                                                      |
|--------|-------------------------------------------------------------|
| 400    | Comando malformado, parametro invalido, payload invalido    |
| 401    | Comando antes de REGISTER                                   |
| 404    | UNICAST para destinatario nao registrado                    |
| 409    | NAME_TAKEN (REGISTER com nome ja em uso)                    |
| 500    | Erro interno do broker                                      |

## Justificativa de escolhas

- **Linha-orientado** para depurar com `nc localhost 9000` se preciso.
- **base64** no payload: garante que o payload nao contem `\n` que
  quebraria o framing de linhas.
- **Re-uso do socket TCP**: nao abrimos um socket UDP separado para
  entrega; CONSUME consome a fila do cliente registrada na sessao.
- **Estilo RTSP**: alinhado ao material de aula (Client.py / ServerWorker.py).
