FROM amsterdam/python:3.9-buster
MAINTAINER datapunt@amsterdam.nl

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

# Install StUF service in /app folder
WORKDIR /app

RUN apt-get install -y apt-transport-https

# Install SQL Server driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Install GDAL
RUN apt-get install -y libgdal-dev

# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Install required Python packages
COPY requirements.txt /app/
RUN pip3 install --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY *.crt /usr/local/share/ca-certificates/extras/
RUN chmod -R 644 /usr/local/share/ca-certificates/extras/ \
 && update-ca-certificates

# Create directory for client certs
RUN mkdir -p /certs/gob/ && chmod -R 755 /certs

# Copy gob stuf module
COPY gobstuf gobstuf

# Copy deploy dir
COPY deploy /deploy/

# OAuth2 Proxy
COPY ./oauth2-proxy oauth2-proxy
COPY ./oauth2-proxy.cfg oauth2-proxy.cfg
RUN chmod 755 oauth2-proxy
RUN mkdir -p /var/log/oauth2-proxy && chown datapunt /var/log/oauth2-proxy

# Create downloaded dir for regression tests with correct permissions
RUN mkdir -p /app/gobstuf/regression_tests/downloaded
RUN chown datapunt /app/gobstuf/regression_tests/downloaded

USER datapunt

CMD ["/deploy/docker-run.sh"]
