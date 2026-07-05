import os
import telebot
import sqlite3
from dotenv import load_dotenv
import os
print("📍 ВНИМАНИЕ! Бот сейчас физически работает в папке:", os.getcwd())

from openai import OpenAI

# 1. Загружаем секретные ключи безопасности
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

ai_client = OpenAI(
    api_key=os.getenv("PROXY_API_KEY"),
    base_url="https://api.proxyapi.ru/openai/v1"
)

# 2. Создаем новую Базу Данных для автосервиса
conn = sqlite3.connect('autoservice.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу клиентов СТО (ID, Имя, Телефон, Марка машины)
cursor.execute('''
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    client_name TEXT,
    car_model TEXT
)''')
conn.commit()

# 1. Приветствие и запуск конвейера сбора данных
@bot.message_handler(commands=['start'])
def start_message(message):
    local_conn = sqlite3.connect('autoservise.db')
    local_cursor = local_conn.cursor()
    local_cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        client_name TEXT,
        car_model TEXT
    )''')
    local_cursor.execute("DELETE FROM clients WHERE user_id = ?", (message.chat.id,))
    local_conn.commit()
    local_conn.close() 
    # Спрашиваем имя и приказываем боту перенаправить следующий ответ пользователя в функцию get_name
    msg = bot.send_message(message.chat.id, "👋 Приветствуем в ИИ-сервисе автотехцентра! Как к вам можно обращаться? Напишите ваше имя:")
    bot.register_next_step_handler(msg, get_name)

# 2. Ловим имя и спрашиваем машину
def get_name(message):
    user_name = message.text # Запоминаем имя, которое написал клиент
    
    # Передаем имя дальше в следующий шаг через хитрый параметр (user_name=user_name)
    msg = bot.send_message(message.chat.id, f"Приятно познакомиться, {user_name}! Какая у вас марка и модель автомобиля? (Например: Toyota Camry)")
    bot.register_next_step_handler(msg, get_car, user_name)

# 3. Ловим машину и консервируем всё в базу данных SQL!
def get_car(message, user_name):
    car_model = message.text # Запоминаем машину
    
    # Открываем нашу новую базу данных и записываем готового клиента
    local_conn = sqlite3.connect('autoservice.db')
    local_cursor = local_conn.cursor()
    local_cursor.execute("INSERT INTO clients (user_id, client_name, car_model) VALUES (?, ?, ?)", 
                         (message.chat.id, user_name, car_model))
    local_conn.commit()
    local_conn.close()
    
    bot.send_message(message.chat.id, f"✅ Отлично! Ваш профиль успешно занесен в CRM-систему.\n👤 Клиент: {user_name}\n🚗 Машина: {car_model}\n\nТеперь вы можете задать ИИ-мастеру любой вопрос по ремонту или стоимости обслуживания!")

# Основной обработчик текста с контекстом клиента и математикой
@bot.message_handler(content_types=['text'])
def handle_client_text(message):
    waiting_msg = bot.send_message(message.chat.id, "🔧 ИИ-мастер изучает ваш вопрос, подождите секунду...")

    local_conn = sqlite3.connect('autoservice.db')
    local_cursor = local_conn.cursor()
    local_cursor.execute("SELECT client_name, car_model FROM clients WHERE user_id = ?", (message.chat.id,))
    client_data = local_cursor.fetchone()
    local_conn.close()
    # Если клиент пропустил /start, даём ему базовые имена
    if client_data:
        name = client_data[0]
        car = client_data[1]
    else:
        name = "Уважаемый клиент"
        car = "ваш автомобиль"

# МАТЕМАТИЧЕСКИЙ БЛОК: Автоматический расчет базовой стоимости (STEM)
# Если клиент спрашивает про цену, колодки или масло, задаем базовую ставку
    base_price_text = ""
    user_query = message.text.lower()
    car_brand = car.lower().strip()
    if "колодк" in user_query: 
        if "lexus" in car_brand or "toyota" in car_brand or "bmw" in car_brand or "mersedes" in car_brand:
            work_cost = 2500
            parts_cost = 4500
            class_name = "премиум-класс"
        else:
            work_cost = 1500
            parts_cost = 1800
            class_name = "стандарт-класс"
        total_price = work_cost + parts_cost # Работа + расходники (пример расчета)
        base_price_text = f"Стоимость замены колодок для вашего автомобиля {car} ({class_name}) составляет: работа - {work_cost} руб., колодки - {parts_cost} руб. Итого под ключ: {total_price} рублей."

    elif "масл" in user_query:
        if "lexus" in car_brand or "toyota" in car_brand or "bmw" in car_brand or "mersedes" in car_brand:
            work_cost = 9000
            parts_cost = 14500
            class_name = "премиум-класс"
        else:
            work_cost = 3100
            parts_cost = 5500
            class_name = "стандарт-класс"
        total_price = work_cost + parts_cost # Работа + расходники (пример расчета)
        base_price_text = f"Стоимость замены масла для вашего автомобиля {car} ({class_name}) составляет: работа - {work_cost} руб., масло и фильтр - {parts_cost} руб. Итого под ключ: {total_price} рублей."
    elif "диагност" in user_query:
        price = 5500
        base_price_text = f" Стоимость комплексной диагностики: {price} рублей."

    try:
    # Отправляем ИИ промпт, в который вшиты имя клиента, машина и наша математика!
        completion = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Ты старший мастер-приёмщик в автосервисе. Твоя задача - проконсультировать клиента по имени {name} для его автомобиля {car}. Вот точная цена из нашей системы: '{base_price_text}'. Обязательно назови её клиенту! Отвечай вежливо, профессионально и коротко (до 3-4 тезисов).В конце предложи записаться на ремонт!"
                },
                {"role": "user", "content": message.text}
            ]
        ) 
        ai_responce = completion.choices[0].message.content
        bot.delete_message(message.chat.id, waiting_msg.message_id)
        bot.send_message(message.chat.id, ai_responce)
    except Exception as e:
        bot.delete_message(message.chat.id, waiting_msg.message_id)
        bot.send_message(message.chat.id, f"❌ Не удалось связаться с ИИ-мастнром. Ошибка: {e}")       

bot.infinity_polling()

print("🚀 База данных автосервиса успешно создана! Бот готов к программированию.")
