# Aplicação Final - EDI 2026.1

Aplicação em Java (Swing) sobre a base solarradiation.csv, montada com o que
venceu nos benchmarks da etapa de experimentação.

## Compilar e executar

```
compilar.bat        (gera o AplicacaoEDI.jar)
executar.bat        (roda com o padrão de 100.000 registros)
```

ou na mão:

```
javac -encoding UTF-8 *.java
jar cfe AplicacaoEDI.jar AplicacaoFinal *.class
java -jar AplicacaoEDI.jar [limite] [caminho_do_csv]
```

O csv é procurado na pasta atual e depois na pasta acima (raiz do projeto).
A carga padrão é de 100.000 registros e demora ~30s por causa da construção
da AVL (tem barra de progresso).

## Operações

- **Buscar**: pesquisa por ID na AVL, mostrando comparações e tempo.
- **Inserir**: insere um registro novo na AVL (chave repetida é recusada).
- **Remover**: remove por ID e rebalanceia.
- **Exibição ordenada**: ordena os registros por ID com o MergeSort e exibe
  na tabela; também dá pra exibir pelo caminhamento em-ordem da árvore, que
  já sai ordenado.

## Decisões (com base nos benchmarks)

- **Estrutura de dados: árvore AVL** (implementação do professor, NA04, a
  mesma do benchmark). Nos testes de busca a AVL manteve ~1,4·ln(n)
  comparações em qualquer ordem de inserção, enquanto a ABB sem
  balanceamento degenerou com entrada ordenada (estouro de pilha em
  n≈24,7 mil). A busca binária em vetor foi a mais rápida na busca, mas
  inserir/remover em vetor ordenado custa O(n) - como a aplicação precisa
  das três operações, a AVL dá O(log n) em todas.
- **Busca: pesquisa da AVL** - pra n=100.000 são ~16 comparações, contra
  ~50.000 da busca sequencial.
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
  inserção, então a construção da AVL é O(n²) (~30s pra 100 mil registros).
  Esse custo é pago uma vez só, na carga; as operações depois são rápidas.
- O MergeSort usa O(n) de memória auxiliar (workSpace), em troca do
  O(n log n) garantido em qualquer distribuição.
- 100 mil registros é o mesmo teto usado no benchmark da AVL (AVL_MAX_N),
  o limite prático da construção O(n²).

## Arquivos

- `AplicacaoFinal.java` - janela e abas (buscar/inserir/remover/exibição)
- `TArvoreAVL.java` - AVL do NA04 + remoção da ABB do NA03 + caminhamentos
- `Ordenacao.java` - mergesort do benchmark pra Registro[]
- `Registro.java` - registro do csv (chave = ID da primeira coluna)
