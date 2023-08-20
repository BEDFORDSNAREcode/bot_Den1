import os
import subprocess


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
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '6550507310:AAGoL9qJ0w-oyBJOo5dQLo8vZQUyc39Z8y0'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage= MemoryStorage())
logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())

# Инициализация базы данных SQLite
conn = sqlite3.connect('survey_answers.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS survey_answers (user_id INTEGER, question TEXT, answer TEXT)')
conn.commit()

# Список вопросов для опросника
questions = [
    "Как дела?",
    "Какую книгу по бизнесу ты сейчас читаешь?",
    "Кофе или чай?",
    "Достоевский - красавчик?",
    "Сколько млрд долларов ты будешь зарабатывать к 2025г?"
]

# Определение FSM состояний
class SurveyStates:
    FIRST_QUESTION = "first_question"
    SECOND_QUESTION = "second_question"
    THIRD_QUESTION = "third_question"
    FOURTH_QUESTION = "fourth_question"
    FIFTH_QUESTION = "fifth_question"

# Кнопка для прекращения опроса
cancel_button = KeyboardButton('Прекратить опрос')

# Команда старта опроса
@dp.message_handler(commands=['start'])
async def start_survey(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await message.answer("Привет! Давай проведем опрос.")

# Устанавливаем начальное состояние - первый вопрос
    await state.update_data(question=questions[0])
    await state.set_state(SurveyStates.FIRST_QUESTION)

# Отправляем первый вопрос с кнопкой отмены
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
    await message.answer(questions[0], reply_markup=markup)

# Обработка ответов на вопросы с использованием FSM
@dp.message_handler(lambda message: message.text, state=SurveyStates.FIRST_QUESTION)
@dp.message_handler(lambda message: message.text, state=SurveyStates.SECOND_QUESTION)
@dp.message_handler(lambda message: message.text, state=SurveyStates.THIRD_QUESTION)
@dp.message_handler(lambda message: message.text, state=SurveyStates.FOURTH_QUESTION)
@dp.message_handler(lambda message: message.text, state=SurveyStates.FIFTH_QUESTION)
async def process_answer(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.id
        question = data.get('question')
        if not question:
            await message.answer("Броски что-то пошло не так блин, давай сначала все это")
            await state.finish()
            return

        question_index = questions.index(data['question'])
        data['answer'] = message.text

# Сохраняем ответ
        cursor.execute('INSERT INTO survey_answers VALUES (?, ?, ?)', (user_id, data['question'], data['answer']))
        conn.commit()

# Проверяем, есть ли следующий вопрос
        if question_index + 1 < len(questions):
            next_question = questions[question_index + 1]
            data['question'] = next_question

# Отправляем следующий вопрос с кнопкой отмены
            markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cancel_button)
            await message.answer(next_question, reply_markup=markup)

        else:
            await message.answer("Спасибо за участие в опросе! Опрос завершен.")
            await state.finish()

# Обработка команды на отмену опроса
@dp.message_handler(lambda message: message.text == 'Прекратить опрос', state='*')
@dp.message_handler(Command('cancel'), state='*')
async def cancel_survey(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await state.finish()
        await message.reply("Вы отменили опрос.", reply_markup=ReplyKeyboardRemove())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
