import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем данные из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@om_valery')

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Простое хранилище пользователей в памяти
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
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_ID[1:]}"),
        types.InlineKeyboardButton(text="✅ Я подписался", callback_data="check_subscription")
    )
    return keyboard

# Главное меню бота
def get_main_menu():
    """Создает главное меню с выбором ботов"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="🎯 Тест: Выбор площадки", url="https://t.me/om_lab_bot"),
        types.InlineKeyboardButton(text="💬 О проекте", callback_data="about")
    )
    return keyboard

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
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
        # Сохраняем пользователя в базу
        users_database.add(user_id)
        logging.info(f"Пользователь {user_id} добавлен. Всего: {len(users_database)}")
        
        await message.answer(
            f"✨ Добро пожаловать, {first_name}!\n\n"
            f"🤖 Я помогу вам найти оптимальную стратегию продвижения.\n\n"
            f"Выберите действие:",
            reply_markup=get_main_menu()
        )

# Обработчик проверки подписки
@dp.callback_query_handler(lambda c: c.data == 'check_subscription')
async def process_check_subscription(callback_query: types.CallbackQuery):
    """Обработчик кнопки проверки подписки"""
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    
    is_subscribed = await check_subscription(user_id)
    
    if is_subscribed:
        users_database.add(user_id)
        logging.info(f"Пользователь {user_id} добавлен. Всего: {len(users_database)}")
        
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=f"✅ Отлично! Вы подписаны.\n\n"
                 f"✨ Добро пожаловать, {first_name}!\n\n"
                 f"Выберите действие:",
            reply_markup=get_main_menu()
        )
    else:
        await callback_query.answer(
            "❌ Вы еще не подписались на канал. Пожалуйста, подпишитесь и попробуйте снова.",
            show_alert=True
        )

# Обработчик кнопки "О проекте"
@dp.callback_query_handler(lambda c: c.data == 'about')
async def process_about(callback_query: types.CallbackQuery):
    """Информация о проекте"""
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="📚 *О проекте OM LAB*\n\n"
             "Мы помогаем экспертам и предпринимателям:\n"
             "✅ Выбрать оптимальные площадки для продвижения\n"
             "✅ Автоматизировать маркетинг с помощью AI\n"
             "✅ Построить эффективную стратегию присутствия\n\n"
             "🚀 Метод 25/8 - это эволюция подхода к продвижению в соцсетях.\n\n"
             "📢 Канал: @om_valery\n"
             "🌐 Сайт: valery.omlab.club",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")
        )
    )

# Обработчик возврата в главное меню
@dp.callback_query_handler(lambda c: c.data == 'back_to_menu')
async def process_back_to_menu(callback_query: types.CallbackQuery):
    """Возврат в главное меню"""
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="🤖 Выберите действие:",
        reply_markup=get_main_menu()
    )

# Запуск бота
if __name__ == '__main__':
    logging.info("Бот запущен!")
    executor.start_polling(dp, skip_updates=True)
