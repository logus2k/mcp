# Monitorizar os serviços de apoio

As ferramentas dependem de **serviços de apoio**: o navegador isolado de pesquisa na web, o Jenkins (para os sensores
SDLC), a chave da NewsAPI, a configuração montada do proxy. A consola sonda-os.

## Onde olhar

- **Monitorização** no menu superior — o serviço e cada serviço de apoio com um ponto e o seu estado; o modo das
  chaves; quantos itens precisam de atenção; **Atualizar o estado**.
- **A barra de estado** — à direita, *serviços de apoio: n ok*, ou quantos estão em baixo ou degradados. Clique para
  abrir as Definições.
- **Definições** › **Serviços de apoio** — o mesmo, com as implementações que dependem de cada um.

## Notas

- O estado é atualizado a cada 30 segundos, e em **Atualizar o estado**.
- Um serviço de apoio em baixo não derruba o serviço: as chamadas às ferramentas que precisam dele falham com o seu
  erro, e o registo mostra-o.

## Ver também
- [Definições](06-03-settings.md)
- [Ler a barra de estado](01-03-the-status-bar.md)
