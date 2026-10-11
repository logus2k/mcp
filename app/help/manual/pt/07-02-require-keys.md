# Exigir chave a todos os chamadores

Por omissão as chaves são **opcionais** para as ferramentas de leitura, para que os consumidores existentes continuem
a funcionar enquanto recebem chaves; as ferramentas de escrita precisam sempre de uma. Quando todos os consumidores
tiverem chave, exija-as.

## Passos

1. Abra **Aplicações**: todas as aplicações que chamam o serviço devem mostrar *chave ativa*. A Visão geral lista as
   que não têm.
2. Abra **Atividade** sem *Só erros* e procure chamadores *anonymous* nos últimos dias; dê-lhes chaves.
3. Defina `MCP_REQUIRE_KEYS=1` no ambiente do serviço e reinicie-o.
4. A barra de estado passa a dizer *chaves obrigatórias*; uma chamada anónima é agora recusada com *an app key is
   required*.

## Ver também
- [Emitir uma chave para uma aplicação](04-02-issue-a-key.md)
- [O que precisa de atenção](06-01-needs-attention.md)
