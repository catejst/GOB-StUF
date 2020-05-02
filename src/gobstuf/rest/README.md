# REST endpoints

## BRP
The BRP endpoints forward the API endpoint request as a StUF message to MKS. The ```StufRestView``` in
```brp/base_view.py``` contains all the logic to handle a GET request. ```StufRestView``` should be extended to define
a new resource. The child should define a request_template and response_template that define the message formats
sent to and received from MKS.

A request to a BRP endpoint should always contain the following headers for authorisation with MKS:
- MKS_GEBRUIKER
- MKS_APPLICATIE

When a StufRestView child receives a GET request, it:
1. Creates a StufRequest object, encapsulating the StUF request message.
2. Makes a request to MKS
3. Creates a StufResponse object from the StUF message received from MKS
4. Maps the StufResponse object to a HAL JSON response, which is then returned.

### Adding a new endpoint
This setup makes it possible to easily define a new resource with MKS mapping by:
- extending the ```StufRestView```
- creating a ```StufRequest``` as the request_template
- creating a ```StufResponse``` as the response_template
Don't forget to add the route to ```rest/brp/routes.py``` and you're done.

More on the ```StufRequest``` and ```StufResponse``` objects [here](../stuf/brp/README.md)

### Existing endpoints:

####/brp/ingeschrevenpersonen/[bsn]

Returns person for supplied BSN.

```
curl -H "MKS_APPLICATIE:<applicatie>" -H "MKS_GEBRUIKER:<gebruiker>" http(s)://<API>/brp/ingeschrevenpersonen/<BSN>
```

The API returns data in the same format as the 
[Haal-Centraal-BRP API](https://github.com/VNG-Realisatie/Haal-Centraal-BRP-bevragen/blob/master/docs/getting-started.md)

In order to use this API you need an API key.

An example that uses the Haal-Centraal-API is:
```
curl -H "x-api-key: <api key>" https://www.haalcentraal.nl/haalcentraal/api/brp/ingeschrevenpersonen/999993847
```

# Differences with the Haal-Centraal BRP API

If any differences exist between this REST API and the Haal-Centraal BRP API the following procedure will be followed:

![Haal-Centraal conformity](/assets/when_diffs_found.png "Haal-Centraal BRP API conformity")
