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

# from google.appengine.api import app_identity
from google.appengine.api import modules
from google.appengine.api import runtime
# from google.appengine.api import users
from google.appengine.ext import ndb

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

def shutdown_hook():
    """A hook function for de-registering myself."""
    logging.info('shutdown_hook called.')
    instance_id = modules.get_current_instance_id()
    ndb.transaction(
        lambda: ActiveServer.get_instance_key(instance_id).delete())

class ActiveServer(ndb.Model):
    """A model to store active servers.

    We use the instance id as the key name, and there are no properties.
    """

    @classmethod
    def get_instance_key(cls, instance_id):
        """Return a key for the given instance_id.

        Args:
            An instance id for the server.

        Returns:
            A Key object which has a common parent key with the name 'Root'.
        """
        return ndb.Key(cls, 'Root', cls, instance_id)


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

        # aju testing instance mgmt -- will probably just remove this code
        # numinst = modules.get_num_instances()
        # logging.info("got %d instances", numinst)
        # if numinst == 2:
        #     logging.info("setting num instances from 2 to 3")
        #     modules.set_num_instances(3)
        # elif numinst == 3:
        #     logging.info("setting num instances from 3 to 4")
        #     modules.set_num_instances(4)

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

class Start(webapp2.RequestHandler):
    """A handler for /_ah/start."""

    def get(self):
        """A handler for /_ah/start, registering myself."""
        runtime.set_shutdown_hook(shutdown_hook)
        instance_id = modules.get_current_instance_id()
        logging.info("registering instance id %s", instance_id)
        server = ActiveServer(key=ActiveServer.get_instance_key(instance_id))
        server.put()


class Stop(webapp2.RequestHandler):
    """A handler for /_ah/stop."""

    def get(self):
        """Just call shutdown_hook now for a temporary workaround.

        With the initial version of the VM Runtime, a call to
        /_ah/stop hits this handler, without invoking the shutdown
        hook we registered in the start handler. We're working on the
        fix to make it a consistent behavior same as the traditional
        App Engine backends. After the fix is out, this stop handler
        won't be necessary any more.
        """
        shutdown_hook()


APP = webapp2.WSGIApplication([
    ('/solve', Solve),
    ('/solve_upld', SolveImageUpload),
    ('/_ah/start', Start),
    ('/_ah/stop', Stop)
], debug=True)
