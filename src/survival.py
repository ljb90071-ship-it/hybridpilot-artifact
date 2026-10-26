"""Finite-cap conditional remaining posting positions (Equation 9)."""
from fractions import Fraction

def remaining(stopping_counts, spent):
    if spent < 0 or any(t < 1 or count < 0 for t,count in stopping_counts.items()):
        raise ValueError('Nonnegative exposure and finite positive stopping positions required')
    survivors=sum(count for t,count in stopping_counts.items() if t>spent)
    if not survivors: raise ValueError('Continuation is already exhausted')
    return Fraction(sum((t-spent)*count for t,count in stopping_counts.items() if t>spent),survivors)
