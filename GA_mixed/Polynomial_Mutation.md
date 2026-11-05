# Mutação Polinomial

É a operação algorítmica que promove variabilidade nas soluções a serem testadas provocando mudanças aleatórias nas soluções. A equação geral é: 

$$
\[
x'=x+\delta_q(x_U-x_L)
\]
$$

Sendo $$ x_U $$ o limite superior, $$ x_L $$ o limite inferior, $$ \delta_q $$ um valor calculado, x o valor original da variável e x' o valor após a mutação

$$ \delta_q $$ é calculado pela expressão: 

$$
\[
\delta_q=
\begin{cases}
\left[2u+(1-2u)(1-\delta_1)^{\eta_m+1}\right]^{\frac{1}{\eta_m+1}}-1,
&u\leq0.5\\[8pt]
1-\left[2(1-u)+2(u-0.5)(1-\delta_2)^{\eta_m+1}\right]^{\frac{1}{\eta_m+1}},
&u>0.5
\end{cases}
\]
$$

Sendo as distâncias normalizadas até os limites iguais a: 
$$
\[
\delta_1=\frac{x-x_L}{x_U-x_L}
\]
$$

$$
\[
\delta_2=\frac{x_U-x}{x_U-x_L}
\]
$$