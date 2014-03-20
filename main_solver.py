# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Managed VMs sample application using OpenCV, App Engine Modules, and Task Queues."""

import base64
import logging
import os
import jinja2
import webapp2

from google.appengine.api import modules
from google.appengine.ext import ndb
from google.appengine.api import runtime
from google.appengine.api import urlfetch

import sudoku_image_parser
import sudoku_solver
import utils


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


class SolverBase(webapp2.RequestHandler):

    api_url = 'https://storage.googleapis.com'

    def _solved_puzzle_image(self, stringified_puzzle):
        solver = sudoku_solver.SudokuSolver()
        solution = ''
        solution = solver.solve(stringified_puzzle)
        image_solution = self.parser.draw_solution(solution)
        image_solution = self.parser.convert_to_jpeg(image_solution)
        return image_solution


class SolveAsync(SolverBase):
    """Handler to parse and solve the given sudoku puzzle image, and write the result to a
    GCS file.  Run as a task handler.
    """

    def post(self):
        """Parse and solve the given sudoku puzzle image, and write the result to a known GCS
        file.
        """

        image_url = self.request.get('image_url')
        filename = self.request.get('filename')
        image_data = None
        try:
            if image_url:
                logging.info("image url: %s", image_url)
                result = urlfetch.fetch(image_url)
                if result.status_code == 200:
                    image_data = result.content
            else:
                logging.info('did not get image url...')
        except:
            logging.exception("issue fetching url data")
        if image_data:
            self.parser = sudoku_image_parser.SudokuImageParser()
            stringified_puzzle = ''
            try:
                stringified_puzzle = self.parser.parse(image_data)
                logging.info("stringified puzzle: %s", stringified_puzzle)
            except (IndexError, sudoku_image_parser.ImageError) as e:
                logging.debug(e)
                utils.copy_error_image(filename)
                return
            try:
                image_solution = self._solved_puzzle_image(stringified_puzzle)
                gcs_file = utils.create_jpg_file(filename, image_solution.tostring())
                logging.debug("url: %s%s", self.api_url, gcs_file)
                return
            except (sudoku_solver.ContradictionError, ValueError) as e:
                logging.debug(e)
                utils.copy_error_image(filename)
                return
        else:
            logging.info("no image data")


APP = webapp2.WSGIApplication([
    ('/solve_async', SolveAsync)
], debug=True)
