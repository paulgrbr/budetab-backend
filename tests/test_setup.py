import sys
import os
import pytest
# Pfad zum src-Ordner hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import *

def test_answer():
    assert add(3) == 6