ManageIQ Python API Client
==========================

This python package provides the ManageIQ API Client library.


Getting Started
---------------

Preparing your python virtual environment::

    $ sudo pip install virtualenv
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -e .  # To create an editable install of this package

If you want to install it directly from GitHub::

    $ pip install git+https://github.com/ManageIQ/manageiq-api-client-python.git

To run the example present in this repository you probably need to configure
your options (if different from the default shown here)::

    $ export MIQURL=http://localhost:3000/api
    $ export MIQUSERNAME=admin
    $ export MIQPASSWORD=smartvm
    $ export MIQTOKEN=<<miq_ephemeral_token>>

    $ python example.py

To generate a temporary miq token from the MIQ Dev environment use the following command::

    $ bin/rails r 'puts Api::UserTokenService.new.generate_token("admin","api")'

Legal
-----

Copyright 2013 Red Hat, Inc. and/or its affiliates.

License: GPL version 2 or any later version (see COPYING or
http://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html for
details).
