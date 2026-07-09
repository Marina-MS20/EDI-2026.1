// mergesort do benchmark (MainOrdenacao.Algoritmo), só trocando long[] por
// Registro[] e comparando pelo id - a mesma chave que os benchmarks ordenaram.
// foi o escolhido por ser o único sempre O(n log n) nas 5 distribuições
// testadas (o quicksort com pivô no primeiro elemento estoura a pilha com
// entrada já ordenada).
public class Ordenacao {

    public static class Counters {
        public long comparisons = 0;
        public long copies = 0;
    }

    private final Registro[] a;
    private final int nElems;
    private final Counters c;

    public Ordenacao(Registro[] data, Counters counters) {
        this.a      = data;
        this.nElems = data.length;
        this.c      = counters;
    }

    //--------------------------------------------------------------
    public void mergeSort()
    {
        if (nElems < 2) return;
        Registro[] workSpace = new Registro[nElems];
        recMergeSort(workSpace, 0, nElems - 1);
    }

    private void recMergeSort(Registro[] workSpace, int lowerBound, int upperBound)
    {
        if(lowerBound == upperBound)
            return;
        else
        {
            int mid = (lowerBound + upperBound)/2;
            recMergeSort(workSpace, lowerBound, mid);
            recMergeSort(workSpace, mid + 1, upperBound);
            merge(workSpace, lowerBound, mid + 1, upperBound);
        }
    }

    private void merge(Registro[] workSpace, int lowPtr, int highPtr, int upperBound)
    {
        int j = 0;
        int lowerBound = lowPtr;
        int mid = highPtr - 1;
        int n = upperBound - lowerBound + 1;
        while(lowPtr <= mid && highPtr <= upperBound)
        {
            c.comparisons++;
            if(a[lowPtr].id < a[highPtr].id)
                workSpace[j++] = a[lowPtr++];
            else
                workSpace[j++] = a[highPtr++];
            c.copies++;
        }
        while(lowPtr <= mid) {
            workSpace[j++] = a[lowPtr++];
            c.copies++;
        }
        while(highPtr <= upperBound) {
            workSpace[j++] = a[highPtr++];
            c.copies++;
        }
        for(j = 0; j < n; j++) {
            a[lowerBound + j] = workSpace[j];
            c.copies++;
        }
    }
    //--------------------------------------------------------------
}
