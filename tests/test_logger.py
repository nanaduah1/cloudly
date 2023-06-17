from dataclasses import dataclass
import logging

from cloudly.logging.logger import DynamoTableHandler, Logger


@dataclass
class FakeTable:
    data: dict = None

    def put_item(self, **kwargs):
        self.data = kwargs.get("Item")
        print("PUTTING ITEM: ", self.data)


def test_logger():
    table = FakeTable()
    _logger = logging.getLogger(__name__)
    handler = DynamoTableHandler("GoodStuff", table)
    _logger.setLevel(logging.INFO)
    _logger.addHandler(handler)

    logger = Logger(_logger)
    logger.info("Testing my shit!", metric={"orders": 1})

    logger.warn("This can be a problem")
    logger.error("There was an error")
