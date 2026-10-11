# Quem pode escrever

As leituras estão abertas na rede interna. As escritas (criar, editar, ativar, eliminar, chaves, reposições) e
**Experimentar** precisam de uma destas:

- **um administrador com sessão iniciada** no domínio: o proxy (Microsoft Entra ID) admite-o e identifica-o; o
  serviço só confia no nome juntamente com o segredo do proxy; o seu endereço está na lista de administradores
  (`MCP_ADMIN_EMAILS`, ou qualquer pessoa que o proxy admita quando a lista está vazia). Registado com o seu endereço.
- **o token de administração** (`MCP_ADMIN_TOKEN`), colado no campo do canto superior direito, ou enviado por um
  programa. Registado como `console`.

Uma pessoa com sessão iniciada que não seja administradora lê tudo e pode usar ferramentas de leitura.

## Ver também
- [Iniciar e terminar sessão, e mudar entre o tema escuro e o claro](01-02-sign-in-and-theme.md)
- [O endereço público](07-04-the-public-address.md)
