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

"""VM Runtime sample application using OpenCV."""

__author__ = 'kbrisbin@google.com (Kathryn Hurley)'

import logging
import os

import jinja2
import webapp2

import sudoku_solver


class Solve(webapp2.RequestHandler):
    """Handles the post request with the sudoku image."""

    def get(self):
        """Simplistic solver API"""

        puzzle = self.request.get('puzzle')
        if puzzle:
            solver = sudoku_solver.SudokuSolver()
            try:
                solution = solver.solve(puzzle)
            except (sudoku_solver.ContradictionError, ValueError) as e:
                logging.debug(e)
                self.response.write(
                        '%s Puzzle: %s.' % (str(e), puzzle))
                return
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(solution)
        else:
            self.response.write('No puzzle data')


APP = webapp2.WSGIApplication([
    ('/solve', Solve)
], debug=True)
