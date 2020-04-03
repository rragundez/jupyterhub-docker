# image used in Amazon Linux 2 AMI (HVM)
# so whatever cutomization runs here should run on top of that AMI
# then we can save that customized AMI as another AMI from where
# we can start the EC2 instances.
FROM amazonlinux:latest

# redundant but to stress that commands need to be ran as root or with sudo
USER root

RUN yum update -y \
  && yum install -y \
  sudo \
  epel-release \
  python-pip \
  git \
  wget \
  tree \
  bash-completion \
  && pip install --upgrade awscli

ARG MINICONDA_PATH=/opt/miniconda
ARG CONDA=$MINICONDA_PATH/bin/conda
# TODO: Get python env name from the environment.yml file
ARG PYTHON_ENV_NAME=python3.7
ARG PYTHON=$MINICONDA_PATH/envs/$PYTHON_ENV_NAME/bin/python
ARG KERNEL=/usr/local/share/jupyter/kernels/$PYTHON_ENV_NAME
ARG ENVIRONMENT_YML_FILE=environment.yml

COPY $ENVIRONMENT_YML_FILE /tmp/environment.yml

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
  && bash /tmp/miniconda.sh -b -p $MINICONDA_PATH \
  && $CONDA update conda -y \
  && $CONDA env create --file /tmp/environment.yml \
  && $PYTHON -m ipykernel install --name $PYTHON_ENV_NAME --display-name="AA Factory $PYTHON_ENV_NAME" \
  && $CONDA install notebook -y \
  && $CONDA install -c conda-forge jupyterhub jupyterlab -y \
  && $MINICONDA_PATH/bin/python -m jupyter kernelspec remove -f python3 \
  && $MINICONDA_PATH/bin/python -m pip uninstall ipykernel -y \
  && $CONDA clean --all -y \
  && bash -c "echo PATH=$PATH:$MINICONDA_PATH/bin >> /etc/profile"

ARG HOME=/home/jupyterhub
ARG JUPYTERHUB_ADMIN_USER=admin

# the group developer will be the only one allowed in JupyterHub
RUN groupadd --gid 501 developers \
  && mkdir -p $HOME \
  && useradd -m -d $HOME/$JUPYTERHUB_ADMIN_USER --uid 502 -s /bin/bash -N $JUPYTERHUB_ADMIN_USER \
  && echo "$JUPYTERHUB_ADMIN_USER:admin" | chpasswd \
  && usermod -a -G developers $JUPYTERHUB_ADMIN_USER
RUN sudo -u $JUPYTERHUB_ADMIN_USER bash -c "mkdir -p $HOME/$JUPYTERHUB_ADMIN_USER/.aws" \
  && if ! grep -q "source activate $PYTHON_ENV_NAME" $HOME/$JUPYTERHUB_ADMIN_USER/.bashrc; then sudo -u $JUPYTERHUB_ADMIN_USER bash -c "echo source activate $PYTHON_ENV_NAME >> $HOME/$JUPYTERHUB_ADMIN_USER/.bashrc"; fi


ARG JUPYTERHUB_CONFIG_FILE=jupyterhub_config.py

COPY $JUPYTERHUB_CONFIG_FILE jupyterhub_config.py

RUN mkdir -p /etc/jupyter/conf \
  && mv jupyterhub_config.py /etc/jupyter/conf/jupyterhub_config.py

EXPOSE 9443
ENV PATH=$PATH:$MINICONDA_PATH/bin
ENV SPARK_HOME=/usr/lib/spark
ENV PYSPARK_DRIVER_PYTHON=$MINICONDA_PATH/envs/$PYTHON_ENV_NAME/bin/python
ENV PYSPARK_PYTHON=$MINICONDA_PATH/envs/$PYTHON_ENV_NAME/bin/python
CMD ["jupyterhub", "-f", "/etc/jupyter/conf/jupyterhub_config.py"]

# if it is as a service
# COPY jupyterhub.service /etc/systemd/system/jupyterhub.service








