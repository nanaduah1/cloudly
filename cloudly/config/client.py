from dataclasses import dataclass
from typing import Any


@dataclass
class ConfigClient:
    table: Any
    app_key: str
    value_field: str = "value"

    def get(self, key: str, default=None) -> Any:
        try:
            response = self.table.get_item(Key={"pk": self.app_key, "sk": key})
            return response.get("Item", {}).get(self.value_field)
        except Exception as ex:
            print(f"Unable to read Config pk:{self.app_key} sk:{key}", ex)
            return default

    def set(self, key: str, value: Any):
        try:
            self.table.put_item(
                Item={"pk": self.app_key, "sk": key, self.value_field: value}
            )
        except Exception as ex:
            print(f"Unable to read Config pk:{self.app_key} sk:{key}", ex)
