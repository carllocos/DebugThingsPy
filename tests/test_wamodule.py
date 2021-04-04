import os
import pytest


from web_assembly import WAModule

@pytest.fixture
def file_name():
    return 'wat_examples/fac.wat'

def test_load(file_name):
    mod = WAModule.from_file(file_name)
    assert true
