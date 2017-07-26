# hypothesis-protobuf
[Hypothesis](http://hypothesis.works/) extension to allow generating [protobuf](https://developers.google.com/protocol-buffers/) messages matching a schema.

## Installation
```
pip install hypothesis-pb
```

## Usage
Given a compiled protobuf schema module, `hypothesis-protobuf` allows for hypothesis strategies to be generated which match the types of the protobuf messages.

### Simple example
Using an example protobuf schema for an instant messaging application:
```proto
syntax = "proto3";
package im;

enum Client {
  CLIENT_UNKNOWN = 0;
  CLIENT_NATIVE_APP = 1;
  CLIENT_WEB_APP = 2;
  CLIENT_API = 3;
}

message User {
  uint64 id = 1;
  string screen_name = 2;
}

message InstantMessage {
  uint64 timestamp = 1;
  Client client = 2;
  fixed32 sender_ip = 3;
  User sender = 4;
  User recipient = 5;
  string message = 6;
  repeated bytes image_attachments = 7;
}
```
a strategy for `InstantMessage` can be generated from the compiled schema (`im_pb2.py`) by executing:
```python
from hypothesis_protobuf import modules_to_strategies
import im_pb2

protobuf_strategies = modules_to_strategies(im_pb2)
instant_message_strategy = protobuf_strategies[im_pb2.InstantMessage]
```
which in turn can be used to generate `InstantMessage` examples:
```python
>>> instant_message_strategy.example()
timestamp: 14420265017158477352
client: CLIENT_NATIVE_APP
sender_ip: 1465109037
sender {
  id: 9509488734701077048
  screen_name: "\364\210\240\2233\007\352\212\222i\354\217\251"
}
recipient {
  id: 14863054719025962687
  screen_name: "\351\274\240"
}
message: "M\361\265\247\224\310\224\362\202\r\347\227\245\n\352\202M]\361\253\237\2700"
image_attachments: "\236rN\267\252\363-s\235"
image_attachments: "\256\376ZP-"
image_attachments: "\340"

```
or as a strategy for use in testing (see the [hypothesis quick-start guide](https://hypothesis.readthedocs.io/en/latest/quickstart.html)):
```python
from hypothesis import given

@given(instant_message=protobuf_strategies[im_pb2.InstantMessage])
def test_instant_message_processor(instant_message):
    assert process_message(instant_message)  # will be run using multiple InstantMessage examples
```

### Overriding strategies
When generating strategies for a given protobuf module, field-specific overrides can be provided. These overrides must be mappings from full field names to strategies, like so:
```python
from hypothesis_protobuf import modules_to_strategies
from hypothesis import strategies as st
import im_pb2

strategy_overrides = {
    'im.InstantMessage.timestamp': st.floats(
        min_value=0, 
        max_value=2e9
    )
}
protobuf_strategies = modules_to_strategies(im_pb2, **strategy_overrides)
instant_message_strategy = protobuf_strategies[im_pb2.InstantMessage]
```
`hypothesis-protobuf` also offers a `full_field_name` utility, allowing the above override to be specified as:
```python
from hypothesis_protobuf import full_field_name
from hypothesis import strategies as st
import im_pb2

strategy_overrides = {
    full_field_name(im_pb2.InstantMessage, 'timestamp'): st.floats(
        min_value=0,
        max_value=2e9
    )
}
```
In cases where the message strategy should choose either from the override provided or from the default field value, the `optional` function can be used:
```python
from hypothesis_protobuf import optional
from hypothesis import strategies as st

strategy_overrides = {
    'im.InstantMessage.timestamp': optional(
        st.floats(min_value=0, max_value=2e9)
    )
}
```
Finally, overrides can also be provided as functions, taking the field's default strategy and returning a new strategy. Using this method, the above can be rewritten as:
```python
strategy_overrides = {
    'im.InstantMessage.timestamp': (
        lambda strategy: strategy.filter(lambda value: value <= 2e9)
    )
}
```

### Known limitations
`hypothesis-protobuf` does not currently support message or enum definitions nested within other message definitions.

## License
`hypothesis-protobuf` is available under the MIT license.
