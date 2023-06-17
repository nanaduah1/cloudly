from dataclasses import dataclass
from cloudly.logging.logger import Logger


@dataclass
class FakeTable:
    data: dict = None

    def put_item(self, **kwargs):
        self.data = kwargs.get("Item")
        print("PUTTING ITEM: ", self.data)


def test_logger():
    table = FakeTable()
    logger = Logger.createLogger(__name__, "APP-01", table)
    logger.info("Testing my shit!", metric={"orders": 1})

    logger.warn("This can be a problem")
    logger.error("There was an error")
