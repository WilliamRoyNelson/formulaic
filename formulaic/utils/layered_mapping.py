import itertools
from collections.abc import MutableMapping
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

# Cached property was introduced in Python 3.8 (we currently support 3.7)
try:
    from functools import cached_property
except ImportError:  # pragma: no cover
    from cached_property import cached_property


class LayeredMapping(MutableMapping):
    """
    A mutable mapping implementation that allows you to stack multiple mappings
    on top of one another, passing key lookups through the stack from top to
    bottom until the key is found or the stack is exhausted. Mutations are
    stored in an additional layer local only to the `LayeredMapping` instance,
    and the layers passed in are never mutated.

    Nest named layers can be extracted via attribute lookups, or via
    `.named_layers`.
    """

    def __init__(self, *layers: Tuple[Optional[Mapping]], name: Optional[str] = None):
        """
        Crepare a `LayeredMapping` instance, populating it with the nominated
        layers.
        """
        self.name = name
        self._mutations: Dict = {}
        self._layers: List[Mapping] = self.__filter_layers(layers)

    @staticmethod
    def __filter_layers(layers: Iterable[Mapping]) -> List[Mapping]:
        """
        Filter incoming `layers` down to those which are not null.
        """
        return [layer for layer in layers if layer is not None]

    def __getitem__(self, key: Any) -> Any:
        for layer in [self._mutations, *self._layers]:
            if key in layer:
                return layer[key]
        raise KeyError(key)

    def __setitem__(self, key: Any, value: Any):
        self._mutations[key] = value

    def __delitem__(self, key: Any):
        if key in self._mutations:
            del self._mutations[key]
        else:
            raise KeyError(f"Key '{key}' not found in mutable layer.")

    def __iter__(self):
        keys = set()
        for layer in [self._mutations, *self._layers]:
            for key in layer:
                if key not in keys:
                    keys.add(key)
                    yield key

    def __len__(self):
        return len(set(itertools.chain(self._mutations, *self._layers)))

    def with_layers(
        self,
        *layers: Tuple[Optional[Mapping]],
        prepend: bool = True,
        inplace: bool = False,
        name: Optional[str] = None,
    ) -> "LayeredMapping":
        """
        Return a copy of this `LayeredMapping` instance with additional layers
        added.

        Args:
            layers: The layers to add.
            prepend: Whether to add the layers before (if `True`) or after (if
                `False`) the current layers.
            inplace: Whether to mutate the existing `LayeredMapping` instance
                instead of returning a copy.

        Returns:
            A reference to the `LayeredMapping` instance with the extra layers.
        """
        layers = self.__filter_layers(layers)
        if not layers:
            return self

        if inplace:
            self._layers = (
                [*layers, *self._layers] if prepend else [*self._layers, *layers]
            )
            self.name = name
            if "named_layers" in self.__dict__:
                del self.named_layers
            return self

        new_layers = [*layers, self] if prepend else [self, *layers]
        return LayeredMapping(*new_layers, name=name)

    # Named layer lookups and caching

    @cached_property
    def named_layers(self):
        named_layers = {}
        local = {}
        for layer in reversed(self._layers):
            if isinstance(layer, LayeredMapping):
                if layer.name:
                    local[layer.name] = layer
                named_layers.update(layer.named_layers)
        named_layers.update(local)
        if self.name:
            named_layers[self.name] = self
        return named_layers

    def __getattr__(self, attr):
        if attr not in self.named_layers:
            raise AttributeError(f"{repr(attr)} does not correspond to a named layer.")
        return self.named_layers[attr]
