# Ligar uma aplicação

Uma aplicação chama ferramentas por **REST** (`POST /tools/<nome>/invoke?app=<app>`) com a sua chave, e indica a
pessoa em nome de quem age em `X-On-Behalf-Of`. O separador **Ligar** de qualquer ferramenta, e o botão **Ligar** de
qualquer aplicação, dão os excertos com os endereços certos.

## Passos

1. Emita uma chave para a aplicação.
2. Abra a ferramenta que a aplicação vai chamar, clique em **Ligar** e copie o excerto **curl** ou **Python**.
3. No programa, envie a chave como `Authorization: Bearer mcpk_…` e o endereço da pessoa em `X-On-Behalf-Of`.
4. Faça uma chamada e abra **Atividade**: aparece com o id da chave como chamador e o endereço em *em nome de*.

## Notas

- A lista REST do que a aplicação recebe: `GET /tools?app=<app>`; as especificações para o modelo:
  `GET /tools/manifest?app=<app>`.
- Dentro da rede o endereço é o do próprio serviço (`http://mcp-service:8080`); no domínio, debaixo do caminho só para
  administradores.
- A referência completa é o **Guia de integração** (menu Ajuda; em inglês).

## Ver também
- [Ligar um agente ou o Claude](04-05-connect-an-agent.md)
- [Entender o registo de uma chamada](05-03-understand-a-call.md)
