from __future__ import annotations


__all__ = ["defs"]


def __getattr__(name: str):
    if name != "defs":
        raise AttributeError(name)

    from .definitions import defs

    return defs
