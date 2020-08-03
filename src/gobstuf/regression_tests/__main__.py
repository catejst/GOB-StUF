import logging
from gobstuf.regression_tests.brp import BrpRegression


def main():
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    BrpRegression(logger).run()


def init():
    if __name__ == "__main__":
        main()


init()
