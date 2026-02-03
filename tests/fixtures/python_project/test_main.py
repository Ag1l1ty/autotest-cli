"""Tests for the main module — only covers add() so far."""

import pytest
from main import add


class TestAdd:
    """Tests for the add function."""

    def test_add_positive_numbers(self):
        assert add(2, 3) == 5

    def test_add_negative_numbers(self):
        assert add(-1, -4) == -5

    def test_add_mixed_signs(self):
        assert add(-2, 5) == 3

    def test_add_with_zero(self):
        assert add(0, 7) == 7
        assert add(7, 0) == 7

    def test_add_floats(self):
        result = add(0.1, 0.2)
        assert round(result, 10) == round(0.3, 10)
