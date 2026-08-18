from uplink_parse.decorators.field import field
from uplink_parse.decorators.fields import fields

class Test:

    @field
    def test1(self):
        ...

    @field
    def test2(self):
        ...
    @field
    def test3(self):
        ...

    @fields
    def test4(self):
        ...

print(fields.get_registered(Test))