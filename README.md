ManageIQ Python API Client
==========================

This python package provides the ManageIQ API Client library.


Getting Started
---------------

Preparing your python virtual environment:

    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -e .  # To create an editable install of this package
    $ pip install git+https://github.com/ManageIQ/manageiq-api-client-python.git  # Or you can install it from git directly

To run the example present in this repository you probably need to configure
your options (if different from the default shown here):

    $ export MIQURL=http://localhost:3000/api
    $ export MIQUSERNAME=admin
    $ export MIQPASSWORD=smartvm

    $ python example.py


Legal
-----

Copyright 2013 Red Hat, Inc. and/or its affiliates.

License: GPL version 2 or any later version (see COPYING or
http://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html for
details).
