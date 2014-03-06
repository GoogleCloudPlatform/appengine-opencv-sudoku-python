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

import sudoku_image_parser
import sudoku_solver


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


class MainHandler(webapp2.RequestHandler):
    """Handles requests to the main page."""

    def get(self):
        """Display the index page."""

        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.out.write(template.render({}))


class Solve(webapp2.RequestHandler):
    """Handles the post request with the sudoku image."""

    def post(self):
        """Display the solved sudoku puzzle."""

        image_data = self.request.get('sudoku')
        if image_data:
            parser = sudoku_image_parser.SudokuImageParser()
            stringified_puzzle = ''
            try:
                stringified_puzzle = parser.parse(image_data)
                logging.info("stringified puzzle: %s", stringified_puzzle)
            except sudoku_image_parser.ImageError as e:
                self._return_error(self, str(e))
                return

            solver = sudoku_solver.SudokuSolver()
            solution = ''
            try:
                solution = solver.solve(stringified_puzzle)
            except (sudoku_solver.ContradictionError, ValueError) as e:
                logging.debug(e)
                self._return_error(
                        self, '%s Puzzle: %s.' % (str(e), stringified_puzzle))
                return

            image_solution = parser.draw_solution(solution)
            image_solution = parser.convert_to_jpeg(image_solution)

            self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.write(image_solution.tostring())

        else:
            self._return_error(self, 'No file uploaded!')

    def _return_error(self, handler, e):
        """Displays an error page.

        Args:
            handler: A RequestHandler object.
            e: A string error message.
        """

        template = JINJA_ENVIRONMENT.get_template('templates/error.html')
        handler.response.out.write(template.render({'error': e}))


APP = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/solve', Solve)
], debug=True)
