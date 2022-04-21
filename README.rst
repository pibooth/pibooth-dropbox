
===============
pibooth-dropbox
===============

|PythonVersions| |PypiPackage| |Downloads|

``pibooth-dropbox`` is a plugin for the `pibooth`_ application.

Its permits to upload the pictures to a `Dropbox`_ folder. It requires an
internet connection.

Install
-------

::

    $ pip3 install pibooth-dropbox

Configuration
-------------

Here below the new configuration options available in the `pibooth`_ configuration.
**The keys and their default values are automatically added to your configuration after first** `pibooth`_ **restart.**

.. code-block:: ini

    [DROPBOX]

    # Album where pictures are uploaded
    album_name = Pibooth

    # Credentials file downloaded from Google API
    client_id_file =

.. note:: Edit the configuration by running the command ``pibooth --config``.

Picture URL
-----------

Uploaded picture URL is set to ``app.previous_picture_url`` attribute at the end of
`processing` state (``state_processing_exit`` hook).

Grant secured access
--------------------

The upload part was mainly taken und adapted from the Dropbox Api example updown.py from the dropbox-sdk-python
https://github.com/dropbox/dropbox-sdk-python
https://github.com/dropbox/dropbox-sdk-python/blob/master/example/updown.py

Description on how to create a dropbox app is described here for a Gravity app, but it can be used to create any other custom app:
https://docs.gravityforms.com/creating-a-custom-dropbox-app/

Description on how to create a refresh token and how to implement this into a python code is very good described here:
https://stackoverflow.com/questions/70641660/how-do-you-get-and-use-a-refresh-token-for-the-dropbox-api-python-3-x


.. --- Links ------------------------------------------------------------------

.. _`pibooth`: https://pypi.org/project/pibooth

.. _`Dropbox`: https://www.dropbox.com

.. |PythonVersions| image:: https://img.shields.io/badge/python-3.6+-red.svg
   :target: https://www.python.org/downloads
   :alt: Python 3.6+

.. |PypiPackage| image:: https://badge.fury.io/py/pibooth-google-photo.svg
   :target: https://pypi.org/project/pibooth-google-photo
   :alt: PyPi package

.. |Downloads| image:: https://img.shields.io/pypi/dm/pibooth-google-photo?color=purple
   :target: https://pypi.org/project/pibooth-google-photo
   :alt: PyPi downloads
