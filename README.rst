
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

    # Dropbox folder where pictures are uploaded. Subfolders can be separated by /
    album_name = Pibooth

    # Dropbox Application Key
    app_key =

    # Dropbox Application Password
    app_secret =

.. note:: Edit the configuration by running the command ``pibooth --config``.

Picture URL
-----------

Uploaded picture URL is set to ``app.previous_picture_url`` attribute at the end of
`processing` state (``state_processing_exit`` hook).

.. warning:: for security reason, URL will expire in 4 hours.

Grant secured access
--------------------

Access to a Dropbox is granted by an APP_KEY and an APP_SECRET that shall be defined
in the configuration. These are not your Dropbox credentials and it can not be used
by an other application than the one defined in Dropbox.com.

===========  ==================================================================
 |step1|     `Go to Dropbox App Console <https://www.dropbox.com/developers/apps>`_
             and click on ``the Create app button``.

 |step2|     Under Choose an API section, select Scoped Access.
             Under Choose the type of access you need, select Full Dropbox.
             Enter a application name (for instance **My Awsome Photo Booth**).

 |step3|     Click the Create app button. You will be redirected to the console
             for your app. Note the presence of your App key and App secret on
             this page (not pictured). You will need to enter these into **pibooth**
             configuration file once you have followed the remaining steps.

 |step4|     Add the OAuth Redirect URI ``http://localhost:35880/`` to your
             Dropbox app settings under the OAuth2 Redirect URIs section.

 |step5|     Click on the **Permissions tab** then select the ``files.content.write``
             and ``files.content.read`` permissions in order to allow **pibooth**
             to upload pictures on your Dropbox. Finally **click the Submit button**
             at the bottom of the page for the new permissions to take effect.
===========  ==================================================================

.. note:: At the first connection, allow ``pibooth`` to use `Dropbox`_ in
          the opened web browser window.


.. --- Links ------------------------------------------------------------------

.. _`pibooth`: https://pypi.org/project/pibooth

.. _`Dropbox`: https://www.dropbox.com

.. |PythonVersions| image:: https://img.shields.io/badge/python-3.6+-red.svg
   :target: https://www.python.org/downloads
   :alt: Python 3.6+

.. |PypiPackage| image:: https://badge.fury.io/py/pibooth-dropbox.svg
   :target: https://pypi.org/project/pibooth-dropbox
   :alt: PyPi package

.. |Downloads| image:: https://img.shields.io/pypi/dm/pibooth-dropbox?color=purple
   :target: https://pypi.org/project/pibooth-dropbox
   :alt: PyPi downloads

.. --- Tuto -------------------------------------------------------------------

.. |step1| image:: https://github.com/pibooth/pibooth-dropbox/blob/master/docs/images/step1_create_button.png?raw=true
   :width: 80 %
   :alt: step1_create_button

.. |step2| image:: https://github.com/pibooth/pibooth-dropbox/blob/master/docs/images/step2_project_name.png?raw=true
   :width: 80 %
   :alt: step2_project_name

.. |step3| image:: https://github.com/pibooth/pibooth-dropbox/blob/master/docs/images/step3_display_name.png?raw=true
   :width: 80 %
   :alt: step3_display_name

.. |step4| image:: https://github.com/pibooth/pibooth-dropbox/blob/master/docs/images/step4_app_type.png?raw=true
   :width: 80 %
   :alt: step4_app_type

.. |step5| image:: https://github.com/pibooth/pibooth-dropbox/blob/master/docs/images/step5_download.png?raw=true
   :width: 80 %
   :alt: step5_download
