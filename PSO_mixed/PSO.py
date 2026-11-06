import numpy as np
import pickle
from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.optimize import minimize

from opendss_solver import initialize_opendss, solve_circuit  # ajuste para o nome do seu arquivo

dss, dss_tools, trafo_df, loads_df, buses_df, lines_df = initialize_opendss()
buses = buses_df["name"].unique().tolist()

N_INT = 5
N_REAL = 5
INT_MIN, INT_MAX = 1, len(buses)
REAL_MIN, REAL_MAX = 0.0, 500.0
POP_SIZE = 100

# Ordem do vetor X: [5 inteiras | 5 reais]
INT_IDX = list(range(0, N_INT))
REAL_IDX = list(range(N_INT, N_INT + N_REAL))

def reparar_unicas(ints, lo, hi):
    """Troca valores repetidos pelo índice livre mais próximo (determinístico)."""
    usadas = set()
    duplicadas = []
    resultado = list(ints)

    for pos, v in enumerate(resultado):
        if v in usadas:
            duplicadas.append(pos)
        else:
            usadas.add(v)

    for pos in duplicadas:
        original = resultado[pos]
        d = 1
        while True:
            achou = False
            for cand in (original - d, original + d):
                if lo <= cand <= hi and cand not in usadas:
                    resultado[pos] = cand
                    usadas.add(cand)
                    achou = True
                    break
            if achou:
                break
            d += 1
    return resultado

class ProblemaMisto(Problem):
    def __init__(self, buses, pop_size):
        # Inteiros em [1, 1217] -> limites contínuos [0.5, 1217.5]
        xl = np.array([INT_MIN - 0.5] * N_INT + [REAL_MIN] * N_REAL)
        xu = np.array([INT_MAX + 0.5] * N_INT + [REAL_MAX] * N_REAL)

        self.buses = buses
        self.pop_size = pop_size

        #Variáveis para análise do desempenho do algoritmo
        self.contador = 0
        self.soma_fitness_converg = 0
        self.soma_fitness = 0
        self.medias = []
        self.medias_converg = []
        self.melhor_fitness = 1e6
        self.melhor_fitness_pop = []
        self.contador_convergencia = 0
        self.contador_convergencia_pop = []

        #Variáveis para o init da classe pai Problem
        super().__init__(n_var=N_INT + N_REAL, n_obj=1, xl=xl, xu=xu)

    @staticmethod
    def decodificar(X):
        X = np.atleast_2d(X).copy()
        X[:, INT_IDX] = np.clip(np.round(X[:, INT_IDX]), INT_MIN, INT_MAX)
        X[:, REAL_IDX] = np.clip(X[:, REAL_IDX], REAL_MIN, REAL_MAX)

        for row in X:  # row é uma view de X, então a atribuição altera X
            ints = row[INT_IDX].astype(int).tolist()
            row[INT_IDX] = reparar_unicas(ints, INT_MIN, INT_MAX)

        return X

    def _evaluate(self, X, out, *args, **kwargs):
        fitness = []
        Xd = self.decodificar(X)

        for x in Xd:
            inteiras = x[INT_IDX].astype(int).tolist()   # 5 inteiras (1..1217)
            selected_buses = [self.buses[i - 1] for i in inteiras]

            powers = x[REAL_IDX].tolist()                 # 5 reais (0..500)

            result, converged = solve_circuit(dss, selected_buses, powers, trafo_df, buses_df, lines_df)

            if result == 0 or np.isnan(result) or np.isinf(result):
                valor_fitness = 1e6
                fitness.append(1e6)
            
            elif result > -5000:
                valor_fitness = 1e6
                fitness.append(1e6)

            elif not converged:
                valor_fitness = 1e6
                fitness.append(1e6)
            
            else:
                fitness.append(abs(result))
                valor_fitness = abs(result)

            if valor_fitness < self.melhor_fitness:
                self.melhor_fitness = valor_fitness

            #Registro de melhor resultado geral a cada geração, média por população (com e sem penalidade) e contagem de soluções convergentes por população
            self.soma_fitness += valor_fitness
            self.contador += 1

            if converged and valor_fitness != 1e6:
                self.contador_convergencia += 1
                self.soma_fitness_converg += valor_fitness

            if self.contador % self.pop_size == 0:
                self.medias.append(self.soma_fitness / self.pop_size)
                self.melhor_fitness_pop.append(self.melhor_fitness)

                if self.contador_convergencia > 0:
                    self.medias_converg.append(self.soma_fitness_converg / self.contador_convergencia)

                else:
                    self.medias_converg.append(1e6)

                self.contador_convergencia_pop.append(self.contador_convergencia)

                self.soma_fitness = 0
                self.soma_fitness_converg = 0
                self.contador_convergencia = 0
                self.contador = 0

        out["F"] = np.array(fitness).reshape(-1, 1)


problem = ProblemaMisto(buses, pop_size=POP_SIZE)

algorithm = PSO(pop_size=POP_SIZE, w=0.9, c1=2.0, c2=2.0, adaptive=True)

res = minimize(
    problem,
    algorithm,
    ("n_gen", 100),
    seed=1,
    verbose=True,
)

medias_pop = problem.medias
melhor_fitness_pop = problem.melhor_fitness_pop
medias_pop_converg = problem.medias_converg
contador_converg = problem.contador_convergencia_pop

with open("medias_pso.pkl", "wb") as arquivo:
    pickle.dump(medias_pop, arquivo)

with open("medias_converg_pso.pkl", "wb") as arquivo:
    pickle.dump(medias_pop_converg, arquivo)

with open("fitness_pso.pkl", "wb") as arquivo:
    pickle.dump(melhor_fitness_pop, arquivo)

with open("contador_converg_pso.pkl", "wb") as arquivo:
    pickle.dump(contador_converg, arquivo)

x_otimo = problem.decodificar(res.X)[0]
print("Barras selecionadas:", [buses[i - 1] for i in x_otimo[INT_IDX].astype(int).tolist()])
print("Potências    :", x_otimo[REAL_IDX].tolist())
print("Fitness  :", res.F[0])