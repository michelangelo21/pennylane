# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unit tests for the :mod:`grouping` utility functions in ``groups/pauli_utils.py``.
"""
import pytest
import numpy as np
from pennylane import Identity, PauliX, PauliY, PauliZ, Hadamard, Hermitian, U3
from pennylane.operation import Tensor

from pennylane.groups.pauli_utils import (
    is_pauli_word,
    are_identical_pauli_words,
    is_commuting,
    pauli_to_binary,
    binary_to_pauli,
    pauli_word_to_matrix,
    pauli_word_to_string,
    string_to_pauli_word,
)


non_pauli_words = [
    PauliX(0) @ Hadamard(1) @ Identity(2),
    Hadamard("a"),
    U3(0.1, 1, 1, wires="a"),
    Hermitian(np.array([[3.2, 1.1 + 0.6j], [1.1 - 0.6j, 3.2]]), wires="a") @ PauliX("b"),
]


class TestPauliUtils:
    """Basic usage and edge-case tests for the measurement optimization utility functions."""

    ops_to_vecs_explicit_wires = [
        (PauliX(0) @ PauliY(1) @ PauliZ(2), np.array([1, 1, 0, 0, 1, 1])),
        (PauliZ(0) @ PauliY(2), np.array([0, 1, 1, 1])),
        (PauliY(1) @ PauliX(2), np.array([1, 1, 1, 0])),
        (Identity(0), np.zeros(2)),
    ]

    @pytest.mark.parametrize("op,vec", ops_to_vecs_explicit_wires)
    def test_pauli_to_binary_no_wire_map(self, op, vec):
        """Test conversion of Pauli word from operator to binary vector representation when no
        ``wire_map`` is specified."""

        assert (pauli_to_binary(op) == vec).all()

    ops_to_vecs_abstract_wires = [
        (PauliX("a") @ PauliZ("b") @ Identity("c"), np.array([1, 0, 0, 0, 0, 1, 0, 0])),
        (PauliY(6) @ PauliZ("a") @ PauliZ("b"), np.array([0, 0, 0, 1, 1, 1, 0, 1])),
        (PauliX("b") @ PauliY("c"), np.array([0, 1, 1, 0, 0, 0, 1, 0])),
        (Identity("a") @ Identity(6), np.zeros(8)),
    ]

    @pytest.mark.parametrize("op,vec", ops_to_vecs_abstract_wires)
    def test_pauli_to_binary_with_wire_map(self, op, vec):
        """Test conversion of Pauli word from operator to binary vector representation if a
        ``wire_map`` is specified."""

        wire_map = {"a": 0, "b": 1, "c": 2, 6: 3}

        assert (pauli_to_binary(op, wire_map=wire_map) == vec).all()

    vecs_to_ops_explicit_wires = [
        (np.array([1, 0, 1, 0, 0, 1]), PauliX(0) @ PauliY(2)),
        (np.array([1, 1, 1, 1, 1, 1]), PauliY(0) @ PauliY(1) @ PauliY(2)),
        (np.array([1, 0, 1, 0, 1, 1]), PauliX(0) @ PauliZ(1) @ PauliY(2)),
        (np.zeros(6), Identity(0)),
    ]

    @pytest.mark.parametrize("non_pauli_word", non_pauli_words)
    def test_pauli_to_binary_non_pauli_word_catch(self, non_pauli_word):
        """Tests TypeError raise for when non Pauli-word Pennylane operations/operators are given
        as input to pauli_to_binary."""

        assert pytest.raises(TypeError, pauli_to_binary, non_pauli_word)

    def test_pauli_to_binary_incompatable_wire_map_n_qubits(self):
        """Tests ValueError raise when n_qubits is not high enough to support the highest wire_map
        value."""

        pauli_word = PauliX("a") @ PauliY("b") @ PauliZ("c")
        wire_map = {"a": 0, "b": 1, "c": 3}
        n_qubits = 3
        assert pytest.raises(ValueError, pauli_to_binary, pauli_word, n_qubits, wire_map)

    @pytest.mark.parametrize("vec,op", vecs_to_ops_explicit_wires)
    def test_binary_to_pauli_no_wire_map(self, vec, op):
        """Test conversion of Pauli in binary vector representation to operator form when no
        ``wire_map`` is specified."""

        assert are_identical_pauli_words(binary_to_pauli(vec), op)

    vecs_to_ops_abstract_wires = [
        (np.array([1, 0, 1, 0, 0, 1]), PauliX("alice") @ PauliY("ancilla")),
        (np.array([1, 1, 1, 1, 1, 1]), PauliY("alice") @ PauliY("bob") @ PauliY("ancilla")),
        (np.array([1, 0, 1, 0, 1, 0]), PauliX("alice") @ PauliZ("bob") @ PauliX("ancilla")),
        (np.zeros(6), Identity("alice")),
    ]

    @pytest.mark.parametrize("vec,op", vecs_to_ops_abstract_wires)
    def test_binary_to_pauli_with_wire_map(self, vec, op):
        """Test conversion of Pauli in binary vector representation to operator form when
        ``wire_map`` is specified."""

        wire_map = {"alice": 0, "bob": 1, "ancilla": 2}

        assert are_identical_pauli_words(binary_to_pauli(vec, wire_map=wire_map), op)

    binary_vecs_with_invalid_wire_maps = [
        ([1, 0], {"a": 1}),
        ([1, 1, 1, 0], {"a": 0}),
        ([1, 0, 1, 0, 1, 1], {"a": 0, "b": 2, "c": 3}),
        ([1, 0, 1, 0], {"a": 0, "b": 2}),
    ]

    @pytest.mark.parametrize("binary_vec,wire_map", binary_vecs_with_invalid_wire_maps)
    def test_binary_to_pauli_invalid_wire_map(self, binary_vec, wire_map):
        """Tests ValueError raise when wire_map values are not integers 0 to N, for input 2N
        dimensional binary vector."""

        assert pytest.raises(ValueError, binary_to_pauli, binary_vec, wire_map)

    not_binary_symplectic_vecs = [[1, 0, 1, 1, 0], [1], [2, 0, 0, 1], [0.1, 4.3, 2.0, 1.3]]

    @pytest.mark.parametrize("not_binary_symplectic", not_binary_symplectic_vecs)
    def test_binary_to_pauli_with_illegal_vectors(self, not_binary_symplectic):
        """Test ValueError raise for when non even-dimensional binary vectors are given to
        binary_to_pauli."""

        assert pytest.raises(ValueError, binary_to_pauli, not_binary_symplectic)

    def test_is_pauli_word(self):
        """Test for determining whether input ``Observable`` instance is a Pauli word."""

        observable_1 = PauliX(0)
        observable_2 = PauliZ(1) @ PauliX(2) @ PauliZ(4)
        observable_3 = PauliX(1) @ Hadamard(4)
        observable_4 = Hadamard(0)

        assert is_pauli_word(observable_1)
        assert is_pauli_word(observable_2)
        assert not is_pauli_word(observable_3)
        assert not is_pauli_word(observable_4)

    def test_are_identical_pauli_words(self):
        """Tests for determining if two Pauli words have the same ``wires`` and ``name`` attributes."""

        pauli_word_1 = Tensor(PauliX(0))
        pauli_word_2 = PauliX(0)

        assert are_identical_pauli_words(pauli_word_1, pauli_word_2)
        assert are_identical_pauli_words(pauli_word_2, pauli_word_1)

        pauli_word_1 = PauliX(0) @ PauliY(1)
        pauli_word_2 = PauliY(1) @ PauliX(0)
        pauli_word_3 = Tensor(PauliX(0), PauliY(1))
        pauli_word_4 = PauliX(1) @ PauliZ(2)

        assert are_identical_pauli_words(pauli_word_1, pauli_word_2)
        assert are_identical_pauli_words(pauli_word_1, pauli_word_3)
        assert not are_identical_pauli_words(pauli_word_1, pauli_word_4)
        assert not are_identical_pauli_words(pauli_word_3, pauli_word_4)

    @pytest.mark.parametrize("non_pauli_word", non_pauli_words)
    def test_are_identical_pauli_words_non_pauli_word_catch(self, non_pauli_word):
        """Tests TypeError raise for when non-Pauli word Pennylane operators/operations are given
        as input to are_identical_pauli_words."""

        with pytest.raises(TypeError):
            are_identical_pauli_words(non_pauli_word, PauliZ(0) @ PauliZ(1))

        with pytest.raises(TypeError):
            are_identical_pauli_words(non_pauli_word, PauliZ(0) @ PauliZ(1))

        with pytest.raises(TypeError):
            are_identical_pauli_words(PauliX("a") @ Identity("b"), non_pauli_word)

        with pytest.raises(TypeError):
            are_identical_pauli_words(non_pauli_word, non_pauli_word)

    @pytest.mark.parametrize(
        "pauli_word,wire_map,expected_string",
        [
            (PauliX(0), {0: 0}, "X"),
            (Identity(0), {0: 0}, "I"),
            (PauliZ(0) @ PauliY(1), {0: 0, 1: 1}, "ZY"),
            (PauliX(1), {0: 0, 1: 1}, "IX"),
            (PauliX(1), None, "X"),
            (PauliX(1), {1: 0, 0: 1}, "XI"),
            (PauliZ("a") @ PauliY("b") @ PauliZ("d"), {"a": 0, "b": 1, "c": 2, "d": 3}, "ZYIZ"),
            (PauliZ("a") @ PauliY("b") @ PauliZ("d"), None, "ZYZ"),
        ],
    )
    def test_pauli_word_to_string(self, pauli_word, wire_map, expected_string):
        """Test that Pauli words are correctly converted into strings."""
        obtained_string = pauli_word_to_string(pauli_word, wire_map)
        assert obtained_string == expected_string

    @pytest.mark.parametrize(
        "pauli_string,wire_map,expected_pauli",
        [
            ("I", {"a": 0}, Identity("a")),
            ("X", {0: 0}, PauliX(0)),
            ("II", {0: 0, 1: 1}, Identity(0)),
            ("ZYIZ", {"a": 0, "b": 1, "c": 2, "d": 3}, PauliZ("a") @ PauliY("b") @ PauliZ("d")),
            ("ZYZ", None, PauliZ(0) @ PauliY(1) @ PauliZ(2)),
        ],
    )
    def test_string_to_pauli_word(self, pauli_string, wire_map, expected_pauli):
        """Test that Pauli words are correctly converted into strings."""
        obtained_pauli = string_to_pauli_word(pauli_string, wire_map)
        assert obtained_pauli.compare(expected_pauli)

    @pytest.mark.parametrize(
        "pauli_word,wire_map,expected_matrix",
        [
            (PauliX(0), {0: 0}, PauliX.matrix),
            (Identity(0), {0: 0}, np.eye(2)),
            (
                PauliZ(0) @ PauliY(1),
                {0: 0, 1: 1},
                np.array([[0, -1j, 0, 0], [1j, 0, 0, 0], [0, 0, 0, 1j], [0, 0, -1j, 0]]),
            ),
            (Identity(0), {0: 0, 1: 1}, np.eye(4)),
            (PauliX(2), None, PauliX.matrix),
            (
                PauliX(2),
                {0: 0, 1: 1, 2: 2},
                np.array(
                    [
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 1],
                        [0, 0, 0, 0, 0, 0, 1, 0],
                    ]
                ),
            ),
            (
                PauliZ("a") @ PauliX(2),
                {"a": 0, 1: 1, 2: 2},
                np.array(
                    [
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, -1, 0, 0],
                        [0, 0, 0, 0, -1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, -1],
                        [0, 0, 0, 0, 0, 0, -1, 0],
                    ]
                ),
            ),
            (
                PauliX(2) @ PauliZ("a"),
                {"a": 0, 1: 1, 2: 2},
                np.array(
                    [
                        [0, 1, 0, 0, 0, 0, 0, 0],
                        [1, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, -1, 0, 0],
                        [0, 0, 0, 0, -1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, -1],
                        [0, 0, 0, 0, 0, 0, -1, 0],
                    ]
                ),
            ),
        ],
    )
    def test_pauli_word_to_matrix(self, pauli_word, wire_map, expected_matrix):
        """Test that Pauli words are correctly converted into strings."""
        obtained_matrix = pauli_word_to_matrix(pauli_word, wire_map)
        assert np.allclose(obtained_matrix, expected_matrix)

    @pytest.mark.parametrize(
        "pauli_word_1,pauli_word_2,wire_map,commute_status",
        [
            (Identity(0), PauliZ(0), {0: 0}, True),
            (PauliY(0), PauliZ(0), {0: 0}, False),
            (PauliX(0), PauliX(1), {0: 0, 1: 1}, True),
            (PauliY("x"), PauliX("y"), None, True),
            (
                PauliZ("a") @ PauliY("b") @ PauliZ("d"),
                PauliX("a") @ PauliZ("c") @ PauliY("d"),
                {"a": 0, "b": 1, "c": 2, "d": 3},
                True,
            ),
            (
                PauliX("a") @ PauliY("b") @ PauliZ("d"),
                PauliX("a") @ PauliZ("c") @ PauliY("d"),
                {"a": 0, "b": 1, "c": 2, "d": 3},
                False,
            ),
        ],
    )
    def test_is_commuting(self, pauli_word_1, pauli_word_2, wire_map, commute_status):
        """Test that Pauli words are correctly converted into strings."""
        do_they_commute = is_commuting(pauli_word_1, pauli_word_2, wire_map=wire_map)
        assert do_they_commute == commute_status