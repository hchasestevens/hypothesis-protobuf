"""Generic utilities."""

from __future__ import absolute_import, division, print_function, unicode_literals

from hypothesis import strategies as st


__all__ = ('full_field_name', 'optional')


def get_field(proto_cls, field_name):
    """Return proto field from class and field name."""
    return proto_cls.DESCRIPTOR.fields_by_name[field_name]


def full_field_name(proto_cls, field_name):
    """Get canonical name for field of class."""
    return get_field(proto_cls, field_name).full_name


def optional(strategy):
    """Return an optional version of the supplied strategy."""
    return st.one_of(st.none(), strategy)
