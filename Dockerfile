FROM mambaorg/micromamba:1.5.6
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
USER root
WORKDIR /app
#ADD ms_setup/odbcinst.ini /etc/odbcinst.ini


# apt-get and system utilities
RUN apt-get update && apt-get install -y  curl apt-utils apt-transport-https debconf-utils
RUN apt-get install -y gcc build-essential g++-7

#RUN apt-get install -y tdsodbc unixodbc-dev
RUN apt-get install -y iputils-ping
#RUN apt install unixodbc -y
RUN apt-get clean -y


RUN rm -rf /var/lib/apt/lists/*

# adding custom Microsoft repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/18.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# install SQL Server drivers
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# install SQL Server tools
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y mssql-tools
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
RUN /bin/bash -c "source ~/.bashrc"


# install necessary locales, this prevents any locale errors related to Microsoft packages
RUN apt-get update && apt-get install -y locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen

USER $MAMBA_USER

RUN micromamba create -y -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1

WORKDIR /code/load_data


