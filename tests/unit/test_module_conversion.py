"""Tests for hypothesis_protobuf/module_conversion.py"""

from __future__ import absolute_import, unicode_literals

from numbers import Number

from past.builtins import basestring
from hypothesis import strategies as st

from .test_schemas import im_pb2

from hypothesis_protobuf.module_conversion import modules_to_strategies
from hypothesis_protobuf.utils import full_field_name


def test_instant_message_example():
    """Ensure InstantMessage can be made into a strategy with the correct types."""
    protobuf_strategies = modules_to_strategies(im_pb2)
    instant_message_strategy = protobuf_strategies[im_pb2.InstantMessage]
    instant_message_example = instant_message_strategy.example()
    assert isinstance(instant_message_example.timestamp, Number)
    assert isinstance(instant_message_example.sender.screen_name, basestring)
    assert isinstance(instant_message_example.recipient.screen_name, basestring)
    assert isinstance(instant_message_example.message, basestring)
    assert isinstance(instant_message_example.metadata.latency, float)
    assert isinstance(instant_message_example.metadata.inner.a, float)
    assert isinstance(instant_message_example.metadata.inner.layer.client.name, basestring)
    assert isinstance(instant_message_example.metadata.inner.layer.status, Number)
    assert isinstance(instant_message_example.client, Number)


def test_overrides_respected():
    """Ensure provided overrides are respected."""
    protobuf_strategies = modules_to_strategies(im_pb2, **{
        full_field_name(im_pb2.InstantMessage, 'message'): st.just('test message')
    })
    instant_message_strategy = protobuf_strategies[im_pb2.InstantMessage]
    instant_message_example = instant_message_strategy.example()
    assert instant_message_example.message == 'test message'
