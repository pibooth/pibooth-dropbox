# -*- coding: utf-8 -*-

import os
import time
import os.path
import datetime

import requests
import dropbox

import pibooth
from pibooth.utils import LOGGER, timeit
from pibooth_dropbox.flow import InstalledAppFlow, Credentials


SECTION = 'DROPBOX'
CACHE_FILE = '.dropbox_token.json'


@pibooth.hookimpl
def pibooth_configure(cfg):
    """Declare the new configuration options"""
    cfg.add_option(SECTION, 'album_name', "Pibooth",
                   "Dropbox folder where pictures are uploaded. Subfolders can be separated by /",
                   "Folder name", "Pibooth")
    cfg.add_option(SECTION, 'app_key', '',
                   "Dropbox Application Key")
    cfg.add_option(SECTION, 'app_secret', '',
                   "Dropbox Application Password")


@pibooth.hookimpl
def pibooth_reset(cfg, hard):
    """Remove cached token file."""
    if hard and os.path.isfile(cfg.join_path(CACHE_FILE)):
        LOGGER.info("Remove Dropbox autorizations '%s'", cfg.join_path(CACHE_FILE))
        os.remove(cfg.join_path(CACHE_FILE))


@pibooth.hookimpl
def pibooth_startup(app, cfg):
    """Create the Dropbox upload instance."""
    app.previous_picture_url = None

    if not cfg.get(SECTION, 'app_key') or not cfg.get(SECTION, 'app_secret'):
        LOGGER.debug("No credentials defined in [%s][token], upload deactivated", SECTION)
    else:
        LOGGER.info("Initialize Dropbox connection")
        app.dropbox = DropboxApi(cfg.get(SECTION, 'app_key'),
                                 cfg.get(SECTION, 'app_secret'),
                                 cfg.join_path(CACHE_FILE))


@pibooth.hookimpl
def state_processing_exit(app, cfg):
    """Upload picture to dropbox folder"""
    if hasattr(app, 'dropbox'):
        result = app.dropbox.upload(app.previous_picture_file,
                                    cfg.get(SECTION, 'album_name'),
                                    os.path.basename(app.previous_picture_file))

        if result is not None:
            app.previous_picture_url = app.dropbox.get_temp_url(result.path_lower)
        else:
            app.previous_picture_url = None


class DropboxApi(object):

    """Dropbox interface.

    APP_KEY and APP_SECRET are required to connect to Dropbox.

    A file ``token_file`` is generated at first run to store permanently the
    autorizations to use Dropbox API.

    :param app_key: application key
    :type app_key: str
    :param app_secret: application secret
    :type app_secret: str
    :param token_file: file where generated token will be stored
    :type token_file: str
    """

    SCOPES = ["account_info.read",
              "files.content.read",
              "files.content.write",
              "files.metadata.read"]

    def __init__(self, app_key, app_secret, token_file="token.json"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.token_cache_file = token_file
        if self.is_reachable():
            self._session = self._get_authorized_session()
        else:
            self._session = None

    def _auth(self):
        """Open browser to create credentials."""
        flow = InstalledAppFlow(self.app_key, self.app_secret, self.SCOPES)
        return flow.run_local_server(port=35880)

    def _save_credentials(self, credentials):
        """Save credentials in a file to use API without need to allow acces."""
        with open(self.token_cache_file, 'w') as fp:
            fp.write(credentials.to_json())

    def _get_authorized_session(self):
        """Create credentials file if required and open a new session."""
        credentials = None
        if not os.path.exists(self.token_cache_file) or \
                os.path.getsize(self.token_cache_file) == 0:
            credentials = self._auth()
            LOGGER.debug("First use of pibooth-dropbox: store token in file %s",
                         self.token_cache_file)
            try:
                self._save_credentials(credentials)
            except OSError as err:
                LOGGER.warning("Can not save Dropbox token in file '%s': %s",
                               self.token_cache_file, err)
        else:
            credentials = Credentials.from_authorized_user_file(self.token_cache_file)

        if credentials:
            return dropbox.Dropbox(app_key=self.app_key,
                                   app_secret=self.app_secret,
                                   oauth2_access_token=credentials.token,
                                   oauth2_refresh_token=credentials.refresh_token,
                                   oauth2_access_token_expiration=credentials.expires_at)
        return None

    def is_reachable(self):
        """Check if Dropbox is reachable."""
        try:
            return requests.head('https://www.dropbox.com').status_code == 200
        except requests.ConnectionError:
            return False

    def upload(self, fullname, folder, name, overwrite=False):
        """Upload a file.
        Return the request response, or None in case of error.
        """
        if not self.is_reachable():
            LOGGER.error("Dropbox upload failure: no internet connexion!")
            return

        if not self._session:
            # Plugin was disabled at startup but activated after
            self._session = self._get_authorized_session()

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

        with timeit('Upload %d bytes' % len(data)):
            try:
                res = self._session.files_upload(
                    data, path, mode,
                    client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                    mute=True)
            except dropbox.exceptions.ApiError:
                LOGGER.error('*** Dropbox API error', exc_info=True)
                return None

        LOGGER.debug('Uploaded as %s', res.name.encode('utf8'))
        return res

    def get_temp_url(self, path):
        """Get the temporary URL for the picture (valid 4 hours only).
        """
        try:
            res = self._session.files_get_temporary_link(path)
            LOGGER.debug('Temporary picture URL -> %s', res.link)
            return res.link
        except:
            LOGGER.error("Can not get temporary URL for Dropbox", exc_info=True)
            return None
