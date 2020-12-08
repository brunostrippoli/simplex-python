#!/usr/bin/python3

from typing import Dict, List
from .exceptions import *
from fractions import Fraction

phase1_iterations = list()
phase2_iterations = list()


def get_min_negative(lst: list):
    negative_values: list = list(filter(lambda x: True if x < 0 else False, lst))
    if len(negative_values):
        return lst.index(min(negative_values))
    else:
        raise NoMinNegativeValue


def get_min_positive(lst: list):
    positive_values: list = list(filter(lambda x: True if x > 0 else False, lst))
    if len(positive_values):
        return lst.index(min(positive_values))
    else:
        raise NoMinPositiveValue


def get_max_positive(lst: list):
    positive_values: list = list(filter(lambda x: True if x > 0 else False, lst))
    if len(positive_values):
        return lst.index(max(positive_values))
    else:
        raise NoMaxPostiveValue


def get_pivot(matrix: List[List[float]], costs: List[float], constraints: List[float], nature: bool):
    m = len(matrix)
    if nature:
        jpivot: int = get_min_negative(costs)
        ratios: list = list()
        for i in range(m):
            try:
                ratios.append(constraints[i] / matrix[i][jpivot])
            except ZeroDivisionError:
                ratios.append(-1)
        ipivot: int = get_min_positive(ratios)
        return ipivot, jpivot
    else:
        jpivot: int = get_max_positive(costs)
        ratios: list = list()
        for i in range(m):
            try:
                ratios.append(constraints[i] / matrix[i][jpivot])
            except ZeroDivisionError:
                ratios.append(-1)
        ipivot = get_min_positive(ratios)
        return ipivot, jpivot


class Simplex:
    def __init__(self, n: int, m: int, a: List[List[float]], b: List[float], constraints: List[str], obj_func: List[
        float], nature: bool = True):
        self.error_message: str = ""
        self.n = n
        self.m = m
        self.a = a
        self.b = b
        self.constraints = constraints
        self.obj_func = obj_func
        self.nature: bool = nature
        self.unknowns: Dict[str, float] = dict()
        self.shift_vars: Dict[str, float] = dict()
        self.artificial_vars: Dict[str, float] = dict()
        self.vars_names: List[str] = list()
        self.base_vars_names: List[str] = list()
        self.table: List[List[float]] = list()
        self.table_cost: float = 0
        self.table_cost_phase2: float = 0
        self.Za: List[List[float], float] = [list(), 0]
        self.table_coef: List[float] = list()
        self.table_coef_phase2: List[float] = list()
        self.table_constraints: List[float] = list()
        self.phase1_steps = list()
        self.phase2_steps = list()
        for i in range(self.m):
            if self.constraints[i] == 'lt':
                self.shift_vars['e' + str(i + 1)] = 1
            elif self.constraints[i] == 'gt':
                self.shift_vars['e' + str(i + 1)] = -1
                if self.b[i] != 0:
                    self.artificial_vars['a' + str(i + 1)] = 1
            else:
                if self.b[i] != 0:
                    self.artificial_vars['a' + str(i + 1)] = 1
        self._construct_table_phase1()
        if len(self.artificial_vars):
            result_phase1 = self.phase1()
            if result_phase1:
                print("Construindo tabela do Passo 2")
                self._phase1_to_phase2_table()
                self.print_state(True)
                self.phase2()
            else:
                pass
        else:
            print("O Passo 1 não é necessário!")
            self._construct_phase2_table()
            self.print_state(False)
            self.phase2()


    def _construct_table_phase1(self):
        self.table = self.a
        k: int = 0
        l: int = len(self.shift_vars)
        p: int = len(self.shift_vars) + len(self.artificial_vars)

        for i in range(self.m):
            zeros = [0 for _ in range(p)]
            if 'e' + str(i + 1) in self.shift_vars:
                zeros[k] = self.shift_vars['e' + str(i + 1)]
                k += 1
            if 'a' + str(i + 1) in self.artificial_vars:
                zeros[l] = self.artificial_vars['a' + str(i + 1)]
                l += 1
            self.table[i] = self.table[i] + zeros
            self.table_constraints.append(self.b[i])
        for i in range(self.n):
            self.unknowns['x' + str(i + 1)] = 0
        for var in self.shift_vars:
            self.shift_vars[var] = 0
        for var in self.artificial_vars:
            self.artificial_vars[var] = 0
        self.vars_names = list(self.unknowns.keys()) + list(self.shift_vars.keys()) + list(self.artificial_vars.keys())
        for i in range(self.m):
            if 'a' + str(i + 1) in self.artificial_vars:
                self.artificial_vars['a' + str(i + 1)] = self.b[i]
                self.base_vars_names.append('a' + str(i + 1))
            else:
                if 'e' + str(i + 1) in self.shift_vars:
                    self.shift_vars['e' + str(i + 1)] = self.b[i]
                    self.base_vars_names.append('e' + str(i + 1))
        p: int = self.n + len(self.shift_vars) + len(self.artificial_vars)
        za: List[float] = [0 for _ in range(p)]
        const_b: float = 0
        for var in self.artificial_vars:
            i: int = int(var[1]) - 1
            tmp: List[float] = [-1 * self.table[i][j] for j in range(p)]
            for j in range(len(tmp)):
                za[j] += tmp[j]
            const_b += self.b[i]
        self.Za[0] = za[:self.n + len(self.shift_vars)]
        self.Za[1] = const_b
        self.table_coef = self.Za[0] + [0 for _ in range(len(self.artificial_vars))]
        self.table_cost = const_b
        self.table_coef_phase2 = self.obj_func[0] + [0 for _ in range(len(self.shift_vars) + len(self.artificial_vars))]
        self.table_cost_phase2 = self.obj_func[1]
        self.store_iterations(
            list(self.vars_names),
            list(self.base_vars_names),
            self.table,
            self.table_constraints,
            self.table_coef,
            self.table_cost,
            True
        )
        self.print_state(True)


    def _construct_phase2_table(self):
        p: int = self.n + len(self.shift_vars)
        self.table_coef = self.obj_func[0] + [0 for _ in range(p-self.n)]
        self.table_cost = self.obj_func[1]


    def _phase1_to_phase2_table(self):
        p:int = self.n + len(self.shift_vars)
        const_coef: float = self.obj_func[1]
        self.table = [line[:p] for line in self.table]
        self.vars_names = self.vars_names[:p]
        self.table_coef = self.table_coef_phase2[:self.n + len(self.shift_vars)]
        self.table_cost = const_coef + self._calculate_table_cost(self.unknowns, self.obj_func)
        self.store_iterations(
            list(self.vars_names),
            list(self.base_vars_names),
            self.table,
            self.table_constraints,
            self.table_coef,
            self.table_cost,
            False         
        )
        self.print_state(False)


    def phase1(self):
        while self.table_cost:
            ipivot: int = 0
            jpivot: int = 0
            pivot: float = 0.0
            p: int = self.n + len(self.shift_vars) + len(self.artificial_vars)
            try:
                ipivot, jpivot = get_pivot(self.table, self.table_coef, self.table_constraints, True)
                pivot = self.table[ipivot][jpivot]
            except NoMinNegativeValue:
                print("ERRO: Fim do 1º Passo")
                if self.table_cost:
                    print("Não há solução possível para este problema")
                    self.error_message = "Não há solução possível para este problema"
                return False
            except NoMinPositiveValue:
                print("ERRO: Não foi encontrado nenhum mínimo de razão.")
                self.error_message = "ERRO: Não foi encontrado nenhum mínimo de razão."
                break
            except DegeneranceProblem:
                print("ERRO")
                self.error_message = "ERRO"
                break
            except Exception as e:
                raise e
            for i in range(p):
                self.table[ipivot][i] /= pivot
            else:
                self.table_constraints[ipivot] /= pivot
            for i in range(self.m):
                if i != ipivot:
                    multiplier: float = self.table[i][jpivot]
                    for j in range(p):
                        self.table[i][j] = self.table[i][j] - self.table[ipivot][j] * multiplier
                    else:
                        self.table_constraints[i] -= self.table_constraints[ipivot] * multiplier
            else:
                multiplier: float = self.table_coef[jpivot]
                for i in range(p):
                    self.table_coef[i] -= self.table[ipivot][i] * multiplier
                multiplier: float = self.table_coef_phase2[jpivot]
                for i in range(p):
                    self.table_coef_phase2[i] -= self.table[ipivot][i] * multiplier
            entering: str = self.vars_names[jpivot]
            self.base_vars_names[ipivot] = entering
            for var in self.unknowns: self.unknowns[var] = 0
            for var in self.shift_vars: self.shift_vars[var] = 0
            for var in self.artificial_vars: self.artificial_vars[var] = 0
            for i in range(self.m):
                var: str = self.base_vars_names[i]
                if var in self.unknowns:
                    self.unknowns[var] = self.table_constraints[i]
                if var in self.shift_vars:
                    self.shift_vars[var] = self.table_constraints[i]
                if var in self.artificial_vars:
                    self.artificial_vars[var] = self.table_constraints[i]
            self.table_cost = self._calculate_table_cost({**self.unknowns, **self.shift_vars}, self.Za)
            self.table_cost_phase2 = self._calculate_table_cost(self.unknowns, self.obj_func)
            self.store_iterations(
                list(self.vars_names),
                list(self.base_vars_names),
                self.table,
                self.table_constraints,
                self.table_coef,
                self.table_cost,
                True
            )
        return True


    def phase2(self):
        while True:
            ipivot: int = 0
            jpivot: int = 0
            pivot: float = 0.0
            p: int = self.n + len(self.shift_vars)
            if self.nature:
                try:
                    ipivot, jpivot = get_pivot(self.table, self.table_coef, self.table_constraints, True)
                except NoMinNegativeValue:
                    print("Fim do algoritmo minimização!")
                    print("Solução: ", end=" ")
                    for var in self.unknowns:
                        print("{}: {}".format(var, self.unknowns[var]), end=" ")
                    print("")
                    break
                except Exception as e:
                    raise e
            else:
                try:
                    ipivot, jpivot = get_pivot(self.table, self.table_coef, self.table_constraints, False)
                except NoMaxPostiveValue:
                    print('Fim do algoritmo maximização!')
                    print("Solução: ", self.unknowns)
                    break
                except NoMinPositiveValue:
                    print("ERRO: Não foi encontrado nenhum mínimo de razão!")
                    self.error_message = "ERRO: Não foi encontrado nenhum mínimo de razão!"
                    break
                except Exception as e:
                    raise e
            pivot = self.table[ipivot][jpivot]
            for i in range(p):
                self.table[ipivot][i] /= pivot
            else:
                self.table_constraints[ipivot] /= pivot
            for i in range(self.m):
                if i is not ipivot:
                    multiplier: float = self.table[i][jpivot]
                    for j in range(p):
                        self.table[i][j] -= multiplier * self.table[ipivot][j]
                    else:
                        self.table_constraints[i] -= multiplier * self.table_constraints[ipivot]
            else:
                multiplier = self.table_coef[jpivot]
                for i in range(p):
                    self.table_coef[i] -= multiplier * self.table[ipivot][i]
            entering: str = self.vars_names[jpivot]
            self.base_vars_names[ipivot] = entering
            for var in self.unknowns: self.unknowns[var] = 0
            for var in self.shift_vars: self.shift_vars[var] = 0
            for i in range(self.m):
                var: str = self.base_vars_names[i]
                if var in self.unknowns:
                    self.unknowns[var] = self.table_constraints[i]
                if var in self.shift_vars:
                    self.shift_vars[var] = self.table_constraints[i]
            self.table_cost = self._calculate_table_cost(self.unknowns, self.obj_func)
            self.store_iterations(
                list(self.vars_names),
                list(self.base_vars_names),
                self.table,
                self.table_constraints,
                self.table_coef,
                self.table_cost,
                False
            )
            self.print_state(False)


    def _calculate_table_cost(self, vars_names: Dict[str, float], Za: List[float]):
        res: float = Za[1]
        coef: list = Za[0]
        for key,value in list(zip(list(vars_names.keys()), coef)):
            res += vars_names[key] * value

        return res


    def store_iterations(
        self,
        vars_names,
        base_vars_names,
        table,
        table_constraints,
        table_coef,
        table_cost,
        phase
    ):
        variables_names = [var for var in vars_names]
        base_variables_names = [var for var in base_vars_names]
        matrix_table = [[var for var in line] for line in table]
        constraints = [var for var in table_constraints]
        coefs = [var for var in table_coef]
        cost = table_cost
        if phase:
            self.phase1_steps.append([
                variables_names,
                base_variables_names,
                matrix_table,
                constraints,
                coefs,
                cost
            ])
        else:
            self.phase2_steps.append([
                variables_names,
                base_vars_names,
                matrix_table,
                constraints,
                coefs,
                cost
            ])


    def print_state(self, nature: bool):
        print("Desconhecidos: ", end="{")
        for var in self.unknowns:
            print("{}: {} ".format(var, self.unknowns[var]), end="")
        print("}")
        print("Trocando Variáveis: ", end="{")
        for var in self.shift_vars:
            print("{}: {} ".format(var, self.shift_vars[var]), end="")
        print("}")
        if nature:
            print("Variáveis de Apoio: ", end="{")
            for var in self.artificial_vars:
                print("{}: {}, ".format(var, self.artificial_vars[var]), end="")
            print("}")
        print("*", end=" | ")
        for var in self.vars_names:
            print("{}".format(var), end="\t")
        else:
            print(" | Restrições")
        for i in range(self.m):
            print(self.base_vars_names[i], end=" | ")
            for var in self.table[i]:
                print("{}".format(var), end="\t")
            else:
                print(" | {}".format(self.table_constraints[i]))
        print("Z ", end=" | ")
        for var in self.table_coef:
            print("{}".format(var), end="\t")
        else:
            print(" | {}".format(self.table_cost))
        print("=" * 20)


if __name__ == '__main__':
    n:int = 2
    m: int = 4
    a = [
        [Fraction(1, 10), Fraction(0)],
        [Fraction(0), Fraction(1, 10)],
        [Fraction(1, 10), Fraction(2, 10)],
        [Fraction(2, 10), Fraction(1, 10)]
    ]
    b = [Fraction(4, 10), Fraction(6, 10), Fraction(2), Fraction(17, 10)]
    const = ['gt', 'gt', 'gt', 'gt']
    objective_function = [Fraction(100), Fraction(40)]
    simplex = Simplex(n, m, a, b, const, [objective_function, 0], True)
    print(len(simplex.phase1_steps))
    for iteration in simplex.phase1_steps:
        print(iteration)
        print("="*100)
    print("Fim da execução!")
