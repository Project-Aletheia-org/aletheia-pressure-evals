"""Strict YAML config loading.

PyYAML's default loader silently keeps the last value when a mapping key is
repeated, so a copy-paste edit that leaves two `max_tokens:` entries in a
config file would be applied without any warning. Every config load in this
project goes through `load_yaml_strict` instead, which raises immediately.
"""

from __future__ import annotations

from pathlib import Path

import yaml


class DuplicateKeyError(ValueError):
    pass


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: yaml.SafeLoader, node: yaml.Node, deep: bool = False) -> dict:
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DuplicateKeyError(f"Duplicate key {key!r} in YAML mapping")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def load_yaml_strict(path: Path) -> dict:
    with Path(path).open() as f:
        return yaml.load(f, Loader=_StrictLoader)
