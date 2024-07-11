import time
from unittest.mock import AsyncMock, Mock

import pytest
from nio import MatrixRoom, RoomMessageText

from scripts.adminbot import COMMANDS
from scripts.validatebot import ValidateBot
from scripts.validators.confirm import ConfirmValidator
from tests import generate_event_id, mock_client_and_run


@pytest.mark.asyncio()
async def test_reset_password() -> None:
    bot = ValidateBot(
        homeserver="http://localhost:8008",
        username="",
        password="",
        commands=COMMANDS,
        secure_validator=ConfirmValidator(),
        coordinator=None,
    )
    mocked_client, t = await mock_client_and_run(bot)
    mocked_client.send = AsyncMock(
        return_value=Mock(ok=True, json=AsyncMock(return_value={}))
    )

    room = MatrixRoom("!roomid:example.org", "@user1:example.org")

    command_event_id = generate_event_id()
    await mocked_client.fake_synced_message(
        room,
        RoomMessageText(
            source={
                "event_id": command_event_id,
                "sender": "@user1:example.org",
                "origin_server_ts": int(time.time() * 1000),
            },
            body="!reset_password @user_to_reset:example.org",
            format=None,
            formatted_body=None,
        ),
    )

    mocked_client.send_markdown_message.assert_awaited_once()
    assert mocked_client.send_markdown_message.await_args
    assert (
        "You are about to reset password of the following users"
        in mocked_client.send_markdown_message.await_args[0][1]
    )
    mocked_client.send_markdown_message.reset_mock()

    await mocked_client.fake_synced_message(
        room,
        RoomMessageText(
            source={
                "event_id": generate_event_id(),
                "sender": "@user1:example.org",
                "origin_server_ts": int(time.time() * 1000),
                "content": {
                    "m.relates_to": {
                        "event_id": command_event_id,
                        "rel_type": "m.thread",
                    }
                },
            },
            body="yes",
            format=None,
            formatted_body=None,
        ),
    )

    mocked_client.send_file_message.assert_awaited_once()
    mocked_client.send_file_message.reset_mock()

    # one call to fetch the devices, and one call to reset the password
    assert len(mocked_client.send.await_args_list) == 2

    assert mocked_client.send.await_args
    assert "/reset_password/" in mocked_client.send.await_args[0][1]
    mocked_client.send.reset_mock()

    t.cancel()
