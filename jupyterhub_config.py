import os

"""
Custom Authenticator to use Azure AD with JupyterHub
"""

import json
import jwt
import os
import urllib

from tornado.auth import OAuth2Mixin
from tornado.log import app_log
from tornado.httpclient import HTTPRequest, AsyncHTTPClient

from jupyterhub.auth import LocalAuthenticator

from traitlets import Unicode, default

from oauthenticator.oauth2 import OAuthLoginHandler, OAuthenticator


class AzureAdOAuthenticator(OAuthenticator):
    login_service = Unicode(
		os.environ.get('LOGIN_SERVICE', 'Azure AD'),
		config=True,
		help="""Azure AD domain name string, e.g. My College"""
	)

    tenant_id = Unicode(config=True, help="The Azure Active Directory Tenant ID")

    @default('tenant_id')
    def _tenant_id_default(self):
        return os.environ.get('AAD_TENANT_ID', '')

    username_claim = Unicode(config=True)

    @default('username_claim')
    def _username_claim_default(self):
        return 'name'

    @default("authorize_url")
    def _authorize_url_default(self):
        return 'https://login.microsoftonline.com/{0}/oauth2/authorize'.format(self.tenant_id)

    @default("token_url")
    def _token_url_default(self):
        return 'https://login.microsoftonline.com/{0}/oauth2/token'.format(self.tenant_id)

    async def authenticate(self, handler, data=None):
        code = handler.get_argument("code")
        http_client = AsyncHTTPClient()

        params = dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            grant_type='authorization_code',
            code=code,
            redirect_uri=self.get_callback_url(handler))

        data = urllib.parse.urlencode(
            params, doseq=True, encoding='utf-8', safe='=')

        url = self.token_url

        headers = {
            'Content-Type':
            'application/x-www-form-urlencoded; charset=UTF-8'
        }
        req = HTTPRequest(
            url,
            method="POST",
            headers=headers,
            body=data  # Body is required for a POST...
        )

        resp = await http_client.fetch(req)
        resp_json = json.loads(resp.body.decode('utf8', 'replace'))

        # app_log.info("Response %s", resp_json)
        access_token = resp_json['access_token']

        id_token = resp_json['id_token']
        decoded = jwt.decode(id_token, verify=False)

        self.log.warning(decoded)
        username = "_".join(decoded[self.username_claim].split("@")[0].split("."))

        decoded[self.username_claim] = username

        userdict = {"name": username}
        userdict["auth_state"] = auth_state = {}
        auth_state['access_token'] = access_token
        # results in a decoded JWT for the user data
        auth_state['user'] = decoded

        return userdict


class LocalAzureAdOAuthenticator(LocalAuthenticator, AzureAdOAuthenticator):
    """A version that mixes in local system user creation"""
    pass

# Configuration file for jupyterhub.

c.JupyterHub.port = 9443
# will automatically redirect to JupyterLab
c.Spawner.default_url = '/lab'

c.JupyterHub.admin_users = {'admin'}
# c.JupyterHub.authenticator_class = 'jupyterhub.auth.PAMAuthenticator'
c.JupyterHub.authenticator_class = AzureAdOAuthenticator

c.JupyterHub.cookie_max_age_days = 1
c.KernelSpecManager.ensure_native_kernel = False
# Set the log level by value or name.
c.JupyterHub.log_level = 'INFO'
# logging of the single-user server
c.Spawner.debug = False
# jupyterhub opening PAM sessions
c.PAMAuthenticator.open_sessions = True
# write JupyterHub DB to a non-persistent storage location
# this means that on every EMR start-up users will need to
# login again. There is no state being kept between clusters.
c.JupyterHub.db_url = '/etc/jupyter/conf/jupyterhub.sqlite'
# put the log file in /var/log
c.JupyterHub.extra_log_file = '/var/log/jupyterhub.log'
# if True users in the machine can get created via JupyterHub
# which we do not want as we want to create them via
# script in the machine such that we control
# the user home setup.
c.LocalAuthenticator.create_system_users = True
# allow only users in the developers system group
c.LocalAuthenticator.group_whitelist = {'developers'}
# whitelist of environment variables for the single-user server
# to inherit from the JupyterHub process.
# JupyterHub blocks many environment variables by default
# but PySpark needs this environment variable to run on top
# of the correct Spark setup using YARN. If not it will
# start as standalone.

import subprocess
import pwd

def pre_spawn_hook(spawner):
    username = spawner.user.name
    try:
        pwd.getpwnam(username)
    except KeyError:
        subprocess.check_call(
            ['useradd', '-ms', '/bin/bash', '-N', '-G', 'developers', username]
        )

c.Spawner.pre_spawn_hook = pre_spawn_hook

c.AzureAdOAuthenticator.username_claim = "email"
c.AzureAdOAuthenticator.tenant_id = os.environ.get('AAD_TENANT_ID')
c.AzureAdOAuthenticator.oauth_callback_url = os.environ.get('AAD_OAUTH_CALLBACK_URL')
c.AzureAdOAuthenticator.client_id = os.environ.get('AAD_CLIENT_ID')
c.AzureAdOAuthenticator.client_secret = os.environ.get('AAD_CLIENT_SECRET')

c.Spawner.env_keep = [
    'SPARK_HOME',
    'PYSPARK_DRIVER_PYTHON',
    'PYSPARK_PYTHON'
]
c.Spawner.cmd = '/opt/miniconda/bin/jupyterhub-singleuser'
