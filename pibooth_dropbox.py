# -*- coding: utf-8 -*-

"""Pibooth plugin to upload pictures on Dropbox."""

import contextlib
import datetime
import os.path
import time
import dropbox

import pibooth
from pibooth.utils import LOGGER

__version__ = "0.0.1"


SECTION = 'DROPBOX'


@pibooth.hookimpl
def pibooth_configure(cfg):
    """Declare the new configuration options"""
    cfg.add_option(SECTION, 'album_name', "Pibooth",
                   "Dropbox folder where pictures are uploaded. Subfolders can be separated by /",
                   "Folder name", "Pibooth")
    cfg.add_option(SECTION, 'token', '',
                   "Refresh-Token for the dropbox api")
    cfg.add_option(SECTION, 'app_key', '',
                   "Dropbox Application Key")
    cfg.add_option(SECTION, 'app_secret', '',
                   "Dropbox Application Password")


@pibooth.hookimpl
def pibooth_startup(app, cfg):
    """Create the Dropbox upload instance."""

    get_config_options(app, cfg)
    LOGGER.debug("Starting Dropbox init")

    app.previous_picture_url = None
    client_id_token = app.dropbox_token

    if not client_id_token:
        LOGGER.debug("No token defined in [DROPBOX][token], upload deactivated")
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

    LOGGER.debug("Dropbox init done")


@pibooth.hookimpl
def state_processing_exit(app, cfg):
    """Upload picture to dropbox folder"""
    if hasattr(app, 'dropbox') and app.dbx is not None:

        get_config_options(app, cfg)

        result = app.dropbox.upload(app.dbx, app.previous_picture_file, app.dropbox_album_name,
                                    os.path.basename(app.previous_picture_file))

        if result is not None:
            app.previous_picture_url = app.dropbox.get_temp_link(app.dbx, result.path_lower)
        else:
            app.previous_picture_url = None


class dropboxApi(object):

    def upload(self, dbx, fullname, folder, name, overwrite=False):
        """Upload a file.
        Return the request response, or None in case of error.
        """
        LOGGER.debug('fullname -> %s', fullname)
        LOGGER.debug('folder -> %s', folder)
        LOGGER.debug('name -> %s', name)

        path = '/%s/%s' % (folder, name)
        LOGGER.debug('path -> %s', path)

        while '//' in path:
            path = path.replace('//', '/')
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        mtime = os.path.getmtime(fullname)

        with open(fullname, 'rb') as fd:
            data = fd.read()

        with stopwatch('upload %d bytes' % len(data)):
            try:
                res = dbx.files_upload(
                    data, path, mode,
                    client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                    mute=True)
            except dropbox.exceptions.ApiError:
                LOGGER.error('*** Dropbox API error', exc_info=True)
                return None

        LOGGER.debug('Pploaded as %s', res.name.encode('utf8'))
        return res

    def get_temp_link(self, dbx, path):
        """ Get the temporary link for the picture. Link is valid 4 hours only. """
        res = dbx.files_get_temporary_link(path)
        LOGGER.debug('dropbox temp picture path -> %s', res.link)
        return res.link


def get_config_options(app, cfg):
    """ Read options at each hook. Options can change at runtime """

    app.dropbox_album_name = cfg.get(SECTION, 'album_name')
    app.dropbox_token = cfg.get(SECTION, 'token')
    app.dropbox_app_key = cfg.get(SECTION, 'app_key')
    app.dropbox_app_secret = cfg.get(SECTION, 'app_secret')

    LOGGER.debug("Dropbox album_name -> %s", app.dropbox_album_name)
    LOGGER.debug("Dropbox token -> %s", app.dropbox_token)
    LOGGER.debug("Dropbox app_key -> %s", app.dropbox_app_key)
    LOGGER.debug("Dropbox app_secret -> %s", app.dropbox_app_secret)


@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        LOGGER.debug('Total elapsed time for %s: %.3f', message, t1 - t0)
