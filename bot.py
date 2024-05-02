import asyncio
import logging
import os
import sys
import re
import asyncpg

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
dp = Dispatcher()
global pool


async def create_pool():
    return await asyncpg.create_pool(
        host='localhost',
        database='db_tests',
        user='onalone',
        password='q1w2e3r4',
        port=5432
    )


class TaskForm(StatesGroup):
    waiting_for_task_description = State()


async def get_msg_args(message, command):
    pattern = rf"/{re.escape(command)}\s+([^\s].*?)(?=\s*/{re.escape(command)}|$)"
    args = re.findall(pattern, message)
    return args


async def write_task(task, user_id):
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO tasks (user_id, task_desc) VALUES ($1, $2);",
                user_id, task
            )


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer("Welcome!")


@dp.message(Command('add'))
async def add_task(message: Message, command: CommandObject, state: FSMContext) -> None:
    cmd_list = await get_msg_args(message.text, 'add')
    if len(cmd_list) > 1:
        for task in cmd_list:
            await write_task(task, message.from_user.id)
        await message.answer(f"Tasks added!")
    elif command.args:
        await write_task(command.args, message.from_user.id)
        await message.answer(f"Task added!")
    else:
        await state.set_state(TaskForm.waiting_for_task_description)
        await message.answer("Please enter the task description:")


@dp.message(Command('tsk'))
async def get_tasks(message: Message) -> None:
    async with pool.acquire() as conn:
        tasks = await conn.fetch(
            "SELECT task_desc FROM tasks WHERE user_id = $1;",
            message.from_user.id
        )
    tsk_str = b'\xF0\x9F\x93\x8B'.decode() + ' <b>Task list:</b>\n\n'
    if len(tasks) > 0:
        for task in tasks:
            tsk_str += b'\xF0\x9F\x94\xB8 '.decode() + task['task_desc'] + '\n\n'
        await message.answer(tsk_str)
    else:
        await message.answer('Task list is empty')


@dp.message(Command('clr'))
async def remove_tasks(message: Message) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM tasks WHERE user_id = $1;",
            message.from_user.id
        )
    await message.answer('Task list is now empty')


@dp.message()
async def process_task_description(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == TaskForm.waiting_for_task_description.state:
        await write_task(message.text, message.from_user.id)
        await message.answer(f"Task added!")
        await state.clear()


async def main() -> None:
    global pool
    pool = await create_pool()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
