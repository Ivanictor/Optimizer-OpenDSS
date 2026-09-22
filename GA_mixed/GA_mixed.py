import numpy as np
from pymoo.core.problem import Problem
from pymoo.core.variable import Real, Integer
from pymoo.core.repair import Repair
from pymoo.core.mixed import MixedVariableGA
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from opendss_solver import initialize_opendss, solve_circuit

dss, dss_tools, trafo_df, loads_df, buses_df, lines_df = initialize_opendss()
buses = loads_df["bus1"].unique().tolist()


class MyMixedProblem(Problem):
    def __init__(self, buses, k=5, max_power=500.0):
        self.buses = buses
        self.k = k

        vars = {}
        for i in range(k):
            vars[f"power_{i}"] = Real(bounds=(0.0, max_power))
        for i in range(k):
            vars[f"bus_{i}"] = Integer(bounds=(0, len(buses) - 1))

        super().__init__(vars=vars, n_obj=1, n_constr=0)

    def _evaluate(self, X, out, *args, **kwargs):
        fitness = []

        for x in X:
            powers = [x[f"power_{i}"] for i in range(self.k)]
            bus_idx = [int(x[f"bus_{i}"]) for i in range(self.k)]

            selected_buses = [self.buses[i] for i in bus_idx]
            resultado = solve_circuit(dss, selected_buses, powers, trafo_df, buses_df, lines_df)

            if resultado == 0 or np.isnan(resultado) or np.isinf(resultado):
                fitness.append(1e6)
            else:
                fitness.append(abs(resultado))

        out["F"] = np.array(fitness)


class UniqueBusRepair(Repair):
    def _do(self, problem, X, **kwargs):
        n_total = len(problem.buses)
        for x in X:
            bus_idx = [x[f"bus_{i}"] for i in range(problem.k)]
            seen = set()
            dup_pos = []
            for i, b in enumerate(bus_idx):
                if b in seen:
                    dup_pos.append(i)
                else:
                    seen.add(b)
            available = list(set(range(n_total)) - seen)
            np.random.shuffle(available)
            for pos, val in zip(dup_pos, available):
                x[f"bus_{pos}"] = val
        return X


problem_mixed = MyMixedProblem(buses=buses, k=5, max_power=500.0)

algorithm_mixed = MixedVariableGA(pop_size=100, repair=UniqueBusRepair())

res_mixed = minimize(problem_mixed, algorithm_mixed, get_termination("n_gen", 100), seed=1)

best = res_mixed.X
powers = [best[f"power_{i}"] for i in range(5)]
bus_idx = [int(best[f"bus_{i}"]) for i in range(5)]
selected_buses = [buses[i] for i in bus_idx]

print("Barras selecionadas:", selected_buses)
print("Potências alocadas:", powers)
print("Fitness:", res_mixed.F)