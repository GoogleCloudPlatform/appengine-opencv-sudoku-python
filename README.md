# VM Runtime OpenCV demo

## About

This sample application demonstrates the use of [OpenCV][1] using App
Engine's VM Runtime feature. The application allows a user to upload
an image of a Sudoku puzzle. The app then solves the puzzle and displays
the solution on the image.

Code was used and modified from the following sources:

- [OpenCV Python Tutorials blog][2]
- [Peter Norvig's blog][3]
- [OpenCV's square detector sample][4]


## Deployment

First, edit the bucket name in `config.py` to the name of a Google Cloud Storage bucket for which your app has been given write permissions via its service account.  See [Using Service Accounts for Authentication](https://developers.google.com/storage/docs/authentication#service_accounts) for more information.

This demo uses two [Modules](https://developers.google.com/appengine/docs/python/modules/), defined in `app.yaml` (the default module) and `backend.yaml` (the 'solver' module).  Change the app name in both those files to the name of your app.

To deploy, do, the following.  First, update the modules as follows:

    <path_to_sdk>/appcfg.py update -s preview.appengine.google.com app.yaml backend.yaml

(You can also deploy them individually if you like).

Then, update the app's module dispatch definitions as follows.  You only need to do this step more than once if you change the app's module routing information.

    <path_to_sdk>/appcfg.py update_dispatch -s preview.appengine.google.com  <proj_dir>

[1]: http://opencv.org/
[2]: http://opencvpython.blogspot.com/
[3]: http://norvig.com/sudoku.html
[4]: https://github.com/Itseez/opencv/blob/master/samples/python2/squares.py
