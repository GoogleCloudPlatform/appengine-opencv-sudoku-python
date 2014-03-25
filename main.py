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
import jinja2
import json
import logging
import os
import webapp2

from google.appengine.api import taskqueue

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
    """Handles requests to the main page, which supports video capture of a puzzle
    to be solved."""

    def get(self):
        """Display the index page."""

        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.out.write(template.render({}))

class UploadImage(webapp2.RequestHandler):
    """Handles requests to show a puzzle upload page, which supports upload of sudoku
    image files."""

    def get(self):
        """Display the puzzle upload page."""

        template = JINJA_ENVIRONMENT.get_template('templates/upload.html')
        self.response.out.write(template.render({}))

class SolveStage(webapp2.RequestHandler):
    """Handles a request with a sudoku image to solve.
    Accepts binary (as from <input type="file">) as default, and looks for an image
    file at a specified URL if the binary input is not given.
    Launches a task queue task, run on a VM backend, to solve the given puzzle.
    """
    api_url = 'https://storage.googleapis.com'

    def generate_error_response(self, filename, solved_url):
        # We got an error, so we'll copy an error message image to the GCS file
        # indicated to contain the result.
        utils.copy_error_image(filename)
        # respond to the client, indicating the URL to which the result has
        # been written.
        resp = {'status': 'ERROR', 'solved_url' : solved_url}
        return json.dumps(resp)

    def post(self):
        """Handles the post request with the sudoku image to solve.
        Accepts binary (as from <input type="file">) as default, and looks for an image
        file at a specified URL if the binary input is not given.
        Launches a task queue task, run on a VM backend, to solve the given puzzle.
        Returns a JSON message to the client, which includes a URL that will contain
        the result.
        """

        # generate a URL to which the result will be written
        filename = utils.create_fname('jpg')  # A new GCS-formatted filename.
        # based on the filename, the results will show up at this URL.
        solved_url = self.api_url + filename
        image_data = self.request.get('sudoku')
        image_url = ''
        # if we got image data, write it to a GCS file and generate a URL
        if image_data:
            image_data = decode_if_needed(image_data)
            gcs_file = utils.create_png_file(image_data)
            image_url = self.api_url + gcs_file
        else:
            # otherwise, try to get the image from the default URL in the form
            logging.info("did not get image data from form submit")
            image_url = self.request.get('sudoku_url')
        if not image_url:
            logging.warn("could not generate image url")
            resp = self.generate_error_response(filename, solved_url)
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(resp)
            return
        logging.info("using image url: %s", image_url)
        # create a task to solve the puzzle.  The handler will be routed to a
        # Managed VM.
        try:
            # Create a Task Queue task to parse and solve the puzzle.
            # As task parameters, indicate the URL containing the image to solve, and
            # the GCS filename to which to write the solution image.
            task = taskqueue.Task(url='/solve_async',
                           method='POST',
                           params={'image_url': image_url,
                                   'filename' : filename})
            # add the task to the default task queue. (Alternately, you could define a separate
            # dedicated task queue for this purpose).
            taskqueue.Queue().add(task)
            # Respond to the client, indicating the URL to which the solution will
            # be written.
            resp = {'status': 'OK',
                    'solved_url' : solved_url}
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(resp))

        except (taskqueue.UnknownQueueError, taskqueue.TransientError):
            logging.exception("issue adding task to queue")
            resp = self.generate_error_response(filename, solved_url)
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(resp)


APP = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/upload', UploadImage),
    ('/stage', SolveStage),
], debug=True)
