# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


"""Tests for Stabilizerstate quantum state class."""

from itertools import product
import random
import time
import unittest
import logging
from ddt import ddt, data, unpack

import numpy as np

from qiskit import QuantumCircuit

from qiskit.quantum_info.random import random_clifford, random_pauli
from qiskit.quantum_info.states import StabilizerState, Statevector
from qiskit.circuit.library import IGate, XGate, HGate
from qiskit.quantum_info.operators import Clifford, Pauli, Operator
from test import combine  # pylint: disable=wrong-import-order
from test import QiskitTestCase  # pylint: disable=wrong-import-order


logger = logging.getLogger(__name__)


@ddt
class TestStabilizerState(QiskitTestCase):
    """Tests for StabilizerState class."""

    rng = np.random.default_rng(12345)
    samples = 10
    shots = 1000
    threshold = 0.1 * shots

    #Allowed percent head room when checking performance
    #of probability calculations with targets vs without target
    performance_varability_percent: float = 0.01

    @staticmethod
    def probability_percent_of_calculated_branches(number_of_calculated_branches: int, num_of_qubits: int) -> float:
        return (number_of_calculated_branches / ((2**(num_of_qubits+1))-1))

    @combine(num_qubits=[2, 3, 4, 5])
    def test_init_clifford(self, num_qubits):
        """Test initialization from Clifford."""
        stab1 = StabilizerState(random_clifford(num_qubits, seed=self.rng))
        stab2 = StabilizerState(stab1)
        self.assertEqual(stab1, stab2)

    @combine(num_qubits=[2, 3, 4, 5])
    def test_init_circuit(self, num_qubits):
        """Test initialization from a Clifford circuit."""
        cliff = random_clifford(num_qubits, seed=self.rng)
        stab1 = StabilizerState(cliff.to_circuit())
        stab2 = StabilizerState(cliff)
        self.assertEqual(stab1, stab2)

    @combine(num_qubits=[2, 3, 4, 5])
    def test_init_instruction(self, num_qubits):
        """Test initialization from a Clifford instruction."""
        cliff = random_clifford(num_qubits, seed=self.rng)
        stab1 = StabilizerState(cliff.to_instruction())
        stab2 = StabilizerState(cliff)
        self.assertEqual(stab1, stab2)

    @combine(num_qubits=[2, 3, 4, 5])
    def test_init_pauli(self, num_qubits):
        """Test initialization from pauli."""
        pauli = random_pauli(num_qubits, seed=self.rng)
        stab1 = StabilizerState(pauli)
        stab2 = StabilizerState(stab1)
        self.assertEqual(stab1, stab2)

    @combine(num_qubits=[2, 3, 4, 5])
    def test_to_operator(self, num_qubits):
        """Test to_operator method for returning projector."""
        for _ in range(self.samples):
            stab = StabilizerState(random_clifford(num_qubits, seed=self.rng))
            target = Operator(stab)
            op = StabilizerState(stab).to_operator()
            self.assertEqual(op, target)

    @combine(num_qubits=[2, 3, 4])
    def test_trace(self, num_qubits):
        """Test trace methods"""
        stab = StabilizerState(random_clifford(num_qubits, seed=self.rng))
        trace = stab.trace()
        self.assertEqual(trace, 1.0)

    @combine(num_qubits=[2, 3, 4])
    def test_purity(self, num_qubits):
        """Test purity methods"""
        stab = StabilizerState(random_clifford(num_qubits, seed=self.rng))
        purity = stab.purity()
        self.assertEqual(purity, 1.0)

    @combine(num_qubits=[2, 3])
    def test_conjugate(self, num_qubits):
        """Test conjugate method."""
        for _ in range(self.samples):
            cliff = random_clifford(num_qubits, seed=self.rng)
            target = StabilizerState(cliff.conjugate())
            state = StabilizerState(cliff).conjugate()
            self.assertEqual(state, target)

    def test_tensor(self):
        """Test tensor method."""
        for _ in range(self.samples):
            cliff1 = random_clifford(2, seed=self.rng)
            cliff2 = random_clifford(3, seed=self.rng)
            stab1 = StabilizerState(cliff1)
            stab2 = StabilizerState(cliff2)
            target = StabilizerState(cliff1.tensor(cliff2))
            state = stab1.tensor(stab2)
            self.assertEqual(state, target)

    def test_expand(self):
        """Test expand method."""
        for _ in range(self.samples):
            cliff1 = random_clifford(2, seed=self.rng)
            cliff2 = random_clifford(3, seed=self.rng)
            stab1 = StabilizerState(cliff1)
            stab2 = StabilizerState(cliff2)
            target = StabilizerState(cliff1.expand(cliff2))
            state = stab1.expand(stab2)
            self.assertEqual(state, target)

    @combine(num_qubits=[2, 3, 4])
    def test_evolve(self, num_qubits):
        """Test evolve method."""
        for _ in range(self.samples):
            cliff1 = random_clifford(num_qubits, seed=self.rng)
            cliff2 = random_clifford(num_qubits, seed=self.rng)
            stab1 = StabilizerState(cliff1)
            stab2 = StabilizerState(cliff2)
            target = StabilizerState(cliff1.compose(cliff2))
            state = stab1.evolve(stab2)
            self.assertEqual(state, target)

    @combine(num_qubits_1=[4, 5, 6], num_qubits_2=[1, 2, 3])
    def test_evolve_subsystem(self, num_qubits_1, num_qubits_2):
        """Test subsystem evolve method."""
        for _ in range(self.samples):
            cliff1 = random_clifford(num_qubits_1, seed=self.rng)
            cliff2 = random_clifford(num_qubits_2, seed=self.rng)
            stab1 = StabilizerState(cliff1)
            stab2 = StabilizerState(cliff2)
            qargs = sorted(np.random.choice(range(num_qubits_1), num_qubits_2, replace=False))
            target = StabilizerState(cliff1.compose(cliff2, qargs))
            state = stab1.evolve(stab2, qargs)
            self.assertEqual(state, target)

    def test_measure_single_qubit(self):
        """Test a measurement of a single qubit"""
        for _ in range(self.samples):
            cliff = Clifford(XGate())
            stab = StabilizerState(cliff)
            value = stab.measure()[0]
            self.assertEqual(value, "1")

            cliff = Clifford(IGate())
            stab = StabilizerState(cliff)
            value = stab.measure()[0]
            self.assertEqual(value, "0")

            cliff = Clifford(HGate())
            stab = StabilizerState(cliff)
            value = stab.measure()[0]
            self.assertIn(value, ["0", "1"])

    def test_measure_qubits(self):
        """Test a measurement of a subsystem of qubits"""

        for _ in range(self.samples):
            num_qubits = 4
            qc = QuantumCircuit(num_qubits)
            stab = StabilizerState(qc)
            value = stab.measure()[0]
            self.assertEqual(value, "0000")
            value = stab.measure([0, 2])[0]
            self.assertEqual(value, "00")
            value = stab.measure([1])[0]
            self.assertEqual(value, "0")

            for i in range(num_qubits):
                qc.x(i)
            stab = StabilizerState(qc)
            value = stab.measure()[0]
            self.assertEqual(value, "1111")
            value = stab.measure([2, 0])[0]
            self.assertEqual(value, "11")
            value = stab.measure([1])[0]
            self.assertEqual(value, "1")

            qc = QuantumCircuit(num_qubits)
            qc.h(0)
            stab = StabilizerState(qc)
            value = stab.measure()[0]
            self.assertIn(value, ["0000", "0001"])
            value = stab.measure([0, 1])[0]
            self.assertIn(value, ["00", "01"])
            value = stab.measure([2])[0]
            self.assertEqual(value, "0")

            qc = QuantumCircuit(num_qubits)
            qc.h(0)
            qc.cx(0, 1)
            qc.cx(0, 2)
            qc.cx(0, 3)
            stab = StabilizerState(qc)
            value = stab.measure()[0]
            self.assertIn(value, ["0000", "1111"])
            value = stab.measure([3, 1])[0]
            self.assertIn(value, ["00", "11"])
            value = stab.measure([2])[0]
            self.assertIn(value, ["0", "1"])

    def test_reset_single_qubit(self):
        """Test reset method of a single qubit"""

        empty_qc = QuantumCircuit(1)

        for _ in range(self.samples):
            cliff = Clifford(XGate())
            stab = StabilizerState(cliff)
            value = stab.reset([0])
            target = StabilizerState(empty_qc)
            self.assertEqual(value, target)

            cliff = Clifford(HGate())
            stab = StabilizerState(cliff)
            value = stab.reset([0])
            target = StabilizerState(empty_qc)
            self.assertEqual(value, target)

    def test_reset_qubits(self):
        """Test reset method of a subsystem of qubits"""

        num_qubits = 3
        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)

        for _ in range(self.samples):
            with self.subTest(msg="reset (None)"):
                stab = StabilizerState(qc)
                res = stab.reset()
                value = res.measure()[0]
                self.assertEqual(value, "000")

        for _ in range(self.samples):
            for qargs in [[0, 1, 2], [2, 1, 0], [1, 2, 0], [1, 0, 2]]:
                with self.subTest(msg=f"reset (qargs={qargs})"):
                    stab = StabilizerState(qc)
                    res = stab.reset(qargs)
                    value = res.measure()[0]
                    self.assertEqual(value, "000")

        for _ in range(self.samples):
            with self.subTest(msg="reset ([0])"):
                stab = StabilizerState(qc)
                res = stab.reset([0])
                value = res.measure()[0]
                self.assertIn(value, ["000", "110"])

        for _ in range(self.samples):
            with self.subTest(msg="reset ([1])"):
                stab = StabilizerState(qc)
                res = stab.reset([1])
                value = res.measure()[0]
                self.assertIn(value, ["000", "101"])

        for _ in range(self.samples):
            with self.subTest(msg="reset ([2])"):
                stab = StabilizerState(qc)
                res = stab.reset([2])
                value = res.measure()[0]
                self.assertIn(value, ["000", "011"])

        for _ in range(self.samples):
            for qargs in [[0, 1], [1, 0]]:
                with self.subTest(msg=f"reset (qargs={qargs})"):
                    stab = StabilizerState(qc)
                    res = stab.reset(qargs)
                    value = res.measure()[0]
                    self.assertIn(value, ["000", "100"])

        for _ in range(self.samples):
            for qargs in [[0, 2], [2, 0]]:
                with self.subTest(msg=f"reset (qargs={qargs})"):
                    stab = StabilizerState(qc)
                    res = stab.reset(qargs)
                    value = res.measure()[0]
                    self.assertIn(value, ["000", "010"])

        for _ in range(self.samples):
            for qargs in [[1, 2], [2, 1]]:
                with self.subTest(msg=f"reset (qargs={qargs})"):
                    stab = StabilizerState(qc)
                    res = stab.reset(qargs)
                    value = res.measure()[0]
                    self.assertIn(value, ["000", "001"])

    def test_probabilities_dict_single_qubit(self):
        """Test probabilities and probabilities_dict methods of a single qubit"""

        num_qubits = 1
        qc = QuantumCircuit(num_qubits)

        for _ in range(self.samples):
            with self.subTest(msg="P(id(0))"):
                stab = StabilizerState(qc)
                value = stab.probabilities_dict()
                target = {"0": 1}
                self.assertEqual(value, target)

                input_target: str = '0'
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"0": 1}
                self.assertEqual(value, target)
                
                #Check probability of target with 0 probability only 
                input_target: str = '1'
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"1": 0}
                self.assertEqual(value, target)

                probs = stab.probabilities()
                target = np.array([1, 0])
                self.assertTrue(np.allclose(probs, target))

        qc.x(0)
        for _ in range(self.samples):
            with self.subTest(msg="P(x(0))"):
                stab = StabilizerState(qc)
                value = stab.probabilities_dict()
                target = {"1": 1}
                self.assertEqual(value, target)

                input_target: str = '1'
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"1": 1}
                self.assertEqual(value, target)
                
                input_target: str = '0'
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"0": 0}
                self.assertEqual(value, target)
                
                probs = stab.probabilities()
                target = np.array([0, 1])
                self.assertTrue(np.allclose(probs, target))

        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        for _ in range(self.samples):
            with self.subTest(msg="P(h(0))"):
                stab = StabilizerState(qc)
                value = stab.probabilities_dict()
                target = {"0": 0.5, "1": 0.5}
                self.assertEqual(value, target)

                input_target: list = ['0', '1'] 
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"0": 0.5, "1": 0.5}
                self.assertEqual(value, target)

                input_target: list = ['1'] 
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"1": 0.5}
                self.assertEqual(value, target)

                input_target: list = ['0'] 
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"0": 0.5}
                self.assertEqual(value, target)
                probs = stab.probabilities()
                target = np.array([0.5, 0.5])
                self.assertTrue(np.allclose(probs, target))

    def test_probabilities_dict_two_qubits(self):
        """Test probabilities and probabilities_dict methods of two qubits"""

        num_qubits = 2
        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        stab = StabilizerState(qc)

        for _ in range(self.samples):
            with self.subTest(msg="P(None)"):
                value = stab.probabilities_dict()
                target = {"00": 0.5, "01": 0.5}
                self.assertEqual(value, target)

                input_target: list[str] = ['00']
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"00": 0.5}
                self.assertEqual(value, target)

                input_target: list[str] = ['01']
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"01": 0.5}
                self.assertEqual(value, target)

                #Verify probability for a target that will return back 0
                input_target: list[str] = ['10']
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"10": 0}
                self.assertEqual(value, target)

                #Verify probability for a target that will return back 0
                input_target: list[str] = ['11']
                value = stab.probabilities_dict_from_bitstrings(target=input_target)
                target = {"11": 0}
                self.assertEqual(value, target)

                probs = stab.probabilities()
                target = np.array([0.5, 0.5, 0, 0])
                self.assertTrue(np.allclose(probs, target))

        for _ in range(self.samples):
            with self.subTest(msg="P([0, 1])"):
                value = stab.probabilities_dict([0, 1])
                target = {"00": 0.5, "01": 0.5}
                self.assertEqual(value, target)
                probs = stab.probabilities([0, 1])
                target = np.array([0.5, 0.5, 0, 0])
                self.assertTrue(np.allclose(probs, target))

                input_target: list[str] = ['00']
                value = stab.probabilities_dict_from_bitstrings([0, 1], target=input_target)
                target = {"00": 0.5}
                self.assertEqual(value, target)

                input_target: list[str] = ['01']
                value = stab.probabilities_dict_from_bitstrings([0, 1], target=input_target)
                target = {"01": 0.5}
                self.assertEqual(value, target)

                #Verify probability for a target that will return back 0
                input_target: list[str] = ['11']
                value = stab.probabilities_dict_from_bitstrings([0, 1], target=input_target)
                target = {"11": 0}
                self.assertEqual(value, target)

                #Verify probability for a target that will return back 0
                input_target: list[str] = ['10']
                value = stab.probabilities_dict_from_bitstrings([0, 1], target=input_target)
                target = {"10": 0}
                self.assertEqual(value, target)

        for _ in range(self.samples):
            with self.subTest(msg="P([1, 0])"):
                value = stab.probabilities_dict([1, 0])
                target = {"00": 0.5, "10": 0.5}
                self.assertEqual(value, target)
                probs = stab.probabilities([1, 0])
                target = np.array([0.5, 0, 0.5, 0])
                self.assertTrue(np.allclose(probs, target))

                input_target: list[str] = ['00']
                value = stab.probabilities_dict_from_bitstrings([1, 0], target=input_target)
                target = {"00": 0.5}
                self.assertEqual(value, target)

                input_target: list[str] = ['10']
                value = stab.probabilities_dict_from_bitstrings([1, 0], target=input_target)
                target = {"10": 0.5}
                self.assertEqual(value, target)

                input_target: list[str] = ['01']
                value = stab.probabilities_dict_from_bitstrings([1, 0], target=input_target)
                target = {"01": 0}
                self.assertEqual(value, target)

                input_target: list[str] = ['11']
                value = stab.probabilities_dict_from_bitstrings([1, 0], target=input_target)
                target = {"11": 0}
                self.assertEqual(value, target)

                probs = stab.probabilities([1, 0])
                target = np.array([0.5, 0, 0.5, 0])
                self.assertTrue(np.allclose(probs, target))

        for _ in range(self.samples):
            with self.subTest(msg="P[0]"):
                value = stab.probabilities_dict([0])
                target = {"0": 0.5, "1": 0.5}
                self.assertEqual(value, target)
                probs = stab.probabilities([0])
                target = np.array([0.5, 0.5])
                self.assertTrue(np.allclose(probs, target))

                input_target: list[str] = ['0']
                value = stab.probabilities_dict_from_bitstrings([0], target=input_target)
                target = {"0": 0.5}
                self.assertEqual(value, target)

                input_target: list[str] = ['1']
                value = stab.probabilities_dict_from_bitstrings([0], target=input_target)
                target = {"1": 0.5}
                self.assertEqual(value, target)

        for _ in range(self.samples):
            with self.subTest(msg="P([1])"):
                value = stab.probabilities_dict([1])
                target = {"0": 1.0}
                self.assertEqual(value, target)

                input_target: list[str] = ['0']
                value = stab.probabilities_dict_from_bitstrings([1], target=input_target)
                target = {"0": 1.0}
                self.assertEqual(value, target)

                input_target: list[str] = ['1']
                value = stab.probabilities_dict_from_bitstrings([1], target=input_target)
                target = {"1": 0}
                self.assertEqual(value, target)
                probs = stab.probabilities([1])
                target = np.array([1, 0])
                self.assertTrue(np.allclose(probs, target))

    def test_probabilities_dict_qubits(self):
        """Test probabilities and probabilities_dict methods of a subsystem of qubits"""

        num_qubits = 3
        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        qc.h(1)
        qc.h(2)
        stab = StabilizerState(qc)

        test_1_time_no_target: float = 0
        test_1_time_with_targets: float = 0
        test_1_1_time_with_targets: float = 0
        for _ in range(self.samples):
            with self.subTest(msg="P(None), decimals=1"):
                test_1_time_no_target_start = time.monotonic()
                value = stab.probabilities_dict(decimals=1)
                test_1_time_no_target += (time.monotonic() - test_1_time_no_target_start)
                target = {
                    "000": 0.1,
                    "001": 0.1,
                    "010": 0.1,
                    "011": 0.1,
                    "100": 0.1,
                    "101": 0.1,
                    "110": 0.1,
                    "111": 0.1,
                }
                self.assertEqual(value, target)
                probs = stab.probabilities(decimals=1)
                target = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
                self.assertTrue(np.allclose(probs, target))

                target_input: list[str] = ["000", "100"]
                test_1_time_with_target_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=1, target=target_input)
                test_1_time_with_targets += (time.monotonic() - test_1_time_with_target_start)
                target = {
                    "000": 0.1,
                    "100": 0.1
                }
                self.assertEqual(value, target)

                target_input = ["001", "011"]
                test_1_1_time_with_target_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=1, target=target_input)
                test_1_1_time_with_targets += (time.monotonic() - test_1_1_time_with_target_start)
                target = {
                    "001": 0.1,
                    "011": 0.1
                }
                self.assertEqual(value, target)

        #Verify the target test always runs faster then non targetted test
        #Due to the small number of qubits, the performance boost will be much less then when using a large number of qubits
        #And there will be a more siginifcant amount of overhead, so simply checking if it always performs better which it always should
        self.assertTrue(test_1_time_with_targets < test_1_time_no_target)       
        self.assertTrue(test_1_1_time_with_targets < test_1_time_no_target)  

        test_2_time_no_target: float = 0
        test_2_time_with_targets: float = 0
        test_2_1_time_with_targets: float = 0
        for _ in range(self.samples):
            with self.subTest(msg="P(None), decimals=2"):
                test_2_time_no_target_start = time.monotonic()
                value = stab.probabilities_dict(decimals=2)
                test_2_time_no_target += (time.monotonic() - test_2_time_no_target_start)
                target = {
                    "000": 0.12,
                    "001": 0.12,
                    "010": 0.12,
                    "011": 0.12,
                    "100": 0.12,
                    "101": 0.12,
                    "110": 0.12,
                    "111": 0.12,
                }
                self.assertEqual(value, target)
                probs = stab.probabilities(decimals=2)
                target = np.array([0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])
                self.assertTrue(np.allclose(probs, target))

                target_input: list[str] = ["000", "100"]
                test_2_time_with_target_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=2, target=target_input)
                test_2_time_with_targets += (time.monotonic() - test_2_time_with_target_start)
                target = {
                    "000": 0.12,
                    "100": 0.12
                }
                self.assertEqual(value, target)

                target_input = ["001", "011"]
                test_2_1_time_with_target_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=2, target=target_input)
                test_2_1_time_with_targets += (time.monotonic() - test_2_1_time_with_target_start)
                target = {
                    "001": 0.12,
                    "011": 0.12
                }
                self.assertEqual(value, target)

        #Verify the target test always runs faster then non targetted test
        self.assertTrue(test_2_time_with_targets < test_2_time_no_target) 
        self.assertTrue(test_2_1_time_with_targets < test_2_time_no_target) 

        test_3_time_no_target: float = 0
        test_3_time_with_targets: float = 0
        test_3_1_time_with_targets: float = 0
        for _ in range(self.samples):
            with self.subTest(msg="P(None), decimals=3"):
                test_3_time_no_target_start = time.monotonic()
                value = stab.probabilities_dict(decimals=3)
                test_3_time_no_target += (time.monotonic() - test_3_time_no_target_start)
                target = {
                    "000": 0.125,
                    "001": 0.125,
                    "010": 0.125,
                    "011": 0.125,
                    "100": 0.125,
                    "101": 0.125,
                    "110": 0.125,
                    "111": 0.125,
                }
                self.assertEqual(value, target)
                probs = stab.probabilities(decimals=3)
                target = np.array([0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125])
                self.assertTrue(np.allclose(probs, target))

                target_input: list[str] = ["000", "100"]
                test_3_time_with_target_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=3, target=target_input)
                test_3_time_with_targets += (time.monotonic() - test_3_time_with_target_start)
                target = {
                    "000": 0.125,
                    "100": 0.125
                }
                self.assertEqual(value, target)

                target_input = ["001", "011"]
                test_3_1_time_with_target_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=3, target=target_input)
                test_3_1_time_with_targets += (time.monotonic() - test_3_1_time_with_target_start)
                target = {
                    "001": 0.125,
                    "011": 0.125
                }
                self.assertEqual(value, target)

        #Verify the target test always runs faster then non targetted test
        self.assertTrue(test_3_time_with_targets < test_3_time_no_target)         
        self.assertTrue(test_3_1_time_with_targets < test_3_time_no_target)          

        
        #Test with larger number of qubits where performance will be significantly improved with targets to calculate
        num_qubits = 12
        qc = QuantumCircuit(num_qubits)
        for qubit_num in range(0,num_qubits):
            qc.h(qubit_num)
        stab = StabilizerState(qc)

        test_4_time_no_target: float = 0
        for _ in range(self.samples):
            with self.subTest(msg="P(None), decimals=5"):
                test_4_time_no_target_start = time.monotonic()
                value = stab.probabilities_dict(decimals=5)
                test_4_time_no_target += (time.monotonic() - test_4_time_no_target_start)
                #Build target with all combinations of 01 for num_qubits long to value 0.00024, the expected result for each
                target = {result : float(0.00024) for result in [''.join(x) for x in product(['0', '1'], repeat = num_qubits)]}
                self.assertEqual(value, target)
                probs = stab.probabilities(decimals=5)
                target = np.array(([0.00024] * (2**num_qubits)))
                self.assertTrue(np.allclose(probs, target))

        #test with target and 2 close branches
        test_4_time_with_target: float = 0
        for _ in range(self.samples):
            with self.subTest(msg="P(None), decimals=5"):
                input_target: list[str] = ["011110001010", "111110001010"]
                test_4_time_with_target_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=5, target=input_target)
                test_4_time_with_target += (time.monotonic() - test_4_time_with_target_start)
                #Build target with all combinations of 01 for num_qubits long to value 0.00024, the expected result for each
                target = {
                    "011110001010" : 0.00024,
                    "111110001010" : 0.00024
                }
                self.assertEqual(value, target)

        """
        Note: Using targets is a performance enhancement, so we need to verify it does increase performance
        Since we are only calculating 2 complete branches of the 4096 possible branches this should lead 
        to a significant improvement in performance. The amount of nodes to calculate for 12 qubits for 
        the test above is 2^(N+1)-1. This give us (2^(12+1)-1) = 8191 nodes. The example above with caching 
        will need to calculate 13 of the 8191 nodes (due to the second target to calculate being 1 branch from the first being calculated) 
        which will roughly take about 0.158% of the time to calculate compared to all the branches. Lets give a 
        small amount of room for variance, adding 0.5% extra time
        """
        test_time_to_be_under: float = (test_4_time_no_target * (self.probability_percent_of_calculated_branches(13, num_qubits) + self.performance_varability_percent))
        self.assertTrue(test_4_time_with_target < test_time_to_be_under)

        #Run same test as above but without branch path caching, this will cause it to have
        #to calculate the entire branch again for the 2nd target which will lead to 12 + 12 = 24 nodes to calculate
        test_4_time_with_target_no_caching: float = 0
        for _ in range(self.samples):
            with self.subTest(msg="P(None), decimals=5"):
                input_target: list[str] = ["011110001010", "111110001010"]
                test_4_time_with_target_no_caching_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=5, target=input_target, use_caching=False)
                test_4_time_with_target_no_caching += (time.monotonic() - test_4_time_with_target_no_caching_start)
                #Build target with all combinations of 01 for num_qubits long to value 0.00024, the expected result for each
                target = {
                    "011110001010" : 0.00024,
                    "111110001010" : 0.00024
                }
                self.assertEqual(value, target)
        
        test_time_to_be_under: float = (test_4_time_no_target * (self.probability_percent_of_calculated_branches(24, num_qubits) + self.performance_varability_percent))
        #Verify not caching but still using targets performs withing expected speed compared to calculating all branches
        self.assertTrue(test_4_time_with_target_no_caching < test_time_to_be_under)

        #Verify the caching of branch values performs better then not caching when using targets
        #This will make sure that caching is also working and giving us a performance benefit
        #The more targets, and specifically the targets that go down similar branches, the more benefit caching will exhibit
        #This is also more prevelant as the number of qubits grows
        self.assertTrue(test_4_time_with_target < test_4_time_with_target_no_caching)

        #test with target and 2 not close branches, requiring 24 node calculations
        test_5_time_with_target: float = 0
        for _ in range(self.samples):
            with self.subTest(msg="P(None), decimals=5"):
                input_target: list[str] = ["011110001010", "100001110101"]
                test_5_time_with_target_start = time.monotonic()
                value = stab.probabilities_dict_from_bitstrings(decimals=5, target=input_target)
                test_5_time_with_target += (time.monotonic() - test_5_time_with_target_start)
                #Build target with all combinations of 01 for num_qubits long to value 0.00024, the expected result for each
                target = {
                    "011110001010" : 0.00024,
                    "100001110101" : 0.00024
                }
                self.assertEqual(value, target)

        test_time_to_be_under: float = (test_4_time_no_target * (self.probability_percent_of_calculated_branches(24, num_qubits) + self.performance_varability_percent))
        self.assertTrue(test_5_time_with_target < test_time_to_be_under)
        

    def test_probabilities_dict_ghz(self):
        """Test probabilities and probabilities_dict method of a subsystem of qubits"""

        num_qubits = 3
        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)

        with self.subTest(msg="P(None)"):
            stab = StabilizerState(qc)
            value = stab.probabilities_dict()
            target = {"000": 0.5, "111": 0.5}
            self.assertEqual(value, target)

            input_target: list[str] = ["000"]
            value = stab.probabilities_dict_from_bitstrings(target=input_target)
            target = {"000": 0.5}
            self.assertEqual(value, target)

            input_target: list[str] = ["111"]
            value = stab.probabilities_dict_from_bitstrings(target=input_target)
            target = {"111": 0.5}
            self.assertEqual(value, target)

            input_target: list[str] = ["001"]
            value = stab.probabilities_dict_from_bitstrings(target=input_target)
            target = {"001": 0}
            self.assertEqual(value, target)

            input_target: list[str] = ["001", "111"]
            value = stab.probabilities_dict_from_bitstrings(target=input_target)
            target = {"001": 0, "111": 0.5}
            #self.assertEqual(value, target)

            input_target: list[str] = ["001", "010", "100", "110", "101", "011"]
            value = stab.probabilities_dict_from_bitstrings(target=input_target)
            target = {"001" : 0, "010" : 0, "100" : 0, "110" : 0, "101" : 0, "011" : 0}
            self.assertEqual(value, target)

            probs = stab.probabilities()
            target = np.array([0.5, 0, 0, 0, 0, 0, 0, 0.5])
            self.assertTrue(np.allclose(probs, target))

        # 3-qubit qargs
        for qargs in [[0, 1, 2], [2, 1, 0], [1, 2, 0], [1, 0, 2]]:
            with self.subTest(msg=f"P({qargs})"):
                probs = stab.probabilities_dict(qargs)
                target = {"000": 0.5, "111": 0.5}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["000"]
                value = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"000": 0.5}
                self.assertEqual(value, target)

                input_target: list[str] = ["111"]
                value = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"111": 0.5}
                self.assertEqual(value, target)

                input_target: list[str] = ["001"]
                value = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"001": 0}
                self.assertEqual(value, target)

                input_target: list[str] = ["001", "111"]
                value = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"001": 0, "111": 0.5}
                #self.assertEqual(value, target)

                input_target: list[str] = ["001", "010", "100", "110", "101", "011"]
                value = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"001" : 0, "010" : 0, "100" : 0, "110" : 0, "101" : 0, "011" : 0}
                self.assertEqual(value, target)

                probs = stab.probabilities(qargs)
                target = np.array([0.5, 0, 0, 0, 0, 0, 0, 0.5])
                self.assertTrue(np.allclose(probs, target))

        # 2-qubit qargs
        for qargs in [[0, 1], [2, 1], [1, 0], [1, 2]]:
            with self.subTest(msg=f"P({qargs})"):
                probs = stab.probabilities_dict(qargs)
                target = {"00": 0.5, "11": 0.5}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["00"]
                probs = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"00": 0.5}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["11"]
                probs = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"11": 0.5}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["01"]
                probs = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"01": 0}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["10"]
                probs = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"10": 0}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["01", "00"]
                probs = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"01": 0, "00": 0.5}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["10", "11"]
                probs = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"11": 0.5, "10": 0}
                self.assertDictAlmostEqual(probs, target)

                probs = stab.probabilities(qargs)
                target = np.array([0.5, 0, 0, 0.5])
                self.assertTrue(np.allclose(probs, target))

        # 1-qubit qargs
        for qargs in [[0], [1], [2]]:
            with self.subTest(msg=f"P({qargs})"):
                probs = stab.probabilities_dict(qargs)
                target = {"0": 0.5, "1": 0.5}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["0"]
                probs = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"0": 0.5}
                self.assertDictAlmostEqual(probs, target)

                input_target: list[str] = ["1"]
                probs = stab.probabilities_dict_from_bitstrings(qargs, target=input_target)
                target = {"1": 0.5}
                self.assertDictAlmostEqual(probs, target)
                
                probs = stab.probabilities(qargs)
                target = np.array([0.5, 0.5])
                self.assertTrue(np.allclose(probs, target))

    @combine(num_qubits=[2, 3, 4])
    def test_probs_random_subsystem(self, num_qubits):
        """Test probabilities and probabilities_dict methods
        of random cliffords for a subsystem of qubits"""

        for _ in range(self.samples):
            for subsystem_size in range(1, num_qubits):
                cliff = random_clifford(num_qubits, seed=self.rng)
                qargs = np.random.choice(num_qubits, size=subsystem_size, replace=False)
                qc = cliff.to_circuit()
                stab = StabilizerState(cliff)
                probs = stab.probabilities(qargs)

                target_dict = Statevector(qc).probabilities_dict(qargs)
                probs_dict = stab.probabilities_dict(qargs)
                target = Statevector(qc).probabilities(qargs)
                self.assertTrue(np.allclose(probs, target))
                self.assertDictAlmostEqual(probs_dict, target_dict)

                #Perform targetted test, with random samples of targets to use
                random_target_dict: list = random.sample(list(target_dict), random.randint(1, len(target_dict)))
                probs_dict = stab.probabilities_dict_from_bitstrings(qargs, target=random_target_dict)
                target_dict_recalc = {key : target_dict[key] for key in probs_dict}
                self.assertDictAlmostEqual(probs_dict, target_dict_recalc)

    @combine(num_qubits=[2, 3, 4, 5])
    def test_expval_from_random_clifford(self, num_qubits):
        """Test that the expectation values for a random Clifford,
        where the Pauli operators are all its stabilizers,
        are equal to 1."""

        for _ in range(self.samples):
            cliff = random_clifford(num_qubits, seed=self.rng)
            qc = cliff.to_circuit()
            stab = StabilizerState(qc)
            stab_gen = stab.clifford.to_dict()["stabilizer"]
            for i in range(num_qubits):
                op = Pauli(stab_gen[i])
                exp_val = stab.expectation_value(op)
                self.assertEqual(exp_val, 1)

    def test_sample_counts_reset_bell(self):
        """Test sample_counts after reset for Bell state"""

        num_qubits = 2
        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        qc.cx(0, 1)
        stab = StabilizerState(qc)

        target = {"00": self.shots / 2, "10": self.shots / 2}
        counts = {"00": 0, "10": 0}
        for _ in range(self.shots):
            res = stab.reset([0])
            value = res.measure()[0]
            counts[value] += 1
        self.assertDictAlmostEqual(counts, target, self.threshold)

        target = {"00": self.shots / 2, "01": self.shots / 2}
        counts = {"00": 0, "01": 0}
        for _ in range(self.shots):
            res = stab.reset([1])
            value = res.measure()[0]
            counts[value] += 1
        self.assertDictAlmostEqual(counts, target, self.threshold)

    def test_sample_counts_memory_ghz(self):
        """Test sample_counts and sample_memory method for GHZ state"""

        num_qubits = 3
        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)
        stab = StabilizerState(qc)

        # 3-qubit qargs
        target = {"000": self.shots / 2, "111": self.shots / 2}
        for qargs in [[0, 1, 2], [2, 1, 0], [1, 2, 0], [1, 0, 2]]:
            with self.subTest(msg=f"counts (qargs={qargs})"):
                counts = stab.sample_counts(self.shots, qargs=qargs)
                self.assertDictAlmostEqual(counts, target, self.threshold)

            with self.subTest(msg=f"memory (qargs={qargs})"):
                memory = stab.sample_memory(self.shots, qargs=qargs)
                self.assertEqual(len(memory), self.shots)
                self.assertEqual(set(memory), set(target))

        # 2-qubit qargs
        target = {"00": self.shots / 2, "11": self.shots / 2}
        for qargs in [[0, 1], [2, 1], [1, 2], [1, 0]]:
            with self.subTest(msg=f"counts (qargs={qargs})"):
                counts = stab.sample_counts(self.shots, qargs=qargs)
                self.assertDictAlmostEqual(counts, target, self.threshold)

            with self.subTest(msg=f"memory (qargs={qargs})"):
                memory = stab.sample_memory(self.shots, qargs=qargs)
                self.assertEqual(len(memory), self.shots)
                self.assertEqual(set(memory), set(target))

        # 1-qubit qargs
        target = {"0": self.shots / 2, "1": self.shots / 2}
        for qargs in [[0], [1], [2]]:
            with self.subTest(msg=f"counts (qargs={qargs})"):
                counts = stab.sample_counts(self.shots, qargs=qargs)
                self.assertDictAlmostEqual(counts, target, self.threshold)

            with self.subTest(msg=f"memory (qargs={qargs})"):
                memory = stab.sample_memory(self.shots, qargs=qargs)
                self.assertEqual(len(memory), self.shots)
                self.assertEqual(set(memory), set(target))

    def test_sample_counts_memory_superposition(self):
        """Test sample_counts and sample_memory method of a 3-qubit superposition"""

        num_qubits = 3
        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        qc.h(1)
        qc.h(2)
        stab = StabilizerState(qc)

        # 3-qubit qargs
        target = {
            "000": self.shots / 8,
            "001": self.shots / 8,
            "010": self.shots / 8,
            "011": self.shots / 8,
            "100": self.shots / 8,
            "101": self.shots / 8,
            "110": self.shots / 8,
            "111": self.shots / 8,
        }
        for qargs in [[0, 1, 2], [2, 1, 0], [1, 2, 0], [1, 0, 2]]:
            with self.subTest(msg=f"counts (qargs={qargs})"):
                counts = stab.sample_counts(self.shots, qargs=qargs)
                self.assertDictAlmostEqual(counts, target, self.threshold)

            with self.subTest(msg=f"memory (qargs={qargs})"):
                memory = stab.sample_memory(self.shots, qargs=qargs)
                self.assertEqual(len(memory), self.shots)
                self.assertEqual(set(memory), set(target))

        # 2-qubit qargs
        target = {
            "00": self.shots / 4,
            "01": self.shots / 4,
            "10": self.shots / 4,
            "11": self.shots / 4,
        }
        for qargs in [[0, 1], [2, 1], [1, 2], [1, 0]]:
            with self.subTest(msg=f"counts (qargs={qargs})"):
                counts = stab.sample_counts(self.shots, qargs=qargs)
                self.assertDictAlmostEqual(counts, target, self.threshold)

            with self.subTest(msg=f"memory (qargs={qargs})"):
                memory = stab.sample_memory(self.shots, qargs=qargs)
                self.assertEqual(len(memory), self.shots)
                self.assertEqual(set(memory), set(target))

        # 1-qubit qargs
        target = {"0": self.shots / 2, "1": self.shots / 2}
        for qargs in [[0], [1], [2]]:
            with self.subTest(msg=f"counts (qargs={qargs})"):
                counts = stab.sample_counts(self.shots, qargs=qargs)
                self.assertDictAlmostEqual(counts, target, self.threshold)

            with self.subTest(msg=f"memory (qargs={qargs})"):
                memory = stab.sample_memory(self.shots, qargs=qargs)
                self.assertEqual(len(memory), self.shots)
                self.assertEqual(set(memory), set(target))


@ddt
class TestStabilizerStateExpectationValue(QiskitTestCase):
    """Tests for StabilizerState.expectation_value method."""

    rng = np.random.default_rng(12345)
    samples = 10
    shots = 1000
    threshold = 0.1 * shots

    @data(("Z", 1), ("X", 0), ("Y", 0), ("I", 1), ("Z", 1), ("-Z", -1), ("iZ", 1j), ("-iZ", -1j))
    @unpack
    def test_expval_single_qubit_0(self, label, target):
        """Test expectation_value method of a single qubit on |0>"""
        qc = QuantumCircuit(1)
        stab = StabilizerState(qc)
        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(("Z", -1), ("X", 0), ("Y", 0), ("I", 1))
    @unpack
    def test_expval_single_qubit_1(self, label, target):
        """Test expectation_value method of a single qubit on |1>"""
        qc = QuantumCircuit(1)
        qc.x(0)
        stab = StabilizerState(qc)
        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(("Z", 0), ("X", 1), ("Y", 0), ("I", 1), ("X", 1), ("-X", -1), ("iX", 1j), ("-iX", -1j))
    @unpack
    def test_expval_single_qubit_plus(self, label, target):
        """Test expectation_value method of a single qubit on |+>"""
        qc = QuantumCircuit(1)
        qc.h(0)
        stab = StabilizerState(qc)
        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(
        ("II", 1),
        ("XX", 0),
        ("YY", 0),
        ("ZZ", 1),
        ("IX", 0),
        ("IY", 0),
        ("IZ", 1),
        ("XY", 0),
        ("XZ", 0),
        ("YZ", 0),
        ("-ZZ", -1),
        ("iZZ", 1j),
        ("-iZZ", -1j),
    )
    @unpack
    def test_expval_two_qubits_00(self, label, target):
        """Test expectation_value method of two qubits in |00>"""

        num_qubits = 2

        qc = QuantumCircuit(num_qubits)
        stab = StabilizerState(qc)

        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(
        ("II", 1),
        ("XX", 0),
        ("YY", 0),
        ("ZZ", 1),
        ("IX", 0),
        ("IY", 0),
        ("IZ", -1),
        ("XY", 0),
        ("XZ", 0),
        ("YZ", 0),
    )
    @unpack
    def test_expval_two_qubits_11(self, label, target):
        """Test expectation_value method of two qubits in |11>"""
        qc = QuantumCircuit(2)
        qc.x(0)
        qc.x(1)
        stab = StabilizerState(qc)
        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(
        ("II", 1),
        ("XX", 1),
        ("YY", 0),
        ("ZZ", 0),
        ("IX", 1),
        ("IY", 0),
        ("IZ", 0),
        ("XY", 0),
        ("XZ", 0),
        ("YZ", 0),
        ("-XX", -1),
        ("iXX", 1j),
        ("-iXX", -1j),
    )
    @unpack
    def test_expval_two_qubits_plusplus(self, label, target):
        """Test expectation_value method of two qubits in |++>"""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.h(1)
        stab = StabilizerState(qc)

        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(
        ("II", 1),
        ("XX", 0),
        ("YY", 0),
        ("ZZ", 0),
        ("IX", 0),
        ("IY", 0),
        ("IZ", -1),
        ("XY", 0),
        ("XZ", -1),
        ("YZ", 0),
    )
    @unpack
    def test_expval_two_qubits_plus1(self, label, target):
        """Test expectation_value method of two qubits in |+1>"""
        qc = QuantumCircuit(2)
        qc.x(0)
        qc.h(1)
        stab = StabilizerState(qc)

        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(
        ("II", 1),
        ("XX", 1),
        ("YY", -1),
        ("ZZ", 1),
        ("IX", 0),
        ("IY", 0),
        ("IZ", 0),
        ("XY", 0),
        ("XZ", 0),
        ("YZ", 0),
        ("-YY", 1),
        ("iYY", -1j),
        ("-iYY", 1j),
    )
    @unpack
    def test_expval_two_qubits_bell_phi_plus(self, label, target):
        """Test expectation_value method of two qubits in bell phi plus"""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        stab = StabilizerState(qc)

        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(
        ("II", 1),
        ("XX", 1),
        ("YY", 1),
        ("ZZ", -1),
        ("IX", 0),
        ("IY", 0),
        ("IZ", 0),
        ("XY", 0),
        ("XZ", 0),
        ("YZ", 0),
        ("-XX", -1),
        ("-YY", -1),
        ("iXX", 1j),
        ("iYY", 1j),
        ("-iXX", -1j),
        ("-iYY", -1j),
    )
    @unpack
    def test_expval_two_qubits_bell_phi_minus(self, label, target):
        """Test expectation_value method of two qubits in bell phi minus"""

        qc = QuantumCircuit(2)
        qc.h(0)
        qc.x(1)
        qc.cx(0, 1)
        stab = StabilizerState(qc)

        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @data(
        ("II", 1),
        ("XX", 1),
        ("YY", 1),
        ("ZZ", -1),
        ("IX", 0),
        ("IY", 0),
        ("IZ", 0),
        ("XY", 0),
        ("XZ", 0),
        ("YZ", 0),
        ("-XX", -1),
        ("-YY", -1),
        ("iXX", 1j),
        ("iYY", 1j),
        ("-iXX", -1j),
        ("-iYY", -1j),
    )
    @unpack
    def test_expval_two_qubits_bell_sdg_h(self, label, target):
        """Test expectation_value method of two qubits in bell followed by sdg and h"""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        qc.sdg(0)
        qc.sdg(1)
        qc.h(0)
        qc.h(1)
        stab = StabilizerState(qc)

        op = Pauli(label)
        expval = stab.expectation_value(op)
        self.assertEqual(expval, target)

    @combine(num_qubits=[2, 3, 4, 5])
    def test_expval_random(self, num_qubits):
        """Test expectation_value method of random Cliffords"""

        for _ in range(self.samples):
            cliff = random_clifford(num_qubits, seed=self.rng)
            op = random_pauli(num_qubits, group_phase=True, seed=self.rng)
            qc = cliff.to_circuit()
            stab = StabilizerState(cliff)
            exp_val = stab.expectation_value(op)
            target = Statevector(qc).expectation_value(op)
            self.assertAlmostEqual(exp_val, target)

    @combine(num_qubits=[2, 3, 4, 5])
    def test_expval_random_subsystem(self, num_qubits):
        """Test expectation_value method of random Cliffords and a subsystem"""

        for _ in range(self.samples):
            cliff = random_clifford(num_qubits, seed=self.rng)
            op = random_pauli(2, group_phase=True, seed=self.rng)
            qargs = np.random.choice(num_qubits, size=2, replace=False)
            qc = cliff.to_circuit()
            stab = StabilizerState(cliff)
            exp_val = stab.expectation_value(op, qargs)
            target = Statevector(qc).expectation_value(op, qargs)
            self.assertAlmostEqual(exp_val, target)

    def test_stabilizer_bell_equiv(self):
        """Test that two circuits produce the same stabilizer group."""

        qc1 = QuantumCircuit(2)
        qc1.h(0)
        qc1.x(1)
        qc1.cx(0, 1)

        qc2 = QuantumCircuit(2)
        qc2.h(0)
        qc2.cx(0, 1)
        qc2.sdg(0)
        qc2.sdg(1)
        qc2.h(0)
        qc2.h(1)

        qc3 = QuantumCircuit(2)
        qc3.h(0)
        qc3.cx(0, 1)

        qc4 = QuantumCircuit(2)
        qc4.h(0)
        qc4.cx(0, 1)
        qc4.s(0)
        qc4.sdg(1)
        qc4.h(0)
        qc4.h(1)

        cliff1 = StabilizerState(qc1)  # ['+XX', '-ZZ']
        cliff2 = StabilizerState(qc2)  # ['+YY', '+XX']
        cliff3 = StabilizerState(qc3)  # ['+XX', '+ZZ']
        cliff4 = StabilizerState(qc4)  # ['-YY', '+XX']

        # [XX, -ZZ] and [XX, YY] both generate the stabilizer group {II, XX, YY, -ZZ}
        self.assertTrue(cliff1.equiv(cliff2))
        self.assertEqual(cliff1.probabilities_dict(), cliff2.probabilities_dict())

        # [XX, ZZ] and [XX, -YY] both generate the stabilizer group {II, XX, -YY, ZZ}
        self.assertTrue(cliff3.equiv(cliff4))
        self.assertEqual(cliff3.probabilities_dict(), cliff4.probabilities_dict())

        self.assertFalse(cliff1.equiv(cliff3))
        self.assertFalse(cliff2.equiv(cliff4))

    def test_visualize_does_not_throw_error(self):
        """Test to verify that drawing StabilizerState does not throw an error"""
        clifford = random_clifford(3, seed=0)
        stab = StabilizerState(clifford)
        _ = repr(stab)

if __name__ == "__main__":
    unittest.main()
