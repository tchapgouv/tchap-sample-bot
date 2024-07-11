from abc import ABC, abstractmethod

from matrix_bot.bot import MatrixClient
from nio import MatrixRoom, RoomMessageText

from scripts.command import Command


class Validator(ABC):
    # TODO property or not ?
    @abstractmethod
    def validation_prompt(self) -> str: ...

    @abstractmethod
    async def validate(
        self,
        room: MatrixRoom,
        user_response: RoomMessageText,
        command: Command,
        matrix_client: MatrixClient,
    ) -> bool: ...
