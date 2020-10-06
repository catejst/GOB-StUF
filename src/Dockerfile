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

# Copy gob stuf module
COPY gobstuf gobstuf

# Copy deploy dir
COPY deploy /deploy/

# Gatekeeper
COPY ./keycloak-gatekeeper.latest keycloak-gatekeeper
COPY ./gatekeeper.conf gatekeeper.conf
RUN chmod 755 keycloak-gatekeeper
RUN mkdir -p /var/log/gatekeeper

USER datapunt

CMD ["/deploy/docker-run.sh"]
