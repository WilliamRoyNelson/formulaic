from .scoped_factor import ScopedFactor


class ScopedTerm:

    __slots__ = ("factors", "scale")

    def __init__(self, factors, scale=1):
        self.factors = tuple(dict.fromkeys(factors))
        self.scale = scale

    def __hash__(self):
        return hash(tuple(sorted(self.factors)))

    def __eq__(self, other):
        if isinstance(other, ScopedTerm):
            return sorted(self.factors) == sorted(other.factors)
        return NotImplemented

    def __repr__(self):
        factor_repr = (
            ":".join(f.__repr__() for f in self.factors) if self.factors else "1"
        )
        if self.scale is not None and self.scale != 1:
            return f"{self.scale}*{factor_repr}"
        return factor_repr

    def copy(self, *, without_values=False):
        factors = self.factors
        if without_values:
            factors = [
                ScopedFactor(
                    factor=factor.factor.replace(values=None),
                    reduced=factor.reduced,
                )
                for factor in factors
            ]
        return ScopedTerm(factors, scale=self.scale)
