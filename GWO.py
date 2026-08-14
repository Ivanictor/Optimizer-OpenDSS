import numpy as np

X = np.random.randint(1, 34, size=(33, 3))

def opendss_solver(candidate):
    return candidate

X_dict = {}
a = 2

for wolf in X:
    j = 0
    X_dict[f"wolf {j}"]["buses"] = wolf
    X_dict[f"wolf {j}"]["rpf"] = opendss_solver(wolf)


def evaluate_wolf(x_dict):
    alpha = beta = delta = float("inf")

    X_alpha = X_beta = X_delta = None

    for i in range(len(X_dict)):
        wolf = x_dict[f"wolf {i}"]

        if wolf["rpf"] < alpha:
            delta, X_delta = beta, X_beta
            beta, X_beta = alpha, X_alpha
            alpha, X_alpha = wolf["rpf"], wolf["buses"]

        elif wolf["rpf"] < beta:
            delta, X_delta = beta, X_beta
            beta, X_beta = wolf["rpf"], wolf["buses"]

        elif wolf["rpf"] < delta:
            delta, X_delta = wolf["rpf"], wolf["buses"]

    return X_alpha, X_beta, X_delta

X_alpha, X_beta, X_delta = evaluate_wolf(X_dict)

C_alpha = np.random.uniform(0, 2, size=(33, 3))
C_beta = np.random.uniform(0, 2, size=(33, 3))
C_delta = np.random.uniform(0, 2, size=(33, 3))

A_alpha = np.random.uniform(0, 2, size=(33, 3))
A_beta = np.random.uniform(0, 2, size=(33, 3))
A_delta = np.random.uniform(0, 2, size=(33, 3))

D_alpha = abs(C_alpha*X_alpha - X)
D_beta = abs(C_beta*X_alpha - X)
D_delta = abs(C_delta*X_delta - X)

X1 = X_alpha - A_alpha*D_alpha
X2 = X_beta - A_beta*D_beta
X3 = X_delta - A_delta*D_delta

X = round((X1 + X2 + X3)/3)



