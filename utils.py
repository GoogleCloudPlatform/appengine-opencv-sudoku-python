"""Contains helper utility functions."""

import base64
import logging
import uuid

import cloudstorage as gcs
import config

def create_jpg_file(image_data):
  """Create a public GCS object for the given image data in the
  configured bucket."""

  path = '/'

  filename = path + config.BUCKET_NAME + path + get_uuid() + '.jpg'
  logging.info('Creating GCS file %s...', filename)

  gcs_file = gcs.open(filename,
                      'w',
                      content_type='image/jpeg',
                      # make the image public
                      options={'x-goog-acl': 'public-read'}
                      )
  gcs_file.write(image_data)
  gcs_file.close()
  return filename

# get a UUID - URL-safe, base64
def get_uuid():
  r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
  return r_uuid.replace('=', '')
