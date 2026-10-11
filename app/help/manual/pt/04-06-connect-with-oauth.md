# Ligar um cliente MCP com OAuth

O Claude Code, os conectores personalizados do claude.ai e outros clientes MCP podem iniciar a sessão de uma **pessoa**
em vez de guardar uma chave: o cliente descobre o servidor OAuth do serviço, a Microsoft inicia a sessão da pessoa
através do domínio, uma página de consentimento pergunta o que o cliente pode fazer, e a pessoa autoriza. Todas as
chamadas ficam então registadas com o seu endereço.

## Passos

1. Dê ao cliente o endereço público da aplicação: `https://logus2k.com/mcp-console/mcp/<app>/` (o excerto
   **OAuth 2.1** no separador **Ligar** de qualquer ferramenta, ou o botão **Ligar** de uma aplicação).
2. O cliente abre o início de sessão. Inicie sessão com a sua conta Microsoft.
3. A página de consentimento nomeia o cliente e lista o que pede: ferramentas de leitura, ferramentas de escrita,
   administração. Clique em **Allow** (ou **Deny**).
4. O cliente fica ligado. Abra **Atividade**: as suas chamadas aparecem como `oauth:<o seu endereço>`.

## Notas

- As ferramentas de escrita e a administração por OAuth são para as pessoas da lista de administradores; um cliente
  pode pedi-las, a lista decide.
- **Definições › Clientes OAuth** lista os clientes que se registaram; **Remover** termina o acesso de um.
- Dentro da rede, os programas continuam a usar chaves: o OAuth é para os clientes das pessoas no domínio.

## Ver também
- [Ligar um agente ou o Claude](04-05-connect-an-agent.md)
- [Emitir uma chave para uma aplicação](04-02-issue-a-key.md)
