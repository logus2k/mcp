# O que precisa de atenção

A lista **Precisa de atenção** da Visão geral é calculada a partir do catálogo, das chaves e do registo. Cada item diz
o quê, porquê e para onde ir.

| Item | Porque aparece | O que fazer |
|---|---|---|
| ferramentas do servidor nunca chamadas | ativas, executadas aqui, sem chamadas registadas | ligue um consumidor, ou desative-as |
| as chaves são opcionais | as ferramentas de leitura respondem a chamadas anónimas | dê uma chave a cada consumidor, depois exija chaves |
| chamadas anónimas nas últimas 24 h | um chamador sem chave | encontre-o na Atividade e dê-lhe uma chave |
| uma ferramenta ligada a uma implementação em falta | o registo nomeia uma implementação que esta versão não inclui | edite a ferramenta, ou instale a implementação |
| uma competência espera ferramentas que as suas aplicações não recebem | a competência nomeia ferramentas; podem ser da própria aplicação | ofereça a ferramenta aqui, ou deixe estar |
| aplicações sem chave | as suas chamadas são anónimas e deixarão de funcionar quando as chaves forem obrigatórias | emita chaves |
| registos renomeados pela migração | duas aplicações tinham o mesmo nome com conteúdo diferente | decida qual manter |

![A Visão geral: os mosaicos e a lista Precisa de atenção](../img/06-01-needs-attention-1.png)

## Ver também
- [Exigir chave a todos os chamadores](07-02-require-keys.md)
- [Monitorizar os serviços de apoio](06-02-monitor-the-backends.md)
