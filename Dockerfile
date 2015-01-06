FROM google/appengine-python27
RUN apt-get install -y python-opencv

ADD . /app
