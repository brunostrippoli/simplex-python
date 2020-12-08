#!/usr/bin/python3


class NoMinNegativeValue(Exception):
    """Nenhum valor negativo mínimo é encontrado no problema de minimização"""
    pass


class NoMinPositiveValue(Exception):
    """Nenhum valor positivo mínimo é encontrado nas relações"""
    pass


class NoMaxPostiveValue(Exception):
    """Nenhum valor positivo máximo é encontrado no problema de maximização"""
    pass
class DegeneranceProblem(Exception):
    """É um problema de degeneração"""
    pass