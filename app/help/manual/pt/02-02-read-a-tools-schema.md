# Ler o esquema de uma ferramenta

O **esquema de entrada** de uma ferramenta diz que argumentos recebe: os nomes, os tipos, quais são obrigatórios, os
valores por omissão. Todas as chamadas são verificadas contra ele antes de a ferramenta correr. Uma ferramenta pode
também declarar um **esquema de saída**: o resultado é então devolvido também como conteúdo estruturado.

## Passos

1. Abra a ferramenta (selecione a sua linha em **Ferramentas**) e clique no separador **Esquema**.
2. A tabela lista cada propriedade com o tipo, se é obrigatória, o valor por omissão e a descrição.
3. **JSON em bruto** mostra o esquema tal como está guardado; o mesmo botão volta à tabela.
4. Por baixo da tabela: se está declarado um esquema de saída, e o próprio esquema quando existe.

## Notas

- O separador **Visão geral** mostra as **anotações** da ferramenta, o que um cliente MCP recebe: *readOnlyHint* (uma
  ferramenta de leitura), *destructiveHint* (uma ferramenta de escrita marcada como destrutiva), *idempotentHint*.
- Uma chamada que não corresponda ao esquema é recusada com a propriedade que falhou; fica registada como erro.

## Ver também
- [Editar uma ferramenta](02-05-edit-a-tool.md)
- [Entender o registo de uma chamada](05-03-understand-a-call.md)
