import java.util.List;

// TArvoreAVL segue a implementação por apontadores do prof. Alcides (NA04),
// a mesma usada no benchmark (MainBusca.java): nodos com esq/dir/pai, insere
// recursivo com parâmetro pai, pesquisa recursiva e rebalanceamento AVL(p)
// subindo pelos pais com balanco/balpreOrdem e rotacao_esquerda/direita.
// Diferença: o nodo guarda o Registro inteiro além da chave.
//
// O NA04 não tem remoção, então usamos o Remove/getMax da ABB do NA03
// (slides 75-77, substituição pelo maior da subárvore esquerda) e depois
// rebalanceamos com o próprio AVL(p) do NA04.
public class TArvoreAVL {

    public static class TNodo {
        TNodo esq;
        long chave;
        Registro item;
        TNodo dir;
        TNodo pai;
        int bal = 0;
        int hesq = 0;
        int hdir = 0;

        TNodo(long chave, Registro item, TNodo pai) {
            this.chave = chave;
            this.item = item;
            this.esq = null;
            this.dir = null;
            this.pai = pai;
        }
    }

    public TNodo T;
    private int h;
    private TNodo p;
    public long comparisons = 0;

    // pai do nó que saiu fisicamente na última remoção
    private TNodo paiRemovido;

    // ===================== INSERÇÃO (NA04) =====================

    public void insere(long chave, Registro item) {
        T = insere(T, chave, item, null);
        AVL(p);
    }

    public TNodo insere(TNodo T, long chave, Registro item, TNodo pai) {
        if (T == null) {
            T = new TNodo(chave, item, pai);
            this.p = T;
        } else {
            pai = T;
            comparisons++;
            if (chave < T.chave)
                T.esq = insere(T.esq, chave, item, pai);
            else if (chave > T.chave)
                T.dir = insere(T.dir, chave, item, pai);
        }
        return T;
    }

    public void AVL(TNodo T) {
        if (T != null) {
            T.bal = balanco(T);
            if (T.bal < 2) {
                AVL(T.pai);
            } else {

                if (T.hesq >= T.hdir)
                    if (T.esq.hesq >= T.esq.hdir) {
                        rotacao_direita(T);
                    }
                    else {
                        rotacao_esquerda(T.esq);
                        rotacao_direita(T);
                    }

                if (T.hdir >= T.hesq)
                    if (T.dir.hdir >= T.dir.hesq) {
                        rotacao_esquerda(T);
                    }
                    else {
                        rotacao_direita(T.dir);
                        rotacao_esquerda(T);
                    }
            }
        }
    }

    public int balanco(TNodo T) {
        h = 0; balpreOrdem(T.esq, 0); T.hesq = h;
        h = 0; balpreOrdem(T.dir, 0); T.hdir = h;
        return Math.abs(T.hesq - T.hdir);
    }

    public void balpreOrdem(TNodo T, int v) {
        if (T != null) {
            v++;
            balpreOrdem(T.esq, v);
            balpreOrdem(T.dir, v);
        } else
            if (v > h) h = v;
    }

    public void rotacao_esquerda(TNodo T) {
        TNodo apu = T.dir;
        T.dir = apu.esq;
        if (apu.esq != null) apu.esq.pai = T;
        apu.pai = T.pai;
        apu.esq = T; T.pai = apu;
        T.bal = 0;
        if (apu.pai == null)
            this.T = apu;
        else {
            if (apu.chave < apu.pai.chave)
                apu.pai.esq = apu;
            else
                apu.pai.dir = apu;
        }
    }

    public void rotacao_direita(TNodo T) {
        TNodo apu = T.esq;
        T.esq = apu.dir;
        if (apu.dir != null) apu.dir.pai = T;
        apu.pai = T.pai;
        apu.dir = T; T.pai = apu;
        T.bal = 0;
        if (apu.pai == null)
            this.T = apu;
        else {
            if (apu.chave < apu.pai.chave)
                apu.pai.esq = apu;
            else
                apu.pai.dir = apu;
        }
    }

    // monta a árvore inteira a partir de um vetor já ordenado por chave,
    // em tempo linear, como o CriaABP do exercício 10 (ENADE 2011, questão 4):
    // o elemento do meio vira a raiz e as metades viram as subárvores.
    // a árvore sai completa, então já nasce balanceada. construir os 7 milhões
    // com o insere um a um seria O(n²) - inviável.
    public void constroiDeVetorOrdenado(Registro[] v) {
        T = criaABP(v, 0, v.length - 1, null);
    }

    private TNodo criaABP(Registro[] v, int i, int j, TNodo pai) {
        if (i > j) return null;
        int pos = (i + j) / 2;
        TNodo t = new TNodo(v[pos].id, v[pos], pai);
        t.esq = criaABP(v, i, pos - 1, t);
        t.dir = criaABP(v, pos + 1, j, t);
        return t;
    }

    // ===================== PESQUISA (NA04) =====================

    public TNodo pesquisa(long chave) {
        return pesquisa(T, chave);
    }

    public TNodo pesquisa(TNodo T, long chave) {
        if (T == null) {
            return T;
        } else {
            comparisons++;
            if (chave == T.chave)
                return T;
            else
                if (chave < T.chave)
                    T = pesquisa(T.esq, chave);
                else
                    T = pesquisa(T.dir, chave);
        }
        return T;
    }

    // ===================== REMOÇÃO (NA03 + AVL do NA04) =====================

    public boolean remove(long chave) {
        if (pesquisa(chave) == null) return false;
        paiRemovido = null;
        Remove(T, chave);

        // o AVL(p) escolhe a rotação lendo hesq/hdir dos FILHOS do nó
        // desbalanceado. na inserção isso funciona porque o caminho de subida
        // passa pelo filho pesado e as alturas estão frescas; na remoção o
        // filho pesado fica do lado oposto ao caminho (alturas velhas) e mais
        // de um ancestral pode desbalancear. então sobe do pai do removido
        // até a raiz recalculando o balanco dos filhos e chamando o AVL do
        // professor em quem estiver desbalanceado.
        TNodo q = paiRemovido;
        while (q != null) {
            if (q.esq != null) balanco(q.esq);
            if (q.dir != null) balanco(q.dir);
            TNodo pai = q.pai; // a rotação mexe nos ponteiros, guarda antes
            if (balanco(q) >= 2) AVL(q);
            q = pai;
        }
        return true;
    }

    public TNodo Remove(TNodo T, long chave) {
        if (T == null) return T;
        if (chave == T.chave)
        {
            TNodo P = T;
            if ((T.esq == null) && (T.dir == null)) {
                if (T.pai == null)
                {
                    this.T = null;
                    paiRemovido = null;
                    return T;
                } else {
                    if (T.chave > T.pai.chave)
                        T.pai.dir = null;
                    else
                        T.pai.esq = null;
                    paiRemovido = T.pai;
                }
            }
            else
                if (T.esq == null) {
                    if (T.pai != null) {
                        if (T.dir != null) T.dir.pai = T.pai;
                        if (T.chave > T.pai.chave)
                            T.pai.dir = T.dir;
                        else
                            T.pai.esq = T.dir;
                        paiRemovido = T.pai;
                    } else {
                        this.T = T.dir;
                        this.T.pai = null;
                        paiRemovido = this.T;
                    }
                }
                else
                    if (T.dir == null) {
                        if (T.pai != null) {
                            if (T.esq != null) T.esq.pai = T.pai;
                            if (T.chave > T.pai.chave)
                                T.pai.dir = T.esq;
                            else
                                T.pai.esq = T.esq;
                            paiRemovido = T.pai;
                        } else {
                            this.T = T.esq;
                            this.T.pai = null;
                            paiRemovido = this.T;
                        }
                    }
                    else
                    {
                        P = getMax(T.esq);
                        paiRemovido = P.pai;
                        T.chave = P.chave;
                        T.item = P.item;
                    }
        }
        else
            if (chave < T.chave)
                Remove(T.esq, chave);
            else
                Remove(T.dir, chave);
        return T;
    }

    public TNodo getMax(TNodo T) {
        if (T.dir == null)
        {
            if (T.esq != null) T.esq.pai = T.pai;
            if (T.chave > T.pai.chave)
                T.pai.dir = T.esq;
            else
                T.pai.esq = T.esq;

            return T;
        }
        else
            return getMax(T.dir);
    }

    // ===================== CAMINHAMENTOS (NA03) =====================

    // pré-ordem sai desordenado - é o que entregamos pro mergesort ordenar
    public void preOrdem(List<Registro> out) {
        preOrdem(T, out);
    }

    private void preOrdem(TNodo T, List<Registro> out) {
        if (T != null) {
            out.add(T.item);
            preOrdem(T.esq, out);
            preOrdem(T.dir, out);
        }
    }

    // em-ordem visita os nós de forma ordenada
    public void emOrdem(List<Registro> out) {
        emOrdem(T, out);
    }

    private void emOrdem(TNodo T, List<Registro> out) {
        if (T != null) {
            emOrdem(T.esq, out);
            out.add(T.item);
            emOrdem(T.dir, out);
        }
    }

    // altura da árvore reaproveitando o balpreOrdem
    public int altura() {
        h = 0;
        balpreOrdem(T, 0);
        return h;
    }
}
