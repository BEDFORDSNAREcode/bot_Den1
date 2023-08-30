import os
import subprocess
import logging
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.filters import state
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

class WaitForCoffeOrTea(state.State):
    pass

project_directory = '/Users/vladlobanov/IdeaProjects/untitled5'
github_repo_url = 'git@github.com:BEDFORDSNAREcode/bot_Den1.git'

def initialize_git():
    try:
        os.chdir(project_directory)
        subprocess.run(['git', 'init'])
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'Первый коммит'])
        subprocess.run(['git', 'remote', 'add', 'origin', github_repo_url])
        print('Git инициализирован и настроен.')
    except Exception as e:
        print(f'Произошла ошибка: {e}')


def upload_to_github():
    try:
        os.chdir(project_directory)
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'Описание вашего коммита'])
        subprocess.run(['git', 'push', 'origin', 'master'])
        print('Код успешно загружен на GitHub.')
    except Exception as e:
        print(f'Произошла ошибка: {e}')

if __name__ == '__main__':
    initialize_git()
    upload_to_github()

API_TOKEN = '6550507310:AAGoL9qJ0w-oyBJOo5dQLo8vZQUyc39Z8y0'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())

conn = sqlite3.connect('survey_answers.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS survey_answers (user_id INTEGER, question TEXT, answer TEXT)')
conn.commit()

questions = [
    "Как дела?",
    "Какую книгу по бизнесу ты сейчас читаешь?",
    "Кофе или чай?",
    "Достоевский - красавчик?",
    "Сколько млрд долларов ты будешь зарабатывать к 2025г?"
]

class SurveyStates:
    FIRST_QUESTION = "first_question"
    SECOND_QUESTION = "second_question"
    THIRD_QUESTION = "third_question"
    FOURTH_QUESTION = "fourth_question"
    FIFTH_QUESTION = "fifth_question"

def validate_drink_answer(answer):
    answer = answer.lower()
    if 'кофе' in answer:
        return 'кофе'
    elif 'чай' in answer:
        return 'чай'
    return None

def validate_number_answer(answer):
    try:
        number = int(answer.split()[0])
        return number
    except ValueError:
        return None

cancel_button = KeyboardButton('Прекратить опрос')

@dp.message_handler(commands=['start'])
async def start_survey(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await message.answer("Привет! Давай проведем опрос.")

    await state.update_data(question=questions[0])
    await state.set_state(SurveyStates.FIRST_QUESTION)

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
    await message.answer(questions[0], reply_markup=markup)

@dp.message_handler(lambda message: message.text, state=SurveyStates.FIRST_QUESTION)
@dp.message_handler(lambda message: message.text, state=SurveyStates.SECOND_QUESTION)
@dp.message_handler(lambda message: message.text, state=SurveyStates.THIRD_QUESTION)
@dp.message_handler(lambda message: message.text, state=SurveyStates.FOURTH_QUESTION)
@dp.message_handler(lambda message: message.text, state=SurveyStates.FIFTH_QUESTION)
async def process_question(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.id
        answer = message.text.lower()

        if data.get('question') == questions[0]:
            data['answer'] = answer
            cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], data['answer']))
            conn.commit()

            next_question = questions[1]
            data['question'] = next_question
            await state.update_data(question=next_question)
            markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
            await message.answer(next_question, reply_markup=markup)
        elif data.get('question') == questions[1]:
            data['answer'] = answer
            cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], data['answer']))
            conn.commit()

            next_question = questions[2]
            data['question'] = next_question
            await state.update_data(question=next_question)
            markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
            await message.answer(next_question, reply_markup=markup)
        elif data.get('question') == questions[2]:
            if 'кофе' in answer:
                data['answer'] = 'кофе'
                cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], data['answer']))
                conn.commit()
            elif 'чай' in answer:
                data['answer'] = 'чай'
                cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], data['answer']))
                conn.commit()
            else:
                if 'invalid_count' not in data:
                    data['invalid_count'] = 1
                else:
                    data['invalid_count'] += 1

                if data['invalid_count'] >= 3:
                    data['answer'] = None
                    cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], 'None'))
                    conn.commit()
                    await state.finish()
                else:
                    await message.answer("Нужно выбрать только кофе или чай, Дениска!")
                    await WaitForCoffeOrTea.set()

            next_question = questions[3]
            data['question'] = next_question
            await state.update_data(question=next_question)
            markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
            await message.answer(next_question, reply_markup=markup)
        elif data.get('question') == questions[3]:
            markup = InlineKeyboardMarkup(row_width=2)
            yes_button = InlineKeyboardButton("Да", callback_data='yes')
            no_button = InlineKeyboardButton("Нет", callback_data='no')
            markup.add(yes_button, no_button)

            await message.answer("Достоевский - красавчик?", reply_markup=markup)

@dp.callback_query_handler(lambda query: query.data == 'yes', state=SurveyStates.FOURTH_QUESTION)
async def process_dostoevsky_yes(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['answer'] = 'Да'
        user_id = query.from_user.id
        cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], data['answer']))
        conn.commit()

    next_question = questions[4]
    data['question'] = next_question
    await state.update_data(question=next_question)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
    await query.message.answer(next_question, reply_markup=markup)

@dp.callback_query_handler(lambda query: query.data == 'no', state=SurveyStates.FOURTH_QUESTION)
async def process_dostoevsky_no(query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['answer'] = 'Нет'
        user_id = query.from_user.id
        cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], data['answer']))
        conn.commit()

    next_question = questions[4]
    data['question'] = next_question
    await state.update_data(question=next_question)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
    await query.message.answer(next_question, reply_markup=markup)

@dp.message_handler(commands=['start'], state='*')
async def start_survey(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    coffee_button = types.InlineKeyboardButton("Кофе", callback_data='coffee')
    tea_button = types.InlineKeyboardButton("Чай", callback_data='tea')
    markup.add(coffee_button, tea_button)

    await message.reply("Выберите напиток:", reply_markup=markup)

@dp.message_handler(lambda message: message.text == 'Прекратить опрос', state='*')
@dp.message_handler(Command('cancel'), state='*')
async def cancel_survey(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await state.finish()
        await message.reply("Вы отменили опрос.", reply_markup=ReplyKeyboardRemove())

@dp.callback_query_handler(lambda query: query.data in ['coffee', 'tea'], state=SurveyStates.THIRD_QUESTION)
async def process_drink_choice(query: types.CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    answer = query.data

    async with state.proxy() as data:
        data['answer'] = answer
        cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], data['answer']))
        conn.commit()

    next_question = questions[3]
    data['question'] = next_question
    await state.update_data(question=next_question)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
    await query.message.answer(next_question, reply_markup=markup)

@dp.message_handler(lambda message: not validate_number_answer(message.text), state=SurveyStates.FIFTH_QUESTION)
async def process_non_numeric_answer(message: types.Message):
    await message.answer("Пожалуйста, введите числовой ответ.")

@dp.message_handler(lambda message: validate_number_answer(message.text), state=SurveyStates.FIFTH_QUESTION)
async def process_numeric_answer(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    answer = validate_number_answer(message.text)

    async with state.proxy() as data:
        data['answer'] = answer
        cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], str(data['answer'])))
        conn.commit()

    await message.answer("Спасибо за ответы! Результаты опроса:")
    async with state.proxy() as data:
        for idx, question in enumerate(questions):
            await message.answer(f"Вопрос {idx + 1}: {question}\nОтвет: {data.get('answer')}")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)




