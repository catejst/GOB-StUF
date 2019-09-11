# GOB-StUF

GOB StUF provides for StUF access

It serves as a proxy and transparantly forwards request to a StUF server.

# Requirements

    * docker-compose >= 1.17
    * docker ce >= 18.03
    * python = 2.7
    
# Installation

## Local

Create a virtual environment:

    virtualenv env
    source venv/bin/activate
    pip install -r src/requirements.txt
    
Or activate the previously created virtual environment

    source venv/bin/activate

Start the StUF service

```
    cd src
    python -m gobstuf
```

The service is default exposed at:
- http://127.0.0.1:8144/

The IP address of the server is also reported at stdout when starting the API from the command line

## Environment

The StUF service needs to be configured using environment variables:

- GOB_STUF_PORT  
  The port at which the service listens for requests
- ROUTE_PATH  
  The path that is simulated by the StUF service
- ROUTE_SCHEME  
  The scheme of the simulated path, normally https
- ROUTE_NETLOC  
  The domain of the simulated path
- PKCS12_FILENAME  
  The file where the certificate is stored
- PKCS12_PASSWORD  
  The password for the certificate file

The environment variables should be stored in a .env file.
An example can be found in .env.example.

The variables can be set using:

```bash
export $(cat .env | xargs)
```

### Tests

```bash
    cd src
    sh test.sh
```

## Docker

```bash
    docker-compose build
    docker-compose up
```

The API is exposed at the same address as for the local installation.

### Tests

```bash
    docker-compose -f src/.jenkins/test/docker-compose.yml build
    docker-compose -f src/.jenkins/test/docker-compose.yml run --rm test
```
