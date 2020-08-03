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
# In this repository
python -m gobstuf.regression_tests.brp
```

## How they work
The tests are defined on the GOB Objectstore per environment (development/acceptatie/productie).
In the directory of each environment you will find a directory `regression_tests`, which contains a
subdirectory `expected` and a file `testcases.csv`.

The testcases are read from `testcases.csv`. Each line contains an id, description and endpoint. For
each line the endpoint is requested and the response is compared to the expected response in the
`expected` directory; these expected files are named after their id. So for the test with id 1 there
is a file `1.json` in the `expected` directory.