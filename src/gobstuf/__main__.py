import datetime
from threading import Thread

from gobcore.logging.logger import logger
from gobcore.message_broker.config import WORKFLOW_EXCHANGE, BRP_REGRESSION_TEST_QUEUE, BRP_REGRESSION_TEST_RESULT_KEY
from gobcore.message_broker.messagedriven_service import messagedriven_service

from gobstuf.api import run as run_api
from gobstuf.regression_tests.brp import BrpRegression, ObjectstoreResultsWriter


def handle_brp_regression_test_msg(msg):
    logger.configure(msg, 'BRP Regression test')

    results = BrpRegression(logger).run()
    writer = ObjectstoreResultsWriter(results, 'regression_tests/results/brp')
    writer.write()
    logger.info("Written test results to Objecstore at regression_tests/results/brp")

    return {
        'header': {
            **msg.get('header', {}),
            'timestamp': datetime.datetime.utcnow().isoformat(),
        },
        'summary': {
            'warnings': logger.get_warnings(),
            'errors': logger.get_errors(),
        }
    }


SERVICEDEFINITION = {
    'brp_regression_test': {
        'queue': BRP_REGRESSION_TEST_QUEUE,
        'handler': handle_brp_regression_test_msg,
        'report': {
            'exchange': WORKFLOW_EXCHANGE,
            'key': BRP_REGRESSION_TEST_RESULT_KEY,
        }
    }
}


def run_message_thread():
    messagedriven_service(SERVICEDEFINITION, "StUF")


def init():
    if __name__ == "__main__":
        # Start messagedriven_service in separate thread
        t = Thread(target=run_message_thread)
        t.start()

        # Run the app locally
        run_api()


init()
