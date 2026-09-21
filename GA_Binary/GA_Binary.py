import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.operators.crossover.hux import HUX
from pymoo.operators.mutation.bitflip import BitflipMutation
from opendss_solver import initialize_opendss, solve_circuit

dss, dss_tools, trafo_df, loads_df, buses_df, lines_df = initialize_opendss()

buses = loads_df["bus1"].unique().tolist()

class MyBinaryProblem(Problem):
    def __init__(self, buses, n_constr_max=5):
        self.buses = buses
        self.max_units = n_constr_max
        super().__init__(n_var=len(buses), n_obj=1, n_constr=1, xl=0, xu=1, vtype=bool)

    def _evaluate(self, x, out, *args, **kwargs):
        fitness = []
        constraints = []

        for individual in x:
            indices = np.where(individual == 1)[0]
            n_selected = np.sum(individual)

            g = n_selected - 5
            constraints.append(g)

            if g > 0:
                fitness.append(1e6)
                continue

            selected_buses = [buses[i] for i in indices]

            resultado = solve_circuit(dss, selected_buses, trafo_df, buses_df, lines_df)

            fitness.append(abs(resultado))

        out["F"] = np.array(fitness)
        out["G"] = np.array(constraints).reshape(-1, 1)

algorithm_bin = GA(
    pop_size=100,
    sampling=BinaryRandomSampling(),
    crossover=HUX(),
    mutation=BitflipMutation(),
    eliminate_duplicates=True,
)

problem = MyBinaryProblem(buses=buses, n_constr_max=3)
res_bin = minimize(problem, algorithm_bin, get_termination("n_gen", 100), seed=1)
print(res_bin.X, res_bin.F)

best_x = res_bin.X                      
indices = np.where(best_x == 1)[0]      
selected_buses = [buses[i] for i in indices]

print("Barras selecionadas:", selected_buses)
print("Fitness:", res_bin.F)