# -*- coding: utf-8 -*-

"""Pibooth plugin to upload pictures on Dropbox."""

import contextlib
import datetime
import os.path
import sys
import time
import dropbox

import pibooth
from pibooth.utils import LOGGER

if sys.version.startswith('2'):
    input = raw_input  # noqa: E501,F821; pylint: disable=redefined-builtin,undefined-variable,useless-suppression

__version__ = "0.0.1"

SECTION = 'DROPBOX'
ZEROONE = ['0', '1']


@pibooth.hookimpl
def pibooth_configure(cfg):
    """Declare the new configuration options"""
    cfg.add_option(SECTION, 'db_album_name', "Pibooth",
                   "Dropbox folder where pictures are uploaded. Subfolders can be separated by /",
                   "Folder name", "Pibooth")
    cfg.add_option(SECTION, 'db_token', '',
                   "Refresh-Token for the dropbox api")
    cfg.add_option(SECTION, 'db_app_key', '',
                   "Dropbox Application Key")
    cfg.add_option(SECTION, 'db_app_secret', '',
                   "Dropbox Application Password")
    cfg.add_option(SECTION, 'db_debug', '0',
                   "Dropbox Debug Mode {}".format(', '.join(ZEROONE)),
                   "Debug Mode (0 or 1)", ZEROONE)


@pibooth.hookimpl
def pibooth_startup(app, cfg):
    """Create the Dropbox upload instance."""

    get_config_options(app, cfg)

    if app.dropbox_debug == 1 or app.dropbox_debug == "1":
        LOGGER.info("Starting Dropbox init")

    app.previous_picture_url = None
    client_id_token = app.dropbox_token

    if not client_id_token:
        LOGGER.debug("No token defined in [DROPBOX][db_token], upload deactivated")
        app.dbx = None
    else:
        try:
            app.dropbox = dropboxApi()
            app.dbx = dropbox.Dropbox(
                app_key=app.dropbox_app_key,
                app_secret=app.dropbox_app_secret,
                oauth2_refresh_token=client_id_token
            )
        except:
            LOGGER.debug('Dropbox Api initialization error, upload deactivated!')
            app.dbx = None

    if app.dropbox_debug == 1 or app.dropbox_debug == "1":
        LOGGER.info("Dropbox init done")


@pibooth.hookimpl
def state_processing_exit(app, cfg):
    """Upload picture to dropbox folder"""
    if hasattr(app, 'dropbox') and app.dbx != None:

        get_config_options(app, cfg)

        result = app.dropbox.upload(app.dbx, app.previous_picture_file, app.dropbox_album_name,
                                    os.path.basename(app.previous_picture_file), app.dropbox_debug)

        if result != None:
            app.previous_picture_url = app.dropbox.get_temp_link(app.dbx, result.path_lower, app.dropbox_debug)
        else:
            app.previous_picture_url = None


class dropboxApi(object):

    def upload(self, dbx, fullname, folder, name, debugmode, overwrite=False):
        """Upload a file.
        Return the request response, or None in case of error.
        """

        if debugmode == 1 or debugmode == "1":
            LOGGER.info('fullname -> ' + fullname)
            LOGGER.info('folder -> ' + folder)
            LOGGER.info('name -> ' + name)

        path = '/%s/%s' % (folder, name)

        if debugmode == 1 or debugmode == "1":
            LOGGER.info('path -> ' + path)

        while '//' in path:
            path = path.replace('//', '/')
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        mtime = os.path.getmtime(fullname)
        with open(fullname, 'rb') as f:
            data = f.read()
        with stopwatch('upload %d bytes' % len(data)):
            try:
                res = dbx.files_upload(
                    data, path, mode,
                    client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                    mute=True)
            except dropbox.exceptions.ApiError as err:
                Logger.info('*** Dropbox API error', err)
                return None
        if debugmode == 1 or debugmode == "1":
            LOGGER.info('uploaded as {}'.format(res.name.encode('utf8')))

        return res

    def get_temp_link(self, dbx, path, debugmode):
        """ Get the temporary link for the picture. Link is valid 4 hours only. """

        res = dbx.files_get_temporary_link(path)

        if debugmode == 1 or debugmode == "1":
            LOGGER.info('dropbox temp picture path -> ' + res.link)

        return res.link


def get_config_options(app, cfg):
    """ Read options at each hook. Options can change at runtime """

    app.dropbox_album_name = cfg.get(SECTION, 'db_album_name')
    app.dropbox_token = cfg.get(SECTION, 'db_token')
    app.dropbox_app_key = cfg.get(SECTION, 'db_app_key')
    app.dropbox_app_secret = cfg.get(SECTION, 'db_app_secret')
    app.dropbox_debug = cfg.get(SECTION, 'db_debug')

    if app.dropbox_debug == 1 or app.dropbox_debug == "1":
        LOGGER.info("dropbox_album_name -> " + app.dropbox_album_name)
        LOGGER.info("dropbox_token -> " + app.dropbox_token)
        LOGGER.info("dropbox_app_key -> " + app.dropbox_app_key)
        LOGGER.info("dropbox_app_secret -> " + app.dropbox_app_secret)
        LOGGER.info("dropbox_debug -> " + app.dropbox_debug)


@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        LOGGER.info('Total elapsed time for %s: %.3f' % (message, t1 - t0))
