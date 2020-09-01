import datetime
from gobstuf.api import get_flask_app
from threading import Thread

from gobcore.logging.logger import logger
from gobcore.message_broker.config import WORKFLOW_EXCHANGE, BRP_REGRESSION_TEST_QUEUE, BRP_REGRESSION_TEST_RESULT_KEY
from gobcore.message_broker.messagedriven_service import messagedriven_service

from gobstuf.config import GOB_STUF_PORT
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
        'summary': logger.get_summary(),
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


def get_app():
    # Start messagedriven_service in separate thread
    t = Thread(target=run_message_thread)
    t.start()

    return get_flask_app()


def run():
    """
    Get the Flask app and run it at the port as defined in config

    :return: None
    """
    app = get_app()
    app.run(port=GOB_STUF_PORT)
