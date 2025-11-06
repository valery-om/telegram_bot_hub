import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем данные из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@om_valery')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключение к Google Sheets (будет настроено позже)
def init_google_sheets():
    """Инициализация подключения к Google Sheets"""
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # Создаем credentials из переменных окружения
        creds_dict = {
            "type": "service_account",
            "project_id": os.getenv('GOOGLE_PROJECT_ID'),
            "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('GOOGLE_PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv('GOOGLE_CERT_URL')
        }
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        return sheet
    except Exception as e:
        logging.error(f"Ошибка подключения к Google Sheets: {e}")
        return None

# Проверка подписки на канал
async def check_subscription(user_id: int) -> bool:
    """Проверяет подписан ли пользователь на канал"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        return False

# Сохранение пользователя в Google Sheets
def save_user_to_sheet(user_id: int, username: str = None, first_name: str = None):
    """Сохраняет данные пользователя в Google Sheets"""
    try:
        sheet = init_google_sheets()
        if sheet:
            # Проверяем, есть ли уже такой пользователь
            existing_ids = sheet.col_values(1)
            if str(user_id) not in existing_ids:
                sheet.append_row([user_id, username or '', first_name or ''])
                logging.info(f"Пользователь {user_id} добавлен в таблицу")
    except Exception as e:
        logging.error(f"Ошибка сохранения в Google Sheets: {e}")

# Клавиатура с кнопкой подписки
def get_subscription_keyboard():
    """Создает клавиатуру с кнопкой подписки и проверки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_ID[1:]}")],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subscription")]
    ])
    return keyboard

# Главное меню бота
def get_main_menu():
    """Создает главное меню с выбором ботов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Тест: Выбор площадки", url="https://t.me/om_lab_bot")],
        [InlineKeyboardButton(text="📊 Мои результаты", callback_data="my_results")],
        [InlineKeyboardButton(text="💬 О проекте", callback_data="about")]
    ])
    return keyboard

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Проверяем подписку
    is_subscribed = await check_subscription(user_id)
    
    if not is_subscribed:
        await message.answer(
            f"👋 Привет, {first_name}!\n\n"
            f"Я бот-ассистент проекта OM LAB.\n\n"
            f"Для доступа ко всем функциям подпишитесь на канал @om_valery 👇",
            reply_markup=get_subscription_keyboard()
        )
    else:
        # Сохраняем пользователя в базу
        save_user_to_sheet(user_id, username, first_name)
        
        await message.answer(
            f"✨ Добро пожаловать, {first_name}!\n\n"
            f"🤖 Я помогу вам найти оптимальную стратегию продвижения.\n\n"
            f"Выберите действие:",
            reply_markup=get_main_menu()
        )

# Обработчик проверки подписки
@dp.callback_query(F.data == "check_subscription")
async def process_check_subscription(callback: types.CallbackQuery):
    """Обработчик кнопки проверки подписки"""
    user_id = callback.from_user.id
    username = callback.from_user.username
    first_name = callback.from_user.first_name
    
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        # Сохраняем пользователя
        save_user_to_sheet(user_id, username, first_name)
        
        await callback.message.edit_text(
            f"✅ Отлично! Вы подписаны.\n\n"
            f"✨ Добро пожаловать, {first_name}!\n\n"
            f"Выберите действие:",
            reply_markup=get_main_menu()
        )
    else:
        await callback.answer(
            "❌ Вы еще не подписались на канал. Пожалуйста, подпишитесь и попробуйте снова.",
            show_alert=True
        )

# Обработчик кнопки "О проекте"
@dp.callback_query(F.data == "about")
async def process_about(callback: types.CallbackQuery):
    """Информация о проекте"""
    await callback.message.edit_text(
        "📚 *О проекте OM LAB*\n\n"
        "Мы помогаем экспертам и предпринимателям:\n"
        "✅ Выбрать оптимальные площадки для продвижения\n"
        "✅ Автоматизировать маркетинг с помощью AI\n"
        "✅ Построить эффективную стратегию присутствия\n\n"
        "🚀 Метод 25/8 - это эволюция подхода к продвижению в соцсетях.\n\n"
        "📢 Канал: @om_valery\n"
        "🌐 Сайт: valery.omlab.club",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")]
        ])
    )

# Обработчик кнопки "Мои результаты"
@dp.callback_query(F.data == "my_results")
async def process_my_results(callback: types.CallbackQuery):
    """Показывает результаты пользователя"""
    await callback.message.edit_text(
        "📊 *Ваши результаты*\n\n"
        "Здесь будут отображаться результаты прохождения тестов и анализа.\n\n"
        "Пока что эта функция в разработке. 🚧",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")]
        ])
    )

# Обработчик возврата в главное меню
@dp.callback_query(F.data == "back_to_menu")
async def process_back_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🤖 Выберите действие:",
        reply_markup=get_main_menu()
    )

# Запуск бота
async def main():
    """Главная функция запуска бота"""
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
