# Copyright 2019 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=protected-access
r"""
Measurements
============

**Module name:** :mod:`pennylane.measure`

.. currentmodule:: pennylane.measure

This module contains the functions for computing expectation values,
variances, and measurement samples of quantum observables.

These are used to indicate to the quantum device how to measure
and return the requested observables. For example, the following
QNode returns the expectation value of observable :class:`~.PauliZ`
on wire 1, and the variance of observable :class:`~.PauliX` on
wire 2.

.. code-block:: python

    import pennylane as qml
    from pennylane import expval, var

    dev = qml.device('default.qubit', wires=2)

    @qml.qnode(dev)
    def circuit(x, y):
        qml.RX(x, wires=0)
        qml.CNOT(wires=[0,1])
        qml.RY(y, wires=1)
        return expval(qml.PauliZ(0)), var(qml.PauliX(1))

Note that *all* returned observables must be within
a measurement function; they cannot be 'bare'.

Summary
^^^^^^^

.. autosummary::
   expval
   var
   sample

Code details
^^^^^^^^^^^^
"""
from .qnode import QNode, QuantumFunctionError
from .operation import Observable, Sample, Variance, Expectation, Tensor


def expval(op):
    r"""Expectation value of the supplied observable.

    Args:
        op (Observable): a quantum observable object
    """
    if not isinstance(op, Observable):
        raise QuantumFunctionError(
            "{} is not an observable: cannot be used with expval".format(op.name)
        )

    if QNode._current_context is not None:
        # delete operations from QNode queue
        if isinstance(op, Tensor):
            for o in op.obs:
                QNode._current_context.queue.remove(o)
        else:
            QNode._current_context.queue.remove(op)

    # set return type to be an expectation value
    op.return_type = Expectation

    if QNode._current_context is not None:
        # add observable to QNode observable queue
        QNode._current_context._append_op(op)

    return op


def var(op):
    r"""Variance of the supplied observable.

    Args:
        op (Observable): a quantum observable object
    """
    if not isinstance(op, Observable):
        raise QuantumFunctionError(
            "{} is not an observable: cannot be used with var".format(op.name)
        )

    if QNode._current_context is not None:
        # delete operations from QNode queue
        if isinstance(op, Tensor):
            for o in op.obs:
                QNode._current_context.queue.remove(o)
        else:
            QNode._current_context.queue.remove(op)

    # set return type to be a variance
    op.return_type = Variance

    if QNode._current_context is not None:
        # add observable to QNode observable queue
        QNode._current_context._append_op(op)

    return op


def sample(op):
    r"""Sample from the supplied observable, with the number of shots
    determined from the ``dev.shots`` attribute of the corresponding device.

    Args:
        op (Observable): a quantum observable object
    """
    if not isinstance(op, Observable):
        raise QuantumFunctionError(
            "{} is not an observable: cannot be used with sample".format(op.name)
        )

    if QNode._current_context is not None:
        # delete operations from QNode queue
        if isinstance(op, Tensor):
            for o in op.obs:
                QNode._current_context.queue.remove(o)
        else:
            QNode._current_context.queue.remove(op)

    # set return type to be a sample
    op.return_type = Sample

    if QNode._current_context is not None:
        # add observable to QNode observable queue
        QNode._current_context._append_op(op)

    return op