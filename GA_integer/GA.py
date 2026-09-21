import numpy as np
from pymoo.core.problem import Problem
from pymoo.core.sampling import Sampling
from pymoo.core.crossover import Crossover
from pymoo.core.mutation import Mutation
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from opendss_solver import initialize_opendss, solve_circuit

dss, dss_tools, trafo_df, loads_df, buses_df, lines_df = initialize_opendss()

buses = buses_df["name"].unique().tolist()  # buses_df para todos os barramentos, loads_df para as cargas


class MyIntegerProblem(Problem):
    def __init__(self, buses, k=5):
        self.buses = buses
        self.k = k
        super().__init__(n_var=k, n_obj=1, n_constr=0, xl=0, xu=len(buses) - 1, vtype=int)

    def _evaluate(self, x, out, *args, **kwargs):
        fitness = []

        for individual in x:
            indices = np.unique(individual.astype(int))
            selected_buses = [self.buses[i] for i in indices]

            resultado = solve_circuit(dss, selected_buses, trafo_df, buses_df, lines_df)

            fitness.append(abs(resultado))

        out["F"] = np.array(fitness)


class UniqueIntegerSampling(Sampling):
    def _do(self, problem, n_samples, **kwargs):
        n_total = int(problem.xu[0]) + 1
        X = np.empty((n_samples, problem.n_var), dtype=int)
        for i in range(n_samples):
            X[i, :] = np.random.choice(n_total, problem.n_var, replace=False)
        return X


class UniqueUniformCrossover(Crossover):
    def __init__(self):
        super().__init__(2, 2)  # 2 pais -> 2 filhos

    #Crossover uniforme
    def _do(self, problem, X, **kwargs):
        _, n_matings, n_var = X.shape
        Y = np.empty_like(X)
        n_total = int(problem.xu[0]) + 1

        for k in range(n_matings):
            p1, p2 = X[0, k], X[1, k]
            mask = np.random.random(n_var) < 0.5               

            for child_idx, (a, b) in enumerate([(p1, p2), (p2, p1)]):
                child = np.where(mask, a, b).astype(int)
                self._repair(child, n_total)
                Y[child_idx, k] = child

        return Y

    #Filtra e substitui valores duplicados
    def _repair(self, child, n_total):
        seen = set()
        duplicated_pos = []
        for i, gene in enumerate(child):
            if gene in seen:
                duplicated_pos.append(i)
            else:
                seen.add(gene)
        available = list(set(range(n_total)) - seen)
        np.random.shuffle(available)
        for pos, val in zip(duplicated_pos, available):
            child[pos] = val


class UniqueSwapMutation(Mutation):
    def __init__(self, prob=0.3):
        super().__init__()
        self.prob = prob

    def _do(self, problem, X, **kwargs):
        n_total = int(problem.xu[0]) + 1
        for individual in X:
            if np.random.random() < self.prob:
                pos = np.random.randint(len(individual))
                current = set(individual)
                available = list(set(range(n_total)) - current)
                if available:
                    individual[pos] = np.random.choice(available)
        return X


algorithm_int = GA(
    pop_size=100,
    sampling=UniqueIntegerSampling(),
    crossover=UniqueUniformCrossover(),
    mutation=UniqueSwapMutation(prob=0.3),
    eliminate_duplicates=True,
)

problem = MyIntegerProblem(buses=buses, k=5)
res_int = minimize(problem, algorithm_int, get_termination("n_gen", 100), seed=1)

print("n_var:", problem.n_var)
print("buses:", len(buses), buses[:10])
print("X shape:", np.shape(res_int.X), type(res_int.X))

best_x = res_int.X
indices = np.unique(best_x.astype(int))
selected_buses = [buses[i] for i in indices]

print("Barras selecionadas:", selected_buses)
print("Fitness:", res_int.F)