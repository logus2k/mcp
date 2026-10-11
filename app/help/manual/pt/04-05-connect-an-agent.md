# Ligar um agente ou o Claude

Um agente liga-se por **MCP**: o endereço padrão `/mcp/<app>/` (Streamable HTTP). Descobre as ferramentas da aplicação
com as suas anotações, chama-as e recebe as competências da aplicação como prompts e recursos. O Claude Code e o Claude
Desktop são clientes MCP.

## Passos

1. Emita uma chave para a aplicação.
2. Abra **Aplicações** › **Ligar** (ou o separador **Ligar** de uma ferramenta) e copie o comando do **Claude Code** ou
   a configuração do **Claude Desktop**. Cole primeiro a chave no campo de token da consola e os excertos levam-na.
3. Execute o comando (Claude Code) ou acrescente a configuração (Claude Desktop). As ferramentas da aplicação aparecem
   no cliente; as suas competências aparecem como prompts.
4. Abra **Atividade**: as chamadas do agente aparecem com o id da chave.

## Notas

- Uma chave por agente, com o seu nome, para que possa ser revogada sozinha.
- Um agente que age por uma pessoa deve enviar `X-On-Behalf-Of`; um que não age por ninguém fica registado sem pessoa.

## Ver também
- [Emitir uma chave para uma aplicação](04-02-issue-a-key.md)
- [O que é uma competência e o que pertence aqui](03-01-what-a-skill-is.md)
