from abc import ABC, abstractmethod

from matrix_bot.bot import MatrixClient
from nio import MatrixRoom, RoomMessage


class Command(ABC):
    def __init__(
        self,
        room: MatrixRoom,
        message: RoomMessage,
        matrix_client: MatrixClient,
    ) -> None:
        self.room = room
        self.message = message
        self.matrix_client = matrix_client
        self.current_status_reaction = None

    async def set_status_reaction(self, key: str | None) -> None:
        if self.current_status_reaction:
            await self.matrix_client.room_redact(
                self.room.room_id, self.current_status_reaction
            )
        if key:
            self.current_status_reaction = await self.matrix_client.send_reaction(
                self.room.room_id, self.message, key
            )

    async def send_result(self) -> None:
        return

    @abstractmethod
    async def execute(self) -> bool: ...


class CommandToValidate(Command):
    # TODO property or not ?
    def validation_message(self) -> str | None:
        return None

    @staticmethod
    @abstractmethod
    def needs_secure_validation() -> bool: ...
