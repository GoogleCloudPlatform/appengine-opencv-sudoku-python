
from google.appengine.api import app_identity

BUCKET_NAME = '' or app_identity.get_default_gcs_bucket_name()
