# GOB-StUF

GOB StUF provides for StUF access

It serves as a proxy and transparantly forwards requests to a StUF server

# Requirements

    * docker-compose >= 1.17
    * docker ce >= 18.03
    * python >= 3.6
    
# Notes

* Both a certificate and a VPN are required to access the underlying StUF service.

* [SoapUI](https://www.soapui.org) can be used to test the StUF service.

The service definition that is exposed is:
```
http://localhost:<<GOB_STUF_PORT>><<ROUTE_NETLOC>>?wsdl
```
eg:
```
http://localhost:8165/SomePath/MijnService?wsdl
```

The StUF endpoint is reported at startup of the service.
    
# Installation

## Local

Create a virtual environment:

```
virtualenv env
source venv/bin/activate
pip install -r src/requirements.txt
```
    
Or activate the previously created virtual environment

```
source venv/bin/activate
```

Set the environment variables (see also next paragraph)

```
export $(cat .env | xargs)
```

Start the StUF service

```
cd src
python -m gobstuf
```

The service is default exposed at:
- http://127.0.0.1:8165/

The IP address of the server is also reported at stdout on startup the API

## Environment

The StUF service needs to be configured using environment variables:

- ROUTE_SCHEME  
  The scheme of the proxied path, default https
- ROUTE_NETLOC
  The domain of the proxied path
- ROUTE_PATH
  The path that is proxied by the StUF service
- PKCS12_FILENAME  
  The file where the certificate is stored
- PKCS12_PASSWORD
  The password for the certificate file
- GOB_STUF_PORT
  The port at which the service listens for requests, default 8165

The environment variables should be stored in a .env file (included in .gitignore)

An example can be found in .env.example.
The example connects to a public number conversion soap service

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
