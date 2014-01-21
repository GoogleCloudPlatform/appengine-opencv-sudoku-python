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

Code modified from the following source:
- http://goo.gl/U4hMDV
"""

__author__ = 'kbrisbin@google.com (Kathryn Hurley)'


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
        """Solve the sudoku puzzle.

        Args:
            grid: String Sudoku puzzle with all numbers in a row and blanks
                set to zero.

        Returns:
            The solution as a string.

        Raises:
            ContradictionError: if puzzle cannot be solved.
        """

        answer = self._search(self._parse_grid(grid))
        if answer:
            keys = answer.keys()
            keys.sort()
            string_answer = ''.join(answer[i] for i in keys)
            return string_answer

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

    def _parse_grid(self, grid):
        """Convert grid to a dict of possible values, {square: digits}.

        Args:
            grid: String Sudoku puzzle with all numbers in a row and blanks
                set to zero.

        Returns:
            Dictionary of possible values.

        Raises:
            ContradictionError: if puzzle cannot be solved.
        """

        # To start, every square can be any digit; assign values from the grid.
        values = dict((s, self.digits) for s in self.squares)
        for s, d in self._grid_values(grid).items():
            if d in self.digits and not self._assign(values, s, d):
                raise ContradictionError('Puzzle cannot be solved.')

        return values

    def _grid_values(self, grid):
        """Convert grid to dict of {square: char} with '0' or '.' for empties.

        Args:
            grid: String Sudoku puzzle with all numbers in a row and blanks
                set to zero.

        Returns:
            Dictionary of {square: char}.
        """

        chars = [c for c in grid if c in self.digits or c in '0.']
        assert len(chars) == 81
        return dict(zip(self.squares, chars))

    def _assign(self, values, s, d):
        """Eliminate all other values (except d) from values[s] and propagate.

        Args:
            values: List of string values.
            s: Index from list values.
            d: String to keep.

        Returns:
            The list of values.

        Raises:
            ContradictionError: if the puzzle cannot be solved.
        """

        other_values = values[s].replace(d, '')

        if all(self._eliminate(values, s, d2) for d2 in other_values):
            return values

        raise ContradictionError('Puzzle cannot be solved.')

    def _search(self, values):
        """Using depth-first search and propagation, try all possible values.

        Args:
            values: List of strings.

        Returns:
            List of string values.

        Raises:
            ValueError: if values is False.
        """

        if values is False:
            raise ValueError('values cannot be False')

        if all(len(values[s]) == 1 for s in self.squares):
            return values

        # Chose the unfilled square s with the fewest possibilities
        n, s = min((len(values[s]), s) for s in self.squares if len(
                values[s]) > 1)
        return self._some(self._search(self._assign(
                values.copy(), s, d)) for d in values[s])

    def _eliminate(self, values, s, d):
        """Eliminate d from values[s]; propagate when values or places <= 2.

        Args:
            values: List of strings.
            s: Index from list of values.
            d: String value to eliminate.

        Returns:
            String list of values.

        Raises:
            ContradictionError: if puzzle cannot be solved.
        """

        if d not in values[s]:
            return values

        values[s] = values[s].replace(d, '')

        # If a square s is reduced to one value d2, eliminate d2 from the peers.
        if not values[s]:
            raise ContradictionError('Puzzle cannot be solved.')

        elif len(values[s]) == 1:
            d2 = values[s]
            if not all(self._eliminate(values, s2, d2) for s2 in self.peers[s]):
                raise ContradictionError('Puzzle cannot be solved.')

        # If a unit u is reduced to only one place for a value d, put it there.
        for u in self.units[s]:
            dplaces = [s for s in u if d in values[s]]
            if not dplaces:
                raise ContradictionError('Puzzle cannot be solved.')

            elif len(dplaces) == 1:
                # d can only be in one place in unit; assign it there
                if not self._assign(values, dplaces[0], d):
                    raise ContradictionError('Puzzle cannot be solved.')

        return values

    def _some(self, seq):
        """Return some element of seq that is true.

        Args:
            seq: An iterable object.

        Returns:
            Any item in the iterable object that is true or False if not found.
        """

        for e in seq:
            if e: return e

        return False


class ContradictionError(Exception):
    """Contradiction found in puzzle."""
