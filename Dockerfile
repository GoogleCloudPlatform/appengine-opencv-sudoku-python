FROM gcr.io/google_appengine/python-compat
RUN apt-get update && apt-get install -y python-opencv

ADD . /app
