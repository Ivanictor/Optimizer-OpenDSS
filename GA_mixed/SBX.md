# Simulated Binary Crossover

O algoritmo SBX é utilizado pelo pymoo de forma padrão (se não for alterado) para algoritmos GA de variáveis mistas. O objetivo do processo realizado por ele é promover o "cruzamento" (crossover) entre dois indíviduos (soluções) da geração atual para gerar dois "descendentes", que são duas novas soluções distintas das iniciais, com grau de distinção variável em relação às soluções pais. O GA seleciona as melhores soluções dentre as testadas, as emparelha e realiza o crossover, de modo a tentar extrair as características que otimizem a solução do problema. 

Para variáveis reais, o procedimento é realizado da seguinte forma:

1) Utiliza-se um número aleatório (distribuição uniforme) u, entre 0 e 1, e o índice de distribuição $$ \eta_c $$, que é definido como 15 na biblioteca, o algoritmo calcula um fator de distribuição $$ \beta_q $$ 

$$
\beta_q =
\begin{cases}
(2u)^{\frac{1}{\eta_c+1}}, & u\leq 0.5\\
\left(\frac{1}{2(1-u)}\right)^{\frac{1}{\eta_c+1}}, & u>0.5
\end{cases}
$$

2) Considerando-se as soluções "pais" como sendo os indivíduos P1 = [100, 200, 300] e P2 = [200, 400, 100], realiza-se o cálculo abaixo para obter as duas novas soluções ("filhas").
$$
\[
C_1=\frac{1}{2}[(1+\beta_q)P_1+(1-\beta_q)P_2]
\]
$$

e

$$
\[
C_2=\frac{1}{2}[(1-\beta_q)P_1+(1+\beta_q)P_2]
\]
$$

3) Como a probabilidade padrão do algoritmo implementado no pymoo é 0.9, apenas 90% dos indivíduos selecionados realizam o crossover, nos outros 10% as soluções filhas são cópias dos pais

4) Para as variáveis inteiras, o resultado final após o crossover dos pais é arredondado para o valor inteiro mais próximo (Rounding Repair)