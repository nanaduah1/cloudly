from dataclasses import dataclass
from logging import Handler, LogRecord
import logging
from typing import Any


class DynamoTableHandler(Handler):
    def __init__(self, client_id: str, database_table: Any, level=logging.INFO):
        Handler.__init__(self, level)
        self.client_id = client_id
        self.database_table = database_table

    def emit(self, record: LogRecord):
        try:
            msg = self.format(record)
            log = {
                "timestamp": record.created,
                "clientId": self.client_id,
                "eventType": record.eventType,
                "detail": msg,
            }

            if record.eventType == "exception":
                log["trace"] = {
                    "file": record.filename,
                    "funcName": record.funcName,
                    "lineNumber": record.lineno,
                    "module": record.module,
                    "stack": record.stack_info,
                }

            if record.metric:
                log["metric"] = record.metric

            self.database_table.put_item(
                Item={
                    "pk": self.client_id.upper(),
                    "sk": f"LOGS#{log['eventType']}#{log['timestamp']}",
                    "data": log,
                }
            )
        except Exception as ex:
            print(ex)


@dataclass
class Logger:
    logger: logging.Logger

    def event(self, eventType: str, message: str, metric: str, value: Any):
        extra = {"eventType": eventType, "metric": {metric: value}}
        self.logger.info(message, extra=extra)

    def info(self, message: str, **kwargs):
        extra = {**kwargs, "eventType": "info"}
        self.logger.info(message, extra=extra)

    def warn(self, message: str, **kwargs):
        extra = {**kwargs, "eventType": "warning"}
        self.logger.warn(message, extra=extra)

    def error(self, message: str, **kwargs):
        extra = {**kwargs, "eventType": "error"}
        self.logger.error(message, extra=extra)

    def exception(self, message: str, ex: Exception, **kwargs):
        extra = {**kwargs, "eventType": "exception", "metric": {"count": 1}}
        self.logger.exception(message, exc_info=ex, extra=extra)
