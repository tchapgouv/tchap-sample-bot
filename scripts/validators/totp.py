from matrix_bot.bot import MatrixClient
from nio import MatrixRoom, RoomMessageText
from pyotp import TOTP
from typing_extensions import override

from scripts.command import Command
from scripts.util import get_fallback_stripped_body
from scripts.validator import Validator


class TOTPValidator(Validator):
    def __init__(self, totps: dict[str, str]) -> None:
        super().__init__()
        self.totps = {user_id: TOTP(totp_seed) for user_id, totp_seed in totps.items()}

    @override
    def validation_prompt(self) -> str:
        return (
            "Please reply to this message with an authentication code"
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
        error_msg = None

        body = get_fallback_stripped_body(user_response)
        totp_code = body.replace(" ", "")

        if len(totp_code) == 6 and totp_code.isdigit():
            totp_checker = self.totps.get(command.message.sender)
            if not totp_checker:
                error_msg = "You are not allowed to execute secure commands, sorry."
            elif not totp_checker.verify(totp_code):
                error_msg = "Wrong authentication code."
        else:
            error_msg = (
                "Couldnt parse the authentication code, it should be a 6 digits code."
            )
        if error_msg is not None:
            await matrix_client.send_text_message(
                room.room_id,
                error_msg,
                reply_to=user_response.event_id,
                thread_root=command.message.event_id,
            )
            return False

        return True
