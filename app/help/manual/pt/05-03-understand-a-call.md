# Entender o registo de uma chamada

| Coluna | Significado |
|---|---|
| Hora | quando a chamada começou |
| Aplicação | a aplicação para a qual foi feita (`?app=` ou a aplicação do endereço) |
| Ferramenta | a ferramenta |
| Chamador | o id da chave; `console` para o token de administração; o seu endereço quando a executou com sessão iniciada; `anonymous` quando nada foi apresentado |
| Em nome de | a pessoa por quem o chamador age (`X-On-Behalf-Of`), ou a pessoa com sessão iniciada |
| Via | `rest` ou `mcp` |
| Duração | quanto tempo a ferramenta demorou |
| Estado | ok, ou o erro que o chamador recebeu |

## Os erros que vai ver

- *invalid_arguments at /x* — os argumentos não correspondiam ao esquema; a propriedade é indicada.
- *401: a write-tier tool needs an app key* — um chamador anónimo tentou uma ferramenta de escrita.
- *401: an app key is required* — as chaves são obrigatórias e nenhuma foi apresentada.
- *403: this key belongs to app 'a', not 'b'* — uma chave usada no endereço de outra aplicação.
- *409: tool disabled* / *client-executed tool* — a ferramenta está desligada, ou o serviço não a executa.
- *502 …* — a implementação falhou; a mensagem é a dela.

## Notas

- Os argumentos são registados como um **resumo** (uma impressão digital), não como texto, a não ser que o registo
  esteja definido para os guardar, e nunca para ferramentas de escrita.

## Ver também
- [Ler a atividade](05-01-read-the-activity.md)
- [O registo e a sua retenção](07-03-record-and-retention.md)
