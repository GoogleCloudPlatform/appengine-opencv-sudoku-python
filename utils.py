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

"""Contains helper utility functions for the Sudoku solver app."""

import base64
import logging
import uuid

import cloudstorage as gcs

import config

def create_fname(suffix):
    path = '/'
    filename = path + config.BUCKET_NAME + path + get_uuid() + '.' + suffix
    # logging.info('Creating GCS filename %s...', filename)
    return filename

def create_jpg_file(filename, image_data):
    """Create a public GCS object for the given image data in the
    configured bucket."""

    gcs_file = gcs.open(filename,
                        'w',
                        content_type='image/jpeg',
                        # make the image public
                        options={'x-goog-acl': 'public-read'}
                        )
    gcs_file.write(image_data)
    gcs_file.close()
    return filename

def create_png_file(image_data):
    """Create a public GCS object for the given image data in the
    configured bucket."""

    filename = create_fname('png')

    gcs_file = gcs.open(filename,
                        'w',
                        content_type='image/png',
                        # make the image public
                        options={'x-goog-acl': 'public-read'}
                        )
    gcs_file.write(image_data)
    gcs_file.close()
    return filename

def copy_error_image(filename):
    """Copy an error image to the given GCS-formatted filename.
    """
    try:
        # If we had an error, use an error message image as the response.
        f = open("templates/sorry.jpg", "rb")
        image_data = f.read()
        gcs_file = create_jpg_file(filename, image_data)
        return gcs_file
    except:
        logging.exception("could not copy image file")
        return None

# get a UUID - URL-safe, base64
def get_uuid():
    r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    return r_uuid.replace('=', '')
