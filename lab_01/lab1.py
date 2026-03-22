import math
from math import exp, sqrt, cos
import matplotlib.pyplot as plot

curr = 1

def binary_random_generator():
    global curr
    a = 16807
    b = 0
    c = 2147483647
    curr = (a * curr + b) % c
    return curr / c


def poisson_gen(l, n):
    data = []
    q = exp(-l)
    for i in range(n):
        X = -1
        S = 1
        while (S > q):
            U = binary_random_generator()
            S=S * U
            X+=1
        data.append(X)
    return data

def gauss_gen(avg, var, n):
    data = []
    for i in range(n // 2 + 1):
        X1 = 0
        X2 = 0
        U1 = binary_random_generator()
        U2 = binary_random_generator()
        X1 = sqrt(-2*math.log(U1))*cos(2*math.pi*U2)
        X2 = sqrt(-2*math.log(U1))*math.sin(2*math.pi*U2)
        X1 = avg + var * X1
        X2 = avg + var * X2
        data.append(X1)
        data.append(X2)
    return data

plot.hist(poisson_gen(14, 1000000), bins=100)
plot.show()

plot.hist(gauss_gen(14, 123, 1000000), bins=100)
plot.show()
