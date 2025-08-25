// --- CONJUNTOS
{string} MateriasPrimas = ...;
{string} Elementos = ...;
{int} Pacotes = ...;

// --- PARÂMETROS
float Estoque[MateriasPrimas] = ...;
float ComposicaoQuimica[MateriasPrimas][Elementos] = ...;
float LimitesConcentracao[Elementos][1..2] = ...;
float LIb = ...;
float LSb = ...;
float LIp = ...;
float LSp = ...;
int MaxTiposPorPacote = ...;

// --- VARIÁVEIS DE DECISÃO ---
dvar float+ x[MateriasPrimas][Pacotes];      // Quantidade (kg) da matéria-prima i no pacote j
dvar boolean y[MateriasPrimas][Pacotes];     // 1 se a matéria-prima i é usada no pacote j, 0 caso contrário
dvar float+ desvioMaximo[Elementos];         // Variável auxiliar para a nova função objetivo

// --- EXPRESSÕES LINEARES ---

// Peso total de cada pacote
dexpr float pesoPacote[j in Pacotes] = 
    sum(i in MateriasPrimas) x[i][j];

// Quantidade total de cada elemento químico em cada pacote
dexpr float qtdeElemento[k in Elementos][j in Pacotes] = 
    sum(i in MateriasPrimas) (ComposicaoQuimica[i][k] / 100) * x[i][j];

// --- FUNÇÃO OBJETIVO (LINEARIZADA) ---

// Minimizar a soma dos desvios máximos (range) da quantidade de cada elemento entre os pacotes.
// Isso promove a uniformidade, que era o objetivo original do desvio padrão.
minimize sum(k in Elementos) desvioMaximo[k];

// --- RESTRIÇÕES ---
subject to {
    // R1: Limites de peso do pacote
    forall(j in Pacotes) {
        ctPesoPacote: LIp <= pesoPacote[j] <= LSp;
    }

	// R2: Relação entre x e y com "Big-M"
    forall(i in MateriasPrimas, j in Pacotes) {
        ctBigM_U: x[i][j] <= LSb * y[i][j];
        ctBigM_L: x[i][j] >= LIb * y[i][j];
    }

    // R3: Limite de tipos de matéria-prima por pacote
    forall(j in Pacotes) {
        ctMaxTipos: sum(i in MateriasPrimas) y[i][j] <= MaxTiposPorPacote;
    }
    
    // R4: Limites de concentração química (LINEARIZADA)
    forall(k in Elementos, j in Pacotes) {
        ctConcMin: LimitesConcentracao[k][1] / 100 * pesoPacote[j] <= qtdeElemento[k][j];
        ctConcMax: qtdeElemento[k][j] <= LimitesConcentracao[k][2] / 100 * pesoPacote[j];
    }

    // R6: Restrições para a nova função objetivo (LINEARIZADA)
    // Força 'desvioMaximo[k]' a ser maior ou igual à diferença entre a quantidade do elemento k
    // em qualquer par de pacotes (j1, j2).
    forall(k in Elementos, j1 in Pacotes, j2 in Pacotes) {
        ctDesvio: qtdeElemento[k][j1] - qtdeElemento[k][j2] <= desvioMaximo[k];
    }
    
     // R7: Limite de estoque
    forall(i in MateriasPrimas) {
        ctEstoque: sum(j in Pacotes) x[i][j] <= Estoque[i];
    }
}

execute {
  var ofile = new IloOplOutputFile("solucao.txt");
  ofile.writeln("desvioMaximo = ", desvioMaximo, ";");
  ofile.writeln("x = ", x, ";");
  ofile.writeln("y = ", y, ";");
  ofile.close();
}

