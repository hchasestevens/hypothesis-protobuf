"""Conversion of protobuf modules to hypothesis strategies via internal representation."""

from __future__ import absolute_import, division, print_function, unicode_literals

from functools import partial

from hypothesis import strategies as st

from google.protobuf.internal.well_known_types import FieldDescriptor


RANGE32 = dict(max_value=2 ** 31 - 1, min_value=-(2 ** 31) + 1)
RANGE64 = dict(max_value=2 ** 63 - 1, min_value=-(2 ** 63) + 1)
URANGE32 = dict(min_value=0, max_value=2 ** 32 - 1)
URANGE64 = dict(min_value=0, max_value=2 ** 64 - 1)

SCALAR_MAPPINGS = {
    FieldDescriptor.TYPE_DOUBLE: st.floats(),
    FieldDescriptor.TYPE_FLOAT: st.floats(),
    FieldDescriptor.TYPE_INT32: st.integers(**RANGE32),
    FieldDescriptor.TYPE_INT64: st.integers(**RANGE64),
    FieldDescriptor.TYPE_UINT32: st.integers(**URANGE32),
    FieldDescriptor.TYPE_UINT64: st.integers(**URANGE64),
    FieldDescriptor.TYPE_SINT32: st.integers(**RANGE32),
    FieldDescriptor.TYPE_SINT64: st.integers(**RANGE64),
    FieldDescriptor.TYPE_FIXED32: st.integers(**URANGE32),
    FieldDescriptor.TYPE_FIXED64: st.integers(**URANGE64),
    FieldDescriptor.TYPE_SFIXED32: st.integers(**URANGE32),
    FieldDescriptor.TYPE_SFIXED64: st.integers(**URANGE64),
    FieldDescriptor.TYPE_BOOL: st.booleans(),
    FieldDescriptor.TYPE_STRING: st.text(),
    FieldDescriptor.TYPE_BYTES: st.binary()
}

LABEL_MAPPINGS = {
    FieldDescriptor.LABEL_OPTIONAL: partial(st.one_of, st.none()),  # N.B. NoneType is not a valid proto value, but is handled in buildable
    FieldDescriptor.LABEL_REPEATED: st.lists,
    FieldDescriptor.LABEL_REQUIRED: lambda x: x
}


def overridable(f):
    """
    Handle overrides in a strategy-generating function, taking a field as a
    first argument.

    Overrides can be strategies themselves or functions from strategies to
    strategies. In the latter case, the override will be passed the originally
    generated strategy from the decorated function.
    """
    def wrapper(*args, **kwargs):
        overrides = kwargs.get('overrides')
        if not overrides:
            return f(*args)

        field = args[0]
        field_name = getattr(field, 'DESCRIPTOR', field).full_name

        overridden_strategy = overrides.get(field_name)
        if not overridden_strategy:
            return f(*args)

        if not callable(overridden_strategy):
            return overridden_strategy

        return overridden_strategy(f(*args))
    return wrapper


@overridable
def enum_to_strategy(enum):
    """Generate strategy for enum."""
    return st.sampled_from([
        value.number
        for value in enum.DESCRIPTOR.values
    ])


def find_strategy_in_env(descriptor, env):
    """Find strategy matching descriptor."""
    for proto_cls, strategy in env.items():
        if proto_cls.DESCRIPTOR.full_name == descriptor.full_name:
            return strategy
    raise LookupError("Did not exist in env.")


def apply_modifier(strategy, field):
    """Apply labeled modifier to strategy."""
    return LABEL_MAPPINGS.get(field.label)(strategy)


def non_null(x):
    return x is not None


@overridable
def field_to_strategy(field, env):
    """Generate strategy for field."""
    if SCALAR_MAPPINGS.get(field.type) is not None:
        return apply_modifier(
            strategy=SCALAR_MAPPINGS[field.type],
            field=field
        )

    if field.type is FieldDescriptor.TYPE_ENUM:
        return apply_modifier(
            strategy=find_strategy_in_env(field.enum_type, env),
            field=field
        )

    if field.type is FieldDescriptor.TYPE_MESSAGE:
        field_options = field.message_type.GetOptions()

        if field_options.deprecated:
            return st.none()

        if field_options.map_entry:
            k, v = field.message_type.fields
            return st.dictionaries(
                field_to_strategy(k, env).filter(non_null),
                field_to_strategy(v, env).filter(non_null)
            )

        return apply_modifier(
            strategy=find_strategy_in_env(field.message_type, env),
            field=field
        )

    raise Exception("Unhandled field {}.".format(field))


def buildable(message_obj):
    """Return a "buildable" callable for st.builds which will handle optionals."""
    def builder(**kwargs):
        return message_obj(**{
            k: v
            for k, v in kwargs.items()
            if v is not None  # filter out unpopulated optional param
        })
    builder.__name__ = message_obj.DESCRIPTOR.full_name
    return builder


def message_to_strategy(message_obj, env, overrides=None):
    """Generate strategy from message."""
    # TODO: nested enums are not supported
    # TODO: nested messages are not supported

    return st.builds(
        buildable(message_obj),
        **{
            field_name: field_to_strategy(field, env, overrides=overrides)
            for field_name, field in message_obj.DESCRIPTOR.fields_by_name.items()
        }
    )


def load_module_into_env(module_, env, overrides=None):
    """Populate env with all messages and enums from the module."""
    for enum in module_.DESCRIPTOR.enum_types_by_name.values():
        enum_obj = getattr(module_, enum.name)
        env[enum_obj] = enum_to_strategy(enum_obj, overrides=overrides)

    # Some message types are dependant on other messages being loaded
    # Unfortunately, how to determine load order is not clear.
    # We'll loop through all the messages, skipping over errors until we've either:
    # A) loaded all the messages
    # B) exhausted all the possible orderings
    message_types = module_.DESCRIPTOR.message_types_by_name.values()
    total_messages = len(message_types)
    loaded = set()
    for __ in range(total_messages):
        for message in message_types:
            if message in loaded:
                continue
            try:
                message_obj = getattr(module_, message.name)
                env[message_obj] = message_to_strategy(message_obj, env, overrides=overrides)
                loaded.add(message)
            except LookupError:
                continue

        if all(message in loaded for message in message_types):
            break


def modules_to_strategies(*modules, **overrides):
    """
    Map protobuf classes from all supplied modules to hypothesis strategies.

    If overrides are provided as strategies, these are used in place of the
    fields or enums they are mapped to. If they are provided as callables of
    type Callable[[Strategy], Strategy], they will be passed the originally
    generated strategy for the field they are mapped to.
    """
    env = {}
    loaded_packages = set()
    modules_to_load = sorted(modules, key=lambda m: len(m.DESCRIPTOR.dependencies))
    while len(loaded_packages) != len(modules_to_load):
        for module_ in modules_to_load:
            if module_.DESCRIPTOR.package in loaded_packages:
                continue
            if not all(dependency.package in loaded_packages for dependency in module_.DESCRIPTOR.dependencies):
                continue
            load_module_into_env(module_, env, overrides)
            loaded_packages.add(module_.DESCRIPTOR.package)
    return env
