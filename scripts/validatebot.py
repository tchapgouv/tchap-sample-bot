import cachetools
from matrix_bot.bot import MatrixBot
from matrix_bot.eventparser import EventNotConcerned
from nio import MatrixRoom, RoomMessage, RoomMessageText

from scripts.command import Command, CommandToValidate
from scripts.validator import Validator
from scripts.validators.confirm import CONFIRM_VALIDATOR


class ValidateBot(MatrixBot):
    def __init__(
        self,
        *,
        homeserver: str,
        username: str,
        password: str,
        commands: list[type[Command]],
        secure_validator: Validator | None,
        coordinator: str | None,
    ) -> None:
        needs_secure_validator = False
        for command_type in commands:
            if (
                issubclass(command_type, CommandToValidate)
                and command_type.needs_secure_validation()
            ):
                needs_secure_validator = True
                break
        if needs_secure_validator and not secure_validator:
            raise Exception  # TODO
        super().__init__(homeserver, username, password)
        self.commands = commands
        self.secure_validator = secure_validator
        self.coordinator = coordinator

        self.recent_events_cache: cachetools.TTLCache[str, RoomMessage] = (
            cachetools.TTLCache(maxsize=5120, ttl=24 * 60 * 60)
        )
        self.commands_cache: cachetools.TTLCache[str, Command] = cachetools.TTLCache(
            maxsize=5120, ttl=24 * 60 * 60
        )

        self.callbacks.register_on_message_event(self.store_event_in_cache)
        self.callbacks.register_on_message_event(self.validate_and_execute)
        self.callbacks.register_on_message_event(self.handle_commands)

    async def store_event_in_cache(
        self,
        _room: MatrixRoom,
        message: RoomMessage,
    ) -> None:
        self.recent_events_cache[message.event_id] = message

    def get_replied_event(self, message: RoomMessage) -> RoomMessage | None:
        return self.recent_events_cache.get(
            message.source.get("content", {})
            .get("m.relates_to", {})
            .get("m.in_reply_to", {})
            .get("event_id")
        )

    async def get_related_command_to_validate(
        self, message: RoomMessage
    ) -> CommandToValidate | None:
        content = message.source.get("content", {})
        if not content:
            return None

        # let's check if we have a thread root message and if it is a command
        command_to_validate: CommandToValidate | None = None
        if content.get("m.relates_to", {}).get("rel_type") == "m.thread":
            command = self.commands_cache.get(
                content.get("m.relates_to", {}).get("event_id")
            )
            if isinstance(command, CommandToValidate):
                return command

        if not command_to_validate:
            # no thread here, let's check the reply chain for a command to validate
            replied_event = message
            while replied_event:
                replied_event = self.get_replied_event(replied_event)
                if replied_event:
                    command = self.commands_cache.get(replied_event.event_id)
                    if isinstance(command, CommandToValidate):
                        return command

        return None

    async def validate_and_execute(
        self,
        room: MatrixRoom,
        message: RoomMessage,
    ) -> None:
        if not isinstance(message, RoomMessageText):
            return

        content = message.source.get("content", {})
        if not content:
            return

        command_to_validate: (
            CommandToValidate | None
        ) = await self.get_related_command_to_validate(message)

        if not command_to_validate:
            return

        # the validation should come from the sender of the command
        if command_to_validate.message.sender != message.sender:
            return

        validator: Validator = CONFIRM_VALIDATOR
        if command_to_validate.needs_secure_validation():
            assert self.secure_validator is not None
            validator = self.secure_validator

        if await validator.validate(
            room, message, command_to_validate, self.matrix_client
        ):
            await self.execute_command(command_to_validate)

    async def execute_command(self, command: Command) -> None:
        await command.set_status_reaction("🚀")
        result_reaction = "❌"
        try:
            res = await command.execute()
            if res:
                result_reaction = "✅"
        except Exception as e:
            print(e)

        await command.set_status_reaction(result_reaction)
        try:
            await command.send_result()
        except Exception as e:
            print(e)

    async def handle_commands(
        self,
        room: MatrixRoom,
        message: RoomMessage,
    ) -> None:
        for command_type in self.commands:
            try:
                command = command_type(room, message, self.matrix_client)
                if isinstance(command, CommandToValidate):
                    self.commands_cache[message.event_id] = command
                    if (
                        self.coordinator
                        and self.matrix_client.user_id != self.coordinator
                    ):
                        continue  # TODO or return ?

                    validator: Validator = CONFIRM_VALIDATOR
                    if command.needs_secure_validation():
                        assert self.secure_validator is not None
                        validator = self.secure_validator

                    validation_message = command.validation_message()
                    if validation_message:
                        validation_message += "\n\n"
                    else:
                        validation_message = ""
                    validation_message += validator.validation_prompt()

                    await self.matrix_client.send_markdown_message(
                        room.room_id,
                        validation_message,
                        reply_to=message.event_id,
                        thread_root=message.event_id,
                    )
                    await command.set_status_reaction("🔢")
                else:
                    await self.execute_command(command)
                # TODO break or not ?
            except EventNotConcerned:
                pass
