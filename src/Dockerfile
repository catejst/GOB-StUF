FROM amsterdam/python:3.7.2-stretch
MAINTAINER datapunt@amsterdam.nl

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

# Install StUF service in /app folder
WORKDIR /app

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

# Gatekeeper
COPY ./keycloak-gatekeeper.latest keycloak-gatekeeper
COPY ./gatekeeper.conf gatekeeper.conf
RUN chmod 755 keycloak-gatekeeper
RUN mkdir -p /var/log/gatekeeper

# Create downloaded dir for regression tests with correct permissions
RUN mkdir -p /app/gobstuf/regression_tests/downloaded
RUN chown datapunt /app/gobstuf/regression_tests/downloaded

USER datapunt

CMD ["/deploy/docker-run.sh"]
