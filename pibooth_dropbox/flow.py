

import json
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import webbrowser
import wsgiref.simple_server
import wsgiref.util

from dropbox import DropboxOAuth2Flow


class Credentials(object):

    _PROPERTIES = ("token",
                   "refresh_token",
                   "token_uri",
                   "account_id",
                   "client_id",
                   "scopes")

    def __init__(self, token, refresh_token, token_uri, account_id,
                 client_id, scopes, expires_at=None):
        self.token = token
        self.refresh_token = refresh_token
        self.token_uri = token_uri
        self.account_id = account_id
        self.client_id = client_id
        if isinstance(scopes, (list, tuple)):
            self.scopes = ' '.join(scopes)
        else:
            self.scopes = scopes
        self.expires_at = expires_at

    @classmethod
    def from_oauth2_flow_result(cls, result):
        """Return a :py:class:`Credentials` instance from OAuth2 flow result.
        """
        return cls(result.access_token, result.refresh_token, result.url_state,
                   result.account_id, result.user_id, result.scope, result.expires_at)

    @classmethod
    def from_authorized_user_file(cls, filename):
        """Return a :py:class:`Credentials` instance from json file.
        """
        with open(filename, 'r') as fp:
            return cls(**json.load(fp))

    def to_json(self, strip=None):
        """Utility function that creates a JSON representation of a Credentials
        object.

        :param strip: Optional list of members to exclude from the generated JSON.
        :type strip: list

        :returns: A JSON representation of this instance, suitable to write in file.
        """
        prep = dict((k, getattr(self, k)) for k in Credentials._PROPERTIES)

        # Remove entries that explicitely need to be removed
        if strip is not None:
            prep = {k: v for k, v in prep.items() if k not in strip}

        # Save scopes has list
        prep["scopes"] = prep["scopes"].split(' ')

        return json.dumps(prep)


class InstalledAppFlow(object):
    """Authorization flow helper for installed applications.

    This class makes it easier to perform the `Installed Application Authorization Flow`.
    This flow is useful for local development or applications that are installed
    on a desktop operating system.

    Note that these aren't the only ways to accomplish the installed application
    flow, it is just the most common way.
    """

    _DEFAULT_AUTH_PROMPT_MESSAGE = (
        "Please visit this URL to authorize this application: {url}"
    )
    _DEFAULT_WEB_SUCCESS_MESSAGE = (
        "The authentication flow has completed. You may close this window."
    )

    def __init__(self, app_key, app_secret, scopes=None, client_type='offline'):
        self.app_key = app_key
        self.app_secret = app_secret
        self.client_type = client_type
        self.scopes = scopes
        self.redirect_uri = None

    def fetch_token(self, uri, state=None):
        """Parse authorization grant response URI into a dict.

        If the resource owner grants the access request, the authorization
        server issues an authorization code and delivers it to the client by
        adding the following parameters to the query component of the
        redirection URI using the ``application/x-www-form-urlencoded`` format:

        **code**
                REQUIRED.  The authorization code generated by the
                authorization server.  The authorization code MUST expire
                shortly after it is issued to mitigate the risk of leaks.  A
                maximum authorization code lifetime of 10 minutes is
                RECOMMENDED.  The client MUST NOT use the authorization code
                more than once.  If an authorization code is used more than
                once, the authorization server MUST deny the request and SHOULD
                revoke (when possible) all tokens previously issued based on
                that authorization code.  The authorization code is bound to
                the client identifier and redirection URI.

        **state**
                REQUIRED if the "state" parameter was present in the client
                authorization request.  The exact value received from the
                client.

        :param uri: The full redirect URL back to the client.
        :param state: The state parameter from the authorization request.
        """
        query = urlparse.urlparse(uri).query
        params = dict(urlparse.parse_qsl(query))

        if state and params.get('state', None) != state:
            raise ValueError("State are not matching")

        if 'error' in params:
            raise ValueError(params.get('error'), params)

        if 'code' not in params:
            raise ValueError("Missing code parameter in response")

        return params

    def run_local_server(self, host="localhost", port=8080,
                         authorization_prompt_message=_DEFAULT_AUTH_PROMPT_MESSAGE,
                         success_message=_DEFAULT_WEB_SUCCESS_MESSAGE,
                         open_browser=True):
        """Run the flow using the server strategy.

        The server strategy instructs the user to open the authorization URL in
        their browser and will attempt to automatically open the URL for them.
        It will start a local web server to listen for the authorization
        response. Once authorization is complete the authorization server will
        redirect the user's browser to the local web server. The web server
        will get the authorization code from the response and shutdown. The
        code is then exchanged for a token.

        :param host: The hostname for the local redirect server. This will
                be served over http, not https.
        :type host: str
        :param port: The port for the local redirect server.
        :type port: int
        :param authorization_prompt_message: The message to display to tell the
            user to navigate to the authorization URL.
        :type authorization_prompt_message: str
        :param success_message: The message to display in the web browser
            the authorization flow is complete.
        :type success_message: str
        :param open_browser: Whether or not to open the authorization URL in the
            user's browser.
        :type open_browser: bool

        :returns: Credentials: The OAuth 2.0 credentials for the user.
        """
        wsgi_app = _RedirectWSGIApp(success_message)
        # Fail fast if the address is occupied
        wsgiref.simple_server.WSGIServer.allow_reuse_address = False
        local_server = wsgiref.simple_server.make_server(
            host, port, wsgi_app, handler_class=_WSGIRequestHandler
        )

        self.redirect_uri = "http://{}:{}/".format(host, local_server.server_port)
        print("Go on https://www.dropbox.com/developers/apps/info and set Redirect URI to ",
              self.redirect_uri)

        session = {}
        flow = DropboxOAuth2Flow(self.app_key,
                                 self.redirect_uri,
                                 session,
                                 "dropbox-auth-csrf-token",
                                 self.app_secret,
                                 token_access_type=self.client_type)
        auth_url = flow.start()

        if open_browser:
            webbrowser.open(auth_url, new=1, autoraise=True)

        print(authorization_prompt_message.format(url=auth_url))

        local_server.handle_request()

        # Note: using https here because oauthlib is very picky that
        # OAuth 2.0 should only occur over https.
        authorization_response = wsgi_app.last_request_uri
        result = flow.finish(self.fetch_token(authorization_response))

        # This closes the socket
        local_server.server_close()

        return Credentials.from_oauth2_flow_result(result)


class _WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    """Custom WSGIRequestHandler.

    Uses a named logger instead of printing to stderr.
    """

    def log_message(self, format, *args):
        # pylint: disable=redefined-builtin
        # (format is the argument name defined in the superclass.)
        print(format, *args)


class _RedirectWSGIApp(object):
    """WSGI app to handle the authorization redirect.

    Stores the request URI and displays the given success message.
    """

    def __init__(self, success_message):
        """
        :param success_message: The message to display in the web browser
            the authorization flow is complete.
        :type success_message: str
        """
        self.last_request_uri = None
        self._success_message = success_message

    def __call__(self, environ, start_response):
        """WSGI Callable.

        :param environ: The WSGI environment.
        :type environ: dict
        :param start_response: The WSGI start_response callable.
        :type start_response: callable

        :returns: The response body.
        :rtype: list
        """
        start_response("200 OK", [("Content-type", "text/plain")])
        self.last_request_uri = wsgiref.util.request_uri(environ)
        return [self._success_message.encode("utf-8")]
