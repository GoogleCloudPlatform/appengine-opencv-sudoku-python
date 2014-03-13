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

import base64
import logging
import os

import jinja2
import webapp2

import sudoku_image_parser
import sudoku_solver
import utils


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

def decode_if_needed(data):
    if data.startswith('data') and 'base64' in data:
        # remove data URL prefixes
        data = data.split('base64,', 1)[1]
        data = base64.standard_b64decode(data)
    return data


class MainHandler(webapp2.RequestHandler):
    """Handles requests to the main page."""

    def get(self):
        """Display the index page."""

        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.out.write(template.render({}))

class SolverBase(webapp2.RequestHandler):

    # TODO: does the cloudstorage module api include generation of the public URL?
    # Couldn't spot it.
    api_url = 'https://storage.googleapis.com'


    def _solved_puzzle_image(self, stringified_puzzle):
        solver = sudoku_solver.SudokuSolver()
        solution = ''
        solution = solver.solve(stringified_puzzle)
        image_solution = self.parser.draw_solution(solution)
        image_solution = self.parser.convert_to_jpeg(image_solution)
        return image_solution

    def _return_error(self, handler, e):
        """Displays an error page.

        Args:
            handler: A RequestHandler object.
            e: A string error message.
        """

        template = JINJA_ENVIRONMENT.get_template('templates/error.html')
        handler.response.out.write(template.render({'error': e}))


class Solve(SolverBase):
    """Handles the post request with the sudoku image.

    Accepts either data URL strings or binary (as from <input type="file">).
    """

    def post(self):
        """Display the solved sudoku puzzle."""

        image_data = self.request.get('sudoku')
        image_data = decode_if_needed(image_data)
        if image_data:
            self.parser = sudoku_image_parser.SudokuImageParser()
            stringified_puzzle = ''
            try:
                stringified_puzzle = self.parser.parse(image_data)
                logging.info("stringified puzzle: %s", stringified_puzzle)
            except (IndexError, sudoku_image_parser.ImageError) as e:
                logging.exception("parse error")
                self._return_error(self, str(e))
                return
            try:
                image_solution = self._solved_puzzle_image(stringified_puzzle)
                gcs_file = utils.create_jpg_file(image_solution.tostring())
                image_url = self.api_url + gcs_file
                logging.debug("url: %s", image_url)
                template = JINJA_ENVIRONMENT.get_template('templates/result.html')
                self.response.out.write(template.render({'image_url': image_url}))
                return
            except (sudoku_solver.ContradictionError, ValueError) as e:
                logging.debug(e)
                self._return_error(
                        self, '%s Puzzle: %s.' % (str(e), stringified_puzzle))
                return
        else:
            self._return_error(self, 'No file uploaded!')



class SolveImageUpload(SolverBase):
    """Handles the post request with the sudoku image."""


    def post(self):
        """Display the solved sudoku puzzle."""

        image_data = self.request.get('sudoku')
        if image_data:
            self.parser = sudoku_image_parser.SudokuImageParser()
            stringified_puzzle = ''
            try:
                stringified_puzzle = self.parser.parse(image_data)
                logging.info("stringified puzzle: %s", stringified_puzzle)
            except (IndexError, sudoku_image_parser.ImageError) as e:
                self._return_error(self, str(e))
                return
            try:
                image_solution = self._solved_puzzle_image(stringified_puzzle)
                gcs_file = utils.create_jpg_file(image_solution.tostring())
                image_url = self.api_url + gcs_file
                logging.debug("url: %s", image_url)
                template = JINJA_ENVIRONMENT.get_template('templates/result.html')
                self.response.out.write(template.render({'image_url': image_url}))
                return
            except (sudoku_solver.ContradictionError, ValueError) as e:
                logging.debug(e)
                self._return_error(
                        self, '%s Puzzle: %s.' % (str(e), stringified_puzzle))
                return
        else:
            self._return_error(self, 'No file uploaded!')


APP = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/solve', Solve),
    ('/solve_upld', SolveImageUpload)
], debug=True)
