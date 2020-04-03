# Configuration file for jupyterhub.

c.JupyterHub.port = 9443
# will automatically redirect to JupyterLab
c.Spawner.default_url = '/lab'
c.JupyterHub.admin_users = {'jupyterhub_admin'}
c.JupyterHub.authenticator_class = 'jupyterhub.auth.PAMAuthenticator'
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
c.LocalAuthenticator.create_system_users = False
# allow only users in the developers system group
c.LocalAuthenticator.group_whitelist = {'developers'}
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
