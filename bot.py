import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем данные из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@om_valery')

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Простое хранилище пользователей в памяти (временно, вместо Google Sheets)
users_database = set()

# Проверка подписки на канал
async def check_subscription(user_id: int) -> bool:
    """Проверяет подписан ли пользователь на канал"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        return False

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
            f"Для доступа ко всем функциям подпишитесь на канал {CHANNEL_ID} 👇",
            reply_markup=get_subscription_keyboard()
        )
    else:
        # Сохраняем пользователя в базу (в памяти)
        users_database.add(user_id)
        logging.info(f"Пользователь {user_id} добавлен. Всего пользователей: {len(users_database)}")
        
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
    first_name = callback.from_user.first_name
    
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        # Сохраняем пользователя
        users_database.add(user_id)
        logging.info(f"Пользователь {user_id} добавлен. Всего пользователей: {len(users_database)}")
        
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
