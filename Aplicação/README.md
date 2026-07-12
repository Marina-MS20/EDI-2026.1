# Aplicação Final - EDI 2026.1

Aplicação em Java (Swing) sobre a base solarradiation.csv, montada com o que
venceu nos benchmarks da etapa de experimentação.

## Compilar e executar

```
compilar.bat        (gera o AplicacaoEDI.jar)
executar.bat        (roda com a base inteira, ~7 milhões de registros)
```

ou na mão:

```
javac -encoding UTF-8 *.java
jar cfe AplicacaoEDI.jar AplicacaoFinal *.class
java -Xmx4g -jar AplicacaoEDI.jar [limite] [caminho_do_csv]
```

O csv é procurado na pasta atual e depois na pasta acima (raiz do projeto).
Por padrão a carga lê o arquivo inteiro (~7,1 milhões de registros, uns 10s,
~1,5GB de memória - por isso o -Xmx4g). Dá pra limitar passando um número
como primeiro argumento (ex.: 100000 pra uma demo rápida).

## Operações

- **Buscar**: pesquisa por ID na AVL, mostrando comparações e tempo.
- **Inserir**: insere um registro novo na AVL (chave repetida é recusada).
- **Remover**: remove por ID e rebalanceia.
- **Exibição ordenada**: ordena os registros por ID com o MergeSort e exibe
  na tabela; também dá pra exibir pelo caminhamento em-ordem da árvore, que
  já sai ordenado.
- **Análises**: consultas sobre os dados usando a AVL - maior emissão de uma
  data, data de maior emissão de um comprimento de onda, primeira/última
  data do banco (descida pelas bordas da árvore, já que os IDs do csv
  crescem em ordem cronológica), menor/maior comprimento de onda, média de
  emissão num intervalo de comprimento de onda, pesquisa por data e/ou por
  qualquer campo do registro (listando os que baterem) e gráfico do espectro da data
  (comprimento de onda em nm × irradiância em W/m²/nm, desenhado em Swing).
  Cada consulta gera um registro de execução com a operação, os parâmetros,
  o resultado, as comparações, o tempo, o nível onde o resultado estava e a
  altura atual da AVL.

## Decisões (com base nos benchmarks)

- **Estrutura de dados: árvore AVL** (implementação do professor, NA04, a
  mesma do benchmark). Nos testes de busca a AVL manteve ~1,4·ln(n)
  comparações em qualquer ordem de inserção, enquanto a ABB sem
  balanceamento degenerou com entrada ordenada (estouro de pilha em
  n≈24,7 mil). A busca binária em vetor foi a mais rápida na busca, mas
  inserir/remover em vetor ordenado custa O(n) - como a aplicação precisa
  das três operações, a AVL dá O(log n) em todas.
- **Busca: pesquisa da AVL** - pra n=7,1 milhões são ~23 comparações, contra
  ~3,5 milhões da busca sequencial.
- **Remoção: Remove/getMax da ABB (NA03)** - substituição pelo maior da
  subárvore esquerda, o modo usado na disciplina. Como o NA04 não tem
  remoção pra AVL, depois da retirada o rebalanceamento sobe do pai do nó
  removido até a raiz chamando o AVL(p) do professor em quem desbalancear
  (na remoção mais de um ancestral pode desbalancear, diferente da
  inserção, e as alturas dos filhos precisam ser recalculadas antes porque
  o filho pesado fica do lado oposto ao caminho da remoção).
- **Ordenação: MergeSort** (mesmo código do benchmark), pela mesma chave
  que os benchmarks ordenaram (o ID da primeira coluna). Foi o único sempre
  O(n log n) nas 5 distribuições testadas e o de menor coeficiente no caso
  aleatório (8,34·n·ln n contra 9,56 do heapsort). O quicksort com pivô no
  primeiro elemento até foi um pouco mais rápido no caso aleatório, mas
  estoura a pilha com entrada já ordenada (n≈15,3 mil) - e a base
  frequentemente já está ordenada. Insertion/selection/bubble são O(n²).

## Trade-offs

- O balanco() do NA04 recalcula as alturas percorrendo as subárvores a cada
  inserção, então montar a árvore inserindo um a um é O(n²) - foi ~30s pra
  100 mil registros no benchmark, seriam dias pros 7 milhões. Por isso a
  carga usa o CriaABP do exercício 10 (ENADE 2011): como o csv já vem
  ordenado por ID, a árvore completa é montada em tempo linear (0,2s) e já
  nasce balanceada (altura 23 pra 7,1 milhões, o mínimo é ~22,8). Se o csv
  vier fora de ordem, o MergeSort do benchmark ordena antes. As inserções,
  remoções e buscas depois da carga continuam 100% com o código do
  professor.
- O MergeSort usa O(n) de memória auxiliar (workSpace), em troca do
  O(n log n) garantido em qualquer distribuição.
- A tabela da exibição ordenada mostra no máximo 200 mil linhas (o
  MergeSort ordena tudo, só a exibição é limitada - 7 milhões de linhas
  numa JTable estouram a memória sem necessidade).
- Strings repetidas do csv (data, comprimentos de onda, modo, versão,
  qualidade) são guardadas uma vez só, senão a base completa não caberia
  confortavelmente na memória.

## Arquivos

- `AplicacaoFinal.java` - janela e abas (buscar/inserir/remover/exibição/análises)
- `TArvoreAVL.java` - AVL do NA04 + remoção da ABB do NA03 + caminhamentos
- `Ordenacao.java` - mergesort do benchmark pra Registro[]
- `Registro.java` - registro do csv (chave = ID da primeira coluna)
- `Analises.java` - consultas da aba Análises com os registros de execução
- `GraficoEspectro.java` - gráfico do espectro desenhado com Graphics2D
