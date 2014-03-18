# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Solves a Sudoku puzzle.

Code modified from the following sources:
- http://goo.gl/U4hMDV, using http://norvig.com/sudoku.py
"""

__author__ = 'kbrisbin@google.com (Kathryn Hurley)'

import logging

import norvig_sudoku

class SudokuSolver(object):
    """Solves a Sudoku puzzle.

    Attributes:
        digits: String of digits from 1 to 9.
        rows: String of letters from A to I.
        cols: String of digits from 1 to 9.
        squares: String representing the cross product of rows and cols.
        unitlist: List of list of strings representing all parts of the
              Sudoku puzzle that go from 1 to 9 (i.e., the top row and the
              top left box).
        units: Dictionary of each box mapped to a each list in the unitlist
              that the box belongs to.
        peers: Dictionary mapping each box mapped to a set of all other
              boxes it effects.
    """

    def __init__(self):
        """Initialize the SudokuSolver object and attributes."""

        self.digits = '123456789'
        self.rows = 'ABCDEFGHI'
        self.cols = self.digits
        self.squares = self._cross(self.rows, self.cols)
        self.unitlist = (
                [self._cross(self.rows, c) for c in self.cols] +
                [self._cross(r, self.cols) for r in self.rows] +
                [self._cross(rs, cs) for rs in (
                        'ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')])
        self.units = dict(
                (s, [u for u in self.unitlist if s in u]) for s in self.squares)
        self.peers = dict(
                (s, set(sum(self.units[s], []))-set([s])) for s in self.squares)

    def solve(self, grid):
        """Solve the sudoku puzzle, using Peter Norvig's solver script (http://norvig.com/sudoku.py)

        Args:
            grid: String Sudoku puzzle with all numbers in a row and blanks
                set to zero.

        Returns:
            The solution as a string.

        Raises:
            ContradictionError: if puzzle cannot be solved.
        """

        values = norvig_sudoku.solve(grid)
        if values and norvig_sudoku.solved(values):
            logging.info("norvig solver returned: %s", values)
            keys = values.keys()
            keys.sort()
            nstring_answer = ''.join(values[i] for i in keys)
            logging.info("norvig solver final string: %s", nstring_answer)
            return nstring_answer

        raise ContradictionError('Puzzle cannot be solved.')

    def _cross(self, a, b):
        """Cross product of elements in a and elements in b.

        Args:
            a: A list of strings.
            b: A list of strings.

        Returns:
            A list of strings representing the cross product of a and b.
        """

        return [x + y for x in a for y in b]



class ContradictionError(Exception):
    """Contradiction found in puzzle."""
