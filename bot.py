import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.bot import api
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode, CallbackQuery
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)

# конфиг
API_TOKEN = '997719198:AAHzfPmw4AGgi3SkfCAHTFSO3jyejEmJ9UQ'
admin_id = 617953383
bot_id = 997719198

# прокси
patched_url = 'https://telegg.ru/orig/bot{token}/{method}'
setattr(api, 'API_URL', patched_url)

bot = Bot(token=API_TOKEN)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    age = State()  # Will be represented in storage as 'Form:age'
    gender = State()  # Will be represented in storage as 'Form:gender'


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.name.set()

    await message.answer(
        "Покажем работу бота на примере Парикмахерского салона... Бот начинает вести диалог\n\nПривет! Как Вас зовут?")


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.answer('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await message.answer("Далее серия каких-то вопросов еще...Например \n\nСколько вам лет?")


# Check age. Age gotta be digit
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):
    """
    If age is invalid
    """
    return await message.answer("Должно быть число.\nСколько вам лет? (введите цифры)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    # Update state and data
    await Form.next()
    await state.update_data(age=int(message.text))

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Муж", "Женский")
    markup.add("Не знаю")

    await message.answer("Можно использовать клавиатуру для выбора ответов и навигации.. \n\n Какая стрижка будет?",
                         reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["Муж", "Женский", "Не знаю"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    """
    In this example gender has to be one of: Male, Female, Other.
    """
    return await message.reply("Пол не введен. Выберите ваш пол пожалуйста.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gender'] = message.text

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        # And send message
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Принято,', md.bold(data['name'])),
                md.text('Возраст:', md.code(data['age'])),
                md.text('Стрижка:', data['gender']),
                md.text('\n'),
                md.text('Ожидайте сейчас подберем вам ближайшую дату...'),

                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )
        await bot.send_message(message.chat.id, 'Принятые данные можно пересылать администратору или мастеру, '
                                                'также боту можно задать календарь для того чтобы он сам вел диалог и '
                                                'выбирал ближайшую дату для записи. Можно также задать прайс (с ценами '
                                                'рисунками) и систему оплаты\n.Подключить бота к Базе Данных, '
                                                'к CRM системе или к сайту и '
                                                'может выполнять ту же механическую работу вместо администратора, '
                                                'менеджера по продажам и т.д. т.е. все те действия где не требуется '
                                                'личного пристутствия человека или голосовые ответы (звонки и '
                                                'прочее), Все эти процессы можно автоматизировать... \n\nДалее '
                                                'пересылаем ссобщение администратору, тем самым сократив ему время на '
                                                'диалоги и т.д. Админу останется только выбрать дату и ответить боту, '
                                                'чтоб бот уведомил клиента о записи, или админ может написать клиенту '
                                                'напрямую.. ')

        await bot.send_message(message.chat.id, 'Если хотите узнать более подробно о работе ботов, напишите создателю '
                                                'этого демо-бота @vildan_valeev\n\nНачать заново нажмите /start')
        # Finish conversation
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
