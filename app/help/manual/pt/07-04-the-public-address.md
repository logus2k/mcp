# O endereço público

No domínio a consola está em `https://logus2k.com/mcp-console/admin`, atrás do início de sessão Microsoft Entra ID do
proxy, só para os administradores. A face REST está debaixo do mesmo prefixo e da mesma porta de entrada.

As aplicações e os agentes não usam esse endereço: ligam-se na **rede interna**, em `http://mcp-service:8080`, com as
suas chaves. O endereço MCP é aí `/mcp/<app>/`.

## Ver também
- [Ligar uma aplicação](04-04-connect-an-app.md)
- [Quem pode escrever](07-01-who-may-write.md)
