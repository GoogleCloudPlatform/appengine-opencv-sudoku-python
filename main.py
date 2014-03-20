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


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


class MainHandler(webapp2.RequestHandler):
    """Handles requests to the main page."""

    def get(self):
        """Display the index page."""

        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.out.write(template.render({}))

class UploadImage(webapp2.RequestHandler):
    """Handles requests to show a puzzle upload page."""

    def get(self):
        """Display the puzzle upload page."""

        template = JINJA_ENVIRONMENT.get_template('templates/upload.html')
        self.response.out.write(template.render({}))


APP = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/upload', UploadImage)
], debug=True)
