from typing import Final

from matrix_bot.bot import MatrixClient
from nio import MatrixRoom, RoomMessageText
from typing_extensions import override

from scripts.command import Command
from scripts.util import get_fallback_stripped_body
from scripts.validator import Validator


class ConfirmValidator(Validator):
    CONFIRM_KEYWORDS: Final = [
        "yes",
        "ok",
        "confirm",
    ]

    def __init__(self) -> None:
        pass

    @override
    def validation_prompt(self) -> str:
        return (
            "Please reply to this message with `yes`, `ok` or `confirm`"
            " to validate and execute the command."
        )

    @override
    async def validate(
        self,
        room: MatrixRoom,
        user_response: RoomMessageText,
        command: Command,
        matrix_client: MatrixClient,
    ) -> bool:
        body = get_fallback_stripped_body(user_response)
        return body.strip().strip(".") in self.CONFIRM_KEYWORDS


CONFIRM_VALIDATOR = ConfirmValidator()
