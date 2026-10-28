from ticketing.models import Event


class EventCatalog:
    def __init__(self):
        self._templates: dict[str, Event] = {}

    def register(self, key: str, template: Event) -> None:
        self._templates[key] = template

    def edition(self, key: str, **changes) -> Event:
        return self._templates[key].clone(**changes)
