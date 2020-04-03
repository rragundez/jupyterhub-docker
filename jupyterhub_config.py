import os

"""
Custom Authenticator to use Azure AD with JupyterHub
"""

import json
import jwt
import os
import urllib
import subprocess
import pwd

from tornado.auth import OAuth2Mixin
from tornado.log import app_log
from tornado.httpclient import HTTPRequest, AsyncHTTPClient

from jupyterhub.auth import LocalAuthenticator

from traitlets import Unicode, default

from oauthenticator.oauth2 import OAuthLoginHandler, OAuthenticator

from oauthenticator.azuread import AzureAdOAuthenticator


class MyOAutehnticator(AzureAdOAuthenticator):
    async def authenticate(self, handler, data=None):
        userdict = await super().authenticate(handler, data)
        userdict['name'] = userdict['name'].split('@')[0].replace('.', '_')
        return userdict


def pre_spawn_hook(spawner):
    username = spawner.user.name
    try:
        pwd.getpwnam(username)
    except KeyError:
        subprocess.check_call(
            ['useradd', '-ms', '/bin/bash', '-N', username]
        )

# Configuration file for jupyterhub.
c.JupyterHub.port = 9443
# will automatically redirect to JupyterLab
c.Spawner.default_url = '/lab'
# c.JupyterHub.authenticator_class = 'jupyterhub.auth.PAMAuthenticator'
c.JupyterHub.authenticator_class = MyOAutehnticator
c.JupyterHub.cookie_max_age_days = 1
c.KernelSpecManager.ensure_native_kernel = False
# Set the log level by value or name.
c.JupyterHub.log_level = 'INFO'
# logging of the single-user server
c.Spawner.debug = False
# write JupyterHub DB to a non-persistent storage location
# this means that on every EMR start-up users will need to
# login again. There is no state being kept between clusters.
c.JupyterHub.db_url = '/etc/jupyter/conf/jupyterhub.sqlite'
# put the log file in /var/log
c.JupyterHub.extra_log_file = '/var/log/jupyterhub.log'
# Azure active directory integration
c.Spawner.pre_spawn_hook = pre_spawn_hook
c.AzureAdOAuthenticator.username_claim = "email"
c.AzureAdOAuthenticator.tenant_id = os.environ.get('AAD_TENANT_ID')
c.AzureAdOAuthenticator.oauth_callback_url = os.environ.get('AAD_OAUTH_CALLBACK_URL')
c.AzureAdOAuthenticator.client_id = os.environ.get('AAD_CLIENT_ID')
c.AzureAdOAuthenticator.client_secret = os.environ.get('AAD_CLIENT_SECRET')
# whitelist of environment variables for the single-user server
# to inherit from the JupyterHub process.
# JupyterHub blocks many environment variables by default
# but PySpark needs this environment variable to run on top
# of the correct Spark setup using YARN. If not it will
# start as standalone.
c.Spawner.env_keep = [
    'SPARK_HOME',
    'PYSPARK_DRIVER_PYTHON',
    'PYSPARK_PYTHON'
]
c.Spawner.cmd = '/opt/miniconda/bin/jupyterhub-singleuser'
