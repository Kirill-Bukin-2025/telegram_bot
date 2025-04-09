# telegramBot.py
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from config import BOT_TOKEN

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
SELECTING_DEPARTMENT, SELECTING_SUBTOPIC = range(2)

# База данных отделов клиники с подразделами
DEPARTMENTS = {
    'therapy': {
        'name': '🧑⚕️ Терапевт',
        'keywords': ['терапевт', 'простуда', 'грипп', 'температура', 'кашель', 'горло'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'ОРВИ/Грипп': ['простуда', 'грипп', 'температура'],
            'Кашель': ['кашель', 'бронхит', 'горло'],
            'Общее недомогание': ['слабость', 'недомогание', 'усталость']
        }
    },
    'surgery': {
        'name': '🔪 Хирургия',
        'keywords': ['хирург', 'операция', 'перелом', 'травма', 'рана', 'шов'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'Травмы': ['перелом', 'травма', 'ушиб'],
            'Послеоперационный уход': ['шов', 'операция', 'реабилитация'],
            'Гнойные процессы': ['рана', 'абсцесс', 'фурункул']
        }
    },
    'pediatrics': {
        'name': '👶 Педиатр',
        'keywords': ['педиатр', 'ребенок', 'дети', 'младенец', 'грудничок', 'новорожденный'],
        'response': 'Выберите возраст ребенка:',
        'subtopics': {
            'До 1 года': ['грудничок', 'новорожденный', 'младенец'],
            '1-3 года': ['малыш', 'ясли'],
            '3-7 лет': ['дошкольник'],
            'Школьник': ['школа', 'подросток']
        }
    },
    'neurology': {
        'name': '🧠 Невролог',
        'keywords': ['невролог', 'головная боль', 'мигрень', 'спина', 'головокружение', 'сосуды'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'Головные боли': ['мигрень', 'головная боль'],
            'Боли в спине': ['спина', 'остеохондроз', 'грыжа'],
            'Головокружения': ['головокружение', 'вестибулярный аппарат']
        }
    },
    'cardiology': {
        'name': '❤️ Кардиолог',
        'keywords': ['кардиолог', 'сердце', 'давление', 'гипертония', 'аритмия', 'боли в груди'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'Давление': ['гипертония', 'гипотония', 'давление'],
            'Аритмия': ['аритмия', 'сердцебиение'],
            'Боли в сердце': ['боли в груди', 'стенокардия']
        }
    },
    'dentistry': {
        'name': '🦷 Стоматолог',
        'keywords': ['стоматолог', 'зуб', 'зубы', 'кариес', 'болит зуб', 'пломба'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'Острая боль': ['болит зуб', 'острая боль'],
            'Кариес': ['кариес', 'дырка'],
            'Протезирование': ['пломба', 'коронка', 'протез']
        }
    },
    'ophthalmology': {
        'name': '👁️ Офтальмолог',
        'keywords': ['офтальмолог', 'глаз', 'зрение', 'близорукость', 'конъюнктивит', 'очки'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'Ухудшение зрения': ['близорукость', 'дальнозоркость', 'очки'],
            'Воспаления': ['конъюнктивит', 'краснота'],
            'Травмы': ['травма глаза', 'попадание инородного тела']
        }
    },
    'dermatology': {
        'name': '🧴 Дерматолог',
        'keywords': ['дерматолог', 'кожа', 'сыпь', 'аллергия', 'акне', 'экзема'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'Акне': ['акне', 'прыщи', 'угри'],
            'Аллергия': ['аллергия', 'зуд', 'крапивница'],
            'Экзема': ['экзема', 'шелушение']
        }
    },
    'gastroenterology': {
        'name': '🍽️ Гастроэнтеролог',
        'keywords': ['гастроэнтеролог', 'желудок', 'кишечник', 'изжога', 'гастрит', 'диарея'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'Гастрит': ['гастрит', 'желудок', 'изжога'],
            'Кишечник': ['диарея', 'запор', 'вздутие'],
            'Печень': ['печень', 'желчный', 'гепатит']
        }
    },
    'psychology': {
        'name': '🧠 Психолог',
        'keywords': ['психолог', 'депрессия', 'стресс', 'тревога', 'бессонница', 'паника'],
        'response': 'Выберите тип проблемы:',
        'subtopics': {
            'Депрессия': ['депрессия', 'апатия', 'подавленность'],
            'Тревога': ['тревога', 'паника', 'фобии'],
            'Стресс': ['стресс', 'выгорание'],
            'Сон': ['бессонница', 'нарушения сна']
        }
    }
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога - приветствие и кнопки"""
    # Очищаем предыдущие данные
    context.user_data.clear()

    buttons = [[KeyboardButton(dept['name'])] for dept in DEPARTMENTS.values()]
    buttons.append([KeyboardButton("❌ Отмена")])

    await update.message.reply_text(
        "Добрый день! Какой у Вас вопрос?",
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True,
            input_field_placeholder="Выберите отдел или опишите проблему"
        )
    )

    return SELECTING_DEPARTMENT


async def handle_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка возврата в меню"""
    await update.message.reply_text(
        "Возвращаемся в главное меню...",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
    )
    context.user_data.clear()
    return ConversationHandler.END


async def handle_department(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора отдела"""
    user_text = update.message.text.lower()

    # Проверяем отмену или возврат в меню
    if "отмена" in user_text or "вернуться в меню" in user_text or "назад" in user_text:
        return await handle_back_to_menu(update, context)

    # Проверяем выбор через кнопки
    for dept_id, dept_data in DEPARTMENTS.items():
        if dept_data['name'].lower() == user_text.lower():
            context.user_data['current_department'] = dept_id
            return await show_subtopics(update, context, dept_data)

    # Анализируем текст
    for dept_id, dept_data in DEPARTMENTS.items():
        if any(keyword in user_text for keyword in dept_data['keywords']):
            context.user_data['current_department'] = dept_id
            return await show_subtopics(update, context, dept_data)

    # Если не распознали запрос
    buttons = [[KeyboardButton(dept['name'])] for dept in DEPARTMENTS.values()]
    buttons.append([KeyboardButton("❌ Отмена")])

    await update.message.reply_text(
        "Не удалось определить ваш вопрос. Пожалуйста, выберите отдел:",
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True
        )
    )
    return SELECTING_DEPARTMENT


async def show_subtopics(update: Update, context: ContextTypes.DEFAULT_TYPE, dept_data):
    """Показать подразделы для выбранного отдела"""
    if 'subtopics' not in dept_data:
        # Если подразделов нет, сразу переходим к специалисту
        buttons = [
            [KeyboardButton("✅ Подтвердить"), KeyboardButton("🔙 Вернуться в меню")]
        ]

        await update.message.reply_text(
            f"Вы выбрали: {dept_data['name']}\n\n"
            f"Сейчас к вам подключится специалист. Подтвердите выбор или вернитесь в меню.",
            reply_markup=ReplyKeyboardMarkup(
                buttons,
                resize_keyboard=True
            )
        )
        return SELECTING_SUBTOPIC

    # Создаем кнопки подразделов
    subtopic_buttons = [[KeyboardButton(st)] for st in dept_data['subtopics'].keys()]
    subtopic_buttons.append([KeyboardButton("🔙 Вернуться в меню")])

    await update.message.reply_text(
        dept_data['response'],
        reply_markup=ReplyKeyboardMarkup(
            subtopic_buttons,
            resize_keyboard=True
        )
    )
    return SELECTING_SUBTOPIC


async def handle_subtopic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора подраздела"""
    user_text = update.message.text.lower()

    # Проверяем возврат в меню
    if "вернуться в меню" in user_text or "назад" in user_text or "отмена" in user_text:
        return await handle_back_to_menu(update, context)

    # Проверяем подтверждение выбора без подразделов
    if "подтвердить" in user_text:
        dept_id = context.user_data.get('current_department')
        if dept_id:
            dept_data = DEPARTMENTS.get(dept_id, {})
            await update.message.reply_text(
                f"Сейчас к вам подключится специалист из {dept_data.get('name', 'выбранного отдела')}. Ожидайте...",
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("/start")]],
                    resize_keyboard=True
                )
            )
            context.user_data.clear()
            return ConversationHandler.END

    dept_id = context.user_data.get('current_department')
    if not dept_id:
        return await start(update, context)

    dept_data = DEPARTMENTS.get(dept_id, {})

    # Проверяем выбранный подраздел
    if 'subtopics' in dept_data:
        for subtopic, keywords in dept_data['subtopics'].items():
            if subtopic.lower() == user_text.lower() or any(kw in user_text for kw in keywords):
                buttons = [
                    [KeyboardButton("✅ Подтвердить"), KeyboardButton("🔙 Вернуться в меню")]
                ]

                await update.message.reply_text(
                    f"Вы выбрали: {dept_data['name']} -> {subtopic}\n\n"
                    f"Сейчас к вам подключится специалист. Подтвердите выбор или вернитесь в меню.",
                    reply_markup=ReplyKeyboardMarkup(
                        buttons,
                        resize_keyboard=True
                    )
                )
                context.user_data['current_subtopic'] = subtopic
                return SELECTING_SUBTOPIC

    # Если подраздел не распознан
    if 'subtopics' in dept_data:
        subtopic_buttons = [[KeyboardButton(st)] for st in dept_data['subtopics'].keys()]
        subtopic_buttons.append([KeyboardButton("🔙 Вернуться в меню")])

        await update.message.reply_text(
            "Пожалуйста, выберите вариант из списка:",
            reply_markup=ReplyKeyboardMarkup(
                subtopic_buttons,
                resize_keyboard=True
            )
        )
    else:
        buttons = [
            [KeyboardButton("✅ Подтвердить"), KeyboardButton("🔙 Вернуться в меню")]
        ]
        await update.message.reply_text(
            "Пожалуйста, подтвердите выбор или вернитесь в меню:",
            reply_markup=ReplyKeyboardMarkup(
                buttons,
                resize_keyboard=True
            )
        )

    return SELECTING_SUBTOPIC


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text(
        "Диалог завершен. Если у вас появится вопрос, нажмите /start",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/start")]], resize_keyboard=True)
    )
    context.user_data.clear()
    return ConversationHandler.END


def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Основной обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_DEPARTMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_department)
            ],
            SELECTING_SUBTOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subtopic)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    # Обработчик команды /start вне диалога
    application.add_handler(CommandHandler('start', start))

    application.run_polling()


if __name__ == '__main__':
    main()