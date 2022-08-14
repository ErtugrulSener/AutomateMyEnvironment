from scripts.singleton import Singleton


@Singleton
class StringManager:
    def is_int(self, value):
        return value.isdigit()

    def is_boolean(self, value):
        return value in ["True", "False"]

    def is_set(self, value):
        return value.startswith("{") and value.endswith("}")

    def str_to_bool(self, value):
        if not value:
            return False

        return str(value).lower() in ("y", "yes", "t", "true", "on", "1")

    def str_to_set(self, value):
        value = value[1:-1].strip()
        return set(value.split(", "))

    def str_to_int(self, value):
        return int(value)
