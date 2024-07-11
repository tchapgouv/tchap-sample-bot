import datetime

from nio import MatrixRoom, Event

from nio import MatrixRoom, RoomMessage
from matrix_bot.client import MatrixClient
from matrix_bot.callbacks import properly_fail
from matrix_bot.eventparser import MessageEventParser, ignore_when_not_concerned

from scripts.command import Command
from scripts.util import get_server_name
from typing_extensions import override

class GetHourCommand(Command):
    KEYWORD = "get_hour"

    @staticmethod
    @override
    def needs_secure_validation() -> bool:
        return False
    
    def __init__(
        self, room: MatrixRoom, message: RoomMessage, matrix_client: MatrixClient
    ) -> None:
        super().__init__(room, message, matrix_client)

        event_parser = MessageEventParser(
            room=room, event=message, matrix_client=matrix_client
        )
        event_parser.do_not_accept_own_message()
        
        # il ne va répondre qu'au message "!get_hour"
        event_parser.command(self.KEYWORD)

        self.server_name = get_server_name(self.matrix_client.user_id)

    @override
    async def execute(self) -> bool:

        # il ne va répondre qu'au message "!heure"
#        self.event_parser.command("get_hour")
        heure = f"il est {datetime.datetime.now().strftime('%Hh%M')}"
        # il envoie l'information qu'il est en train d'écrire
        # await self.matrix_client.room_typing(self.room.room_id)
        # il envoie le message
        await self.matrix_client.send_text_message(self.room.room_id, heure)

        return True
    
    @override
    async def set_status_reaction(self, key: str | None) -> None:
        return