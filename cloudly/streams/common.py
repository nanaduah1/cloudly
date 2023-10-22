from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Type
from flowfast.step import Task, Mapping
from flowfast.workflow import Workflow
from flowfast.base import Step
from cloudly.logging.logger import Logger
from cloudly.config.client import ConfigClient


@dataclass
class Change:
    pk: str
    sk: str
    old: dict
    new: dict
    event: str

    @property
    def is_insert(self):
        return not self.old and self.new and self.event == "INSERT"

    @property
    def is_delete(self):
        return not self.new and self.event == "REMOVE"

    @property
    def is_update(self):
        return self.old and self.new and self.event == "MODIFY"

    def get_changed_fields(self, change: "Change", fields: Iterable[str]) -> dict:
        """
        Get all the changed fields that are part of Meta.fields
        """

        changed_fields = {}
        old = DynamicObject(change.old)
        new = DynamicObject(change.new)

        for field in fields:
            field_name = field.split(".")[-1]
            old_value = old.get(field)
            new_value = new.get(field)
            if old_value != new_value:
                changed_fields[field_name] = new_value

        return changed_fields

    @classmethod
    def from_stream(cls, record: dict, normalizer: Callable[[dict], dict]):
        event_name = record.get("eventName")
        new = normalizer(record["dynamodb"].get("NewImage", {}))
        old = normalizer(record["dynamodb"].get("OldImage", {}))
        keys = normalizer(record["dynamodb"].get("Keys", {}))

        return cls(
            pk=keys.get("pk"),
            sk=keys.get("sk"),
            old=old,
            new=new,
            event=event_name,
        )


@dataclass
class DynamicObject:
    data: dict

    def get(self, item):
        parts = item.split(".")

        if len(parts) == 1:
            return self.data.get(item)

        obj = self.data
        for part in parts:
            obj = obj.get(part)
            if not obj:
                return None

        return obj


@dataclass
class EventFilter(ABC):
    change: Change

    @abstractmethod
    def is_raised(self) -> bool:
        """
        This method is used to determine if a given event is raised.
        Should be implemented by subclasses of event filter to determine if a specific
        event has occurred.

            Returns True if the event is raised, False otherwise.
        """

        return True


@dataclass
class DbStreamProcessor(Step[Change, Change], ABC):
    """
    This class is used as base for classes that process events from DynamoDB streams.
    The events field is used to determine which events the processor can process.
    Subclasses will register the events they can process by adding them to the events
    field.

    events: Iterable[EventFilter]
    If no events are registered, the processor will process all events.

    can_process_event will return true if any of the registered events is raised.
    """

    database_table: Any
    logger: Logger
    config: ConfigClient

    events = None

    def process(self, input: Change) -> Change:
        try:
            if self.can_process_event(input):
                self.execute(input)
        except Exception as ex:
            self.logger.exception(f"{self.__class__.__name__} failed", ex)
        return input

    def can_process_event(self, change: Change) -> bool:
        if not self.events:
            return True

        return any(event_class(change).is_raised() for event_class in self.events)

    @abstractmethod
    def execute(self, change: Change) -> Change:
        return change


class ParseDynamoJson(Task):
    """
    Parse the DynamoDB JSON format into a Change object
     normalizer: Callable[[dict], dict] = None
      where normalizer is a function that takes a DynamoDB json format and returns a regular json format
    """

    normalizer: Callable[[dict], dict]

    def process(self, input: Mapping) -> Mapping:
        return Change.from_stream(input, self.normalizer)


class StreamProcessor:
    """
    This class is used to process events from DynamoDB streams.
    It will read the events from the stream and execute the processors
    that are registered for the given event.
    """

    processor_classes: Iterable[Type[DbStreamProcessor]]
    database_table: Any
    logger: Logger
    config: ConfigClient
    normalizer: Callable[[dict], dict]

    def run(self, event: dict):
        records = event.get("Records", [])

        if not records:
            self.logger.warn("Stream processor called with no records to process")
            return

        steps = tuple(
            cls(self.database_table, self.logger, self.config)
            for cls in self.processor_classes
        )

        pipeline = Workflow(ParseDynamoJson(self.normalizer))
        for step in steps:
            pipeline = pipeline.next(step)

        try:
            _ = tuple(Workflow.for_each(pipeline).run(records))
        except Exception as ex:
            self.logger.exception("DB Stream processing failed!", ex)
            raise
