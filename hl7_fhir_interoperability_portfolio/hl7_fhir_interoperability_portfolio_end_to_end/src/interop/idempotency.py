"""In-memory duplicate-message demonstration; not durable or distributed."""
class DuplicateMessageError(ValueError):
    pass


class IdempotencyStore:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def claim(self, message_control_id: str) -> None:
        if not message_control_id.strip():
            raise ValueError("message_control_id cannot be blank")
        if message_control_id in self._seen:
            raise DuplicateMessageError(f"Duplicate message control ID: {message_control_id}")
        self._seen.add(message_control_id)
