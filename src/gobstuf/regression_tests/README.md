# BRP Regression tests

## How to run
There are two ways to run the regression tests. By placing a message on the message queue, so that all
logging ends up nicely in the management database and Iris:

```bash
# In gobworkflow
python -m gobworkflow.start brp_regression_test 
```

Or directly from this repository, so that we don't need the complete GOB environment to be
set up, and the tests run quicker during development:

```bash
# In this repository. Point BRP_REGRESSION_TEST_LOCAL_PORT to 8165, the external Docker port (see .env.example)
python -m gobstuf.regression_tests
```

Note: To run the regression tests locally, the GOB-StUF service should be running within Docker, with Gatekeeper
enabled. See `docker-compose.yml` for instructions.

## How they work
The tests are defined on the GOB Objectstore per environment (development/acceptatie/productie).
In the directory of each environment you will find a directory `regression_tests`, which contains a
subdirectory `expected` and a file `testcases.csv`.

The testcases are read from `testcases.csv`. Each line contains an id, description, endpoint and username. For
each line the endpoint is requested and the response is compared to the expected response in the
`expected` directory; these expected files are named after their id. So for the test with id 1 there
is a file `1.json` in the `expected` directory. The username on each line defines which user the test to run with,
as this may impact the response. See Authorisation for more information.


## Authorisation
For each test case, the Keycloak user to run the test with should be defined. An environment variable with the
user's password should be defined as well. To find the environment variable with the user's password, 
the username is capitalised and prefixed with USER_PASSWORD_ to find the correct environment variabled.
For example, when the user for a certain testcase is 'sinterklaas', an environment variable named 
USER_PASSWORD_SINTERKLAAS should be defined, holding the password.
