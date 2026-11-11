import numpy as np
import pickle
from pymoo.core.problem import Problem
from pymoo.core.variable import Real, Integer
from pymoo.core.repair import Repair
from pymoo.core.mixed import MixedVariableGA
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from opendss_solver import initialize_opendss, solve_circuit

dss, dss_tools, trafo_df, loads_df, buses_df, lines_df = initialize_opendss()
buses = buses_df["name"].unique().tolist()


class MyMixedProblem(Problem):
    def __init__(self, buses, k=5, max_power=500.0):
        self.buses = buses
        self.k = k

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
            resultado, converged, energy = solve_circuit(dss, selected_buses, powers, trafo_df, buses_df, lines_df)

            if resultado == 0 or np.isnan(resultado) or np.isinf(resultado):
                valor_fitness = 1e6
                fitness.append(1e6)
            
            elif resultado > -6000:
                valor_fitness = 1e6
                fitness.append(1e6)

            elif energy < 1000 or energy > 100000:
                valor_fitness = 1e6
                fitness.append(1e6)

            elif not converged:
                valor_fitness = 1e6
                fitness.append(1e6)
            
            else:
                fitness.append(abs(resultado))
                valor_fitness = abs(resultado)

            if valor_fitness < self.melhor_fitness:
                self.melhor_fitness = valor_fitness

            #Registro de melhor resultado geral a cada geração, média por população (com e sem penalidade) e contagem de soluções convergentes por população
            self.soma_fitness += valor_fitness
            self.contador += 1

            if converged and valor_fitness != 1e6:
                self.contador_convergencia += 1
                self.soma_fitness_converg += valor_fitness

            if self.contador % 100 == 0:
                self.medias.append(self.soma_fitness / 100)
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

medias_pop = problem_mixed.medias
melhor_fitness_pop = problem_mixed.melhor_fitness_pop
medias_pop_converg = problem_mixed.medias_converg
contador_converg = problem_mixed.contador_convergencia_pop

with open("medias.pkl", "wb") as arquivo:
    pickle.dump(medias_pop, arquivo)

with open("medias_converg.pkl", "wb") as arquivo:
    pickle.dump(medias_pop_converg, arquivo)

with open("fitness.pkl", "wb") as arquivo:
    pickle.dump(melhor_fitness_pop, arquivo)

with open("contador_converg.pkl", "wb") as arquivo:
    pickle.dump(contador_converg, arquivo)

print("Barras selecionadas:", selected_buses)
print("Potências alocadas:", [round(float(p), 2) for p in powers])
print("Fitness:", res_mixed.F)

with open("Resultados GA Alim Reduzido.txt", "w", encoding="utf-8") as f:
    f.write(f"Barras selecionadas:  {selected_buses}\n")
    f.write(f"Potências alocadas: {[round(float(p), 2) for p in powers]}\n")
    f.write(f"Fitness: {res_mixed.F}\n")
    f.write(f"Médias por geração: {str(medias_pop)}\n")
    f.write(f"Médias por geração sem penalidades: {str(medias_pop_converg)}\n")
    f.write(f"Melhor resultado geral a cada geração: {str(melhor_fitness_pop)}\n")
    f.write(f"Quantidade de indivíduos que convergiram a cada geração: {str(contador_converg)}")