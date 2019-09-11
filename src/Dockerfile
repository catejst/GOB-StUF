FROM amsterdam/docker_python:latest
MAINTAINER datapunt@amsterdam.nl

# Install StUF service in /app folder
WORKDIR /app

# Install required Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

# Copy gob stuf module
COPY gobstuf gobstuf

CMD uwsgi
