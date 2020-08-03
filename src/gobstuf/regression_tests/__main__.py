import logging
from gobstuf.regression_tests.brp import BrpRegression, ObjectstoreResultsWriter


def main():
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    results = BrpRegression(logger).run()
    writer = ObjectstoreResultsWriter(results, 'regression_tests/results/brp')
    writer.write()
    logger.info("Written test results to Objecstore at regression_tests/results/brp")


def init():
    if __name__ == "__main__":
        main()


init()
