# Dar um cliente máquina a um programa

Um **cliente máquina** é a forma OAuth de identificar um programa que fala por uma aplicação (um serviço em segundo
plano, um backend, uma tarefa agendada): em vez de uma chave, tem um id e um segredo e troca-os por um token que
expira ao fim de uma hora e traz âmbitos explícitos (a concessão *client credentials*). Ninguém inicia sessão: o
token age como a aplicação.

## Passos

1. Abra **Aplicações** e encontre o cartão da aplicação.
2. Em **Clientes máquina**, dê ao cliente o nome do programa que o vai ter, marque **tools:write** se tiver de usar
   ferramentas de escrita, e clique em **+ Novo cliente máquina**.
3. O id e o segredo aparecem uma vez: copie ambos para os segredos do programa.
4. No programa: `POST /oauth/token` com `grant_type=client_credentials`, o id e o segredo; envie o token devolvido como
   `Authorization: Bearer …` no endereço da aplicação; peça de novo quando expirar.
5. Abra **Atividade**: as chamadas do programa aparecem como `client:<id>` para a aplicação, sem pessoa.

## Notas

- Um cliente máquina funciona só no endereço da sua aplicação; os clientes de uma aplicação retirada não obtêm token.
- **Remover** no cartão termina de imediato os tokens do cliente. **Definições › Clientes OAuth** lista todos os
  clientes, de pessoas e de máquinas.
- Uma chave faz o mesmo trabalho sem expirar; mantenha chaves para programas que não conseguem fazer uma troca OAuth.

## Ver também
- [Emitir uma chave para uma aplicação](04-02-issue-a-key.md)
- [Ligar um cliente MCP com OAuth](04-06-connect-with-oauth.md)
