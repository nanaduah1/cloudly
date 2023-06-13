from dataclasses import dataclass
from typing import Any


@dataclass
class ConfigClient:
    table: Any
    app_key: str
    value_field: str = "value"
    stage_name: str = "beta"

    def get(self, key: str, default=None, shared=False) -> Any:
        try:
            item_key = self.__get_key(key, shared)
            response = self.table.get_item(Key=item_key)
            return response.get("Item", {}).get(self.value_field)
        except Exception as ex:
            print(f"Unable to read Config pk:{self.app_key} sk:{key}", ex)
            return default

    def set(self, key: str, value: Any, shared=False):
        try:
            item_key = self.__get_key(key, shared)
            self.table.put_item(Item={**item_key, self.value_field: value})
        except Exception as ex:
            print(f"Unable to read Config pk:{self.app_key} sk:{key}", ex)

    def get_or_set(self, key: str, default: str, shared=False):
        value = self.get(key, None, shared)
        if value:
            return value
        if default:
            self.set(key, default, shared)
        return default

    def __get_key(self, key: str, shared=False):
        if shared is True:
            return {"pk": f"{self.app_key}", "sk": key}
        return {"pk": f"{self.app_key}#{self.stage_name}".upper(), "sk": key}
