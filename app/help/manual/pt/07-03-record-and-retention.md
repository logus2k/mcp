# O registo e a sua retenção

Todas as chamadas são registadas com a aplicação, a ferramenta, o chamador, a pessoa, o transporte, o resultado e a
duração. Os argumentos são registados como um **resumo** (uma impressão digital que distingue chamadas idênticas) por
omissão.

- `MCP_RECORD_ARGS=1` guarda os argumentos das ferramentas de **leitura** como texto; os das ferramentas de escrita
  nunca são guardados.
- `MCP_RETENTION_DAYS` (90) é quanto tempo as linhas ficam guardadas; as mais antigas são apagadas diariamente.

As Definições mostram os valores atuais; o item *registo* da barra de estado resume-os.

## Ver também
- [Entender o registo de uma chamada](05-03-understand-a-call.md)
- [Filtrar e exportar a atividade](05-02-filter-and-export.md)
