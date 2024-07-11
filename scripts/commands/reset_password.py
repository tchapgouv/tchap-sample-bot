import json
import secrets
import string
import time
from typing import Any

import aiofiles
from matrix_bot.bot import MatrixClient
from matrix_bot.eventparser import MessageEventParser
from nio import MatrixRoom, RoomMessage
from typing_extensions import override

from scripts.command import CommandToValidate
from scripts.util import get_server_name



class ResetPasswordCommand(CommandToValidate):
    KEYWORD = "reset_password"

    @staticmethod
    @override
    def needs_secure_validation() -> bool:
        return True

    def __init__(
        self, room: MatrixRoom, message: RoomMessage, matrix_client: MatrixClient
    ) -> None:
        super().__init__(room, message, matrix_client)

        event_parser = MessageEventParser(
            room=room, event=message, matrix_client=matrix_client
        )
        event_parser.do_not_accept_own_message()
        self.user_ids = event_parser.command(self.KEYWORD).split()

        self.failed_user_ids: list[str] = []

        self.json_report: dict[str, Any] = {"command": self.KEYWORD}

        self.server_name = get_server_name(self.matrix_client.user_id)

    async def reset_password(
        self, user_id: str, password: str, *, logout_devices: bool = True
    ) -> bool:
        # TODO check coordinator config
        if get_server_name(user_id) != self.server_name:
            return True

        resp = await self.matrix_client.send(
            "GET",
            f"/_synapse/admin/v2/users/{user_id}/devices",
            headers={"Authorization": f"Bearer {self.matrix_client.access_token}"},
        )

        self.json_report.setdefault(user_id, {})

        # TODO handle unknown user here and return
        if resp.ok:
            json_body = await resp.json()
            self.json_report[user_id]["devices"] = json_body.get("devices", [])

        resp = await self.matrix_client.send(
            "POST",
            f"/_synapse/admin/v1/reset_password/{user_id}",
            headers={"Authorization": f"Bearer {self.matrix_client.access_token}"},
            data=json.dumps(
                {
                    "new_password": password,
                    "logout_devices": logout_devices,
                }
            ),
        )
        if not resp.ok:
            json_body = await resp.json()
            self.json_report[user_id].update(json_body)
            self.failed_user_ids.append(user_id)
            return False

        return True

    @override
    async def execute(self) -> bool:
        def randomword(length: int) -> str:
            characters = string.ascii_lowercase + string.digits
            return "".join(secrets.choice(characters) for _ in range(length))

        for user_id in self.user_ids:
            await self.reset_password(user_id, randomword(32))

        return not self.failed_user_ids

    @override
    def validation_message(self) -> str | None:
        return "\n".join(
            [
                "You are about to reset password of the following users:",
                "",
                *[f"- {user_id}" for user_id in self.user_ids],
                "",
                "⚠⚠ This will also log-out all of their devices!",
            ]
        )

    @override
    async def send_result(self) -> None:
        async with aiofiles.tempfile.NamedTemporaryFile(suffix=".json") as tmpfile:
            await tmpfile.write(
                json.dumps(self.json_report, indent=2, sort_keys=True).encode()
            )
            await tmpfile.flush()
            await self.matrix_client.send_file_message(
                self.room.room_id,
                str(tmpfile.name),
                mime_type="application/json",
                filename=f"{time.strftime('%Y_%m_%d-%H_%M')}-{self.KEYWORD}.json",
                reply_to=self.message.event_id,
                thread_root=self.message.event_id,
            )

        if self.failed_user_ids:
            text = "\n".join(
                [
                    "Couldn't reset the password of the following users:",
                    "",
                    *[f"- {user_id}" for user_id in self.failed_user_ids],
                ]
            )
            await self.matrix_client.send_markdown_message(
                self.room.room_id,
                text,
                reply_to=self.message.event_id,
                thread_root=self.message.event_id,
            )
