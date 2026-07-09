import os
import telebot
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
from telebot import types  # Наш вчерашний штурм импорта кнопок!

# Контрольный датчик пути (его можно оставить или стереть)
print("📍 ВНИМАНИЕ! Бот сейчас физически работает в папке:", os.getcwd())


# 1. Загружаем секретные ключи безопасности
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

ai_client = OpenAI(
    api_key=os.getenv("PROXY_API_KEY"),
    base_url="https://api.proxyapi.ru/openai/v1"
)

# 2. Создаем новую Базу Данных для автосервиса
# Намертво привязываем базу данных к текущей папке бота!
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'autoservice.db')

conn = sqlite3.connect(db_path, check_same_thread=False)

cursor = conn.cursor()

# Создаем таблицу клиентов СТО (ID, Имя, Телефон, Марка машины)
cursor.execute('''
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    client_name TEXT,
    car_model TEXT
)''')
# Создаем таблицу ПРАЙС-ЛИСТА (Услуга, Цена Стандарт, Цена Премиум, Запчасти)
cursor.execute('''
CREATE TABLE IF NOT EXISTS price_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_keyword TEXT,  
    price_standard INTEGER, 
    price_premium INTEGER,  
    parts_cost INTEGER      
)''')
cursor.execute("SELECT COUNT(*) FROM price_list")
if cursor.fetchone()[0] == 0:
    services = [
        ('колодк', 1500, 2500, 1800),
        ('масл', 1000, 2000, 3500),
        ('диагност', 1200, 2500, 0),
        ('шаров', 1800, 3500, 2200),
        ('проводк', 2000, 4500, 2500)
    ]
    cursor.executemany("INSERT INTO price_list (service_keyword, price_standard, price_premium, parts_cost) VALUES (?, ?, ?, ?)", services)
# Создаем таблицу ЗАПИСЕЙ НА РЕМОНТ (Календарь СТО)
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    client_name TEXT,
    car_model TEXT,
    service_name TEXT,
    booking_date TEXT,
    booking_time TEXT
    )''')           
                  
cursor.execute("SELECT COUNT(*) FROM orders")
if cursor.fetchone()[0] == 0:
    fake_orders = [
        (111222, 'Иван', 'Toyota', 'замена масла', '08.07', '09:00'),
        (333444, 'Олег', 'BMW', 'замена колодок', '08.07', '15:00')
    ]
    cursor.executemany("INSERT INTO orders (user_id, client_name, car_model, service_name, booking_date, booking_time) VALUES (?, ?, ?, ?, ?, ?)", fake_orders)
conn.commit()

# 1. Приветствие и запуск конвейера сбора данных
@bot.message_handler(commands=['start'])
def start_message(message):
    local_conn = sqlite3.connect(db_path)
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
    local_conn = sqlite3.connect(db_path)
    local_cursor = local_conn.cursor()
    local_cursor.execute("INSERT INTO clients (user_id, client_name, car_model) VALUES (?, ?, ?)", 
                         (message.chat.id, user_name, car_model))
    local_conn.commit()
    local_conn.close()
    # 🛠️ СОЗДАЕМ ИНЛАЙН-КНОПКУ ЗАПИСИ ПРЯМО ЗДЕСЬ 
    inline_markup = types.InlineKeyboardMarkup()
    btn_booking = types.InlineKeyboardButton(text="📅 Записаться на ремонт", callback_data="test_click")
    inline_markup.add(btn_booking) 
    
    bot.send_message(
        message.chat.id, 
        f"✅ Отлично! Ваш профиль успешно занесен в CRM-систему.\n👤 Клиент: {user_name}\n🚗 Машина: {car_model}\n\nТеперь вы можете общаться с ИИ-мастером или сразу выбрать время для визита к нам:",
        reply_markup=inline_markup # Прикрепили кнопку!
    )

@bot.message_handler(func=lambda message: message.text.lower() == "запись")
def ask_for_booking(message):
    inline_markup = types.InlineKeyboardMarkup() # Проверь, чтобы было types, а не tepes!
    
    btn_info = types.InlineKeyboardButton(text="📅 Выбрать Время", callback_data="test_click")
    inline_markup.add(btn_info) 
    
    # ИСПРАВЛЕНО: прикрепляем нашу переменную inline_markup вместо "text_markup"
    bot.send_message(message.chat.id, "Для записи на ремонт нажмите кнопку ниже:", reply_markup=inline_markup)



# Основной обработчик текста с контекстом клиента и математикой
@bot.message_handler(content_types=['text'])
def handle_client_text(message):
    waiting_msg = bot.send_message(message.chat.id, "🔧 ИИ-мастер изучает ваш вопрос, подождите секунду...")

    local_conn = sqlite3.connect(db_path)
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
    user_query = message.text.lower().strip()
    car_brand = car.lower().strip()
    if "lexus" in car_brand or "toyota" in car_brand or "bmw" in car_brand or "mersedes" in car_brand or "touareg" in car_brand:
        is_premium = True
        class_name = "премиум-класс"
    else:
        is_premium = False
        class_name = "стандарт-класс"

    local_conn = sqlite3.connect('autoservice.db')
    local_cursor = local_conn.cursor()
    local_cursor.execute("SELECT service_keyword, price_standard, price_premium, parts_cost FROM price_list")
    all_services = local_cursor.fetchall()
    local_conn.close()

    for row in all_services:
        keyword = row[0] # наше ключевое слово из базы (например: шаров, проводк)
        
        if keyword in user_query:
            # Вытаскиваем тарифы из строки базы данных (STEM)
            price_standard = row[1]
            price_premium = row[2]
            parts_cost = row[3]
            
            # На ходу выбираем нужную колонку в зависимости от класса авто (STEM)
            if is_premium:
                work_cost = price_premium
            else:
                work_cost = price_standard
                
            # Математика Python сама считает итоговую сумму под ключ (STEM)
            total_price = work_cost + parts_cost
            base_price_text = f"Стоимость ремонта для вашего автомобиля {car} ({class_name}) составляет: работа — {work_cost} руб., необходимые расходники/детали — {parts_cost} руб. Итого под ключ: {total_price} рублей."
            break 

    try:
    # Отправляем ИИ промпт, в который вшиты имя клиента, машина и наша математика!
        completion = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Ты старший мастер-приёмщик в автосервисе. Твоя задача - проконсультировать клиента по имени {name} для его автомобиля {car}. Вот точная цена из нашей системы: '{base_price_text}'. Обязательно назови её клиенту! Отвечай вежливо, профессионально и коротко (до 3-4 тезисов).В конце предложи записаться на ремонт и сделай предуприждение, если вовремя не сделать данную работу, то возможна поломка автомобиля!"
                },
                {"role": "user", "content": message.text}
            ]
        ) 
        ai_responce = completion.choices[0].message.content
        bot.delete_message(message.chat.id, waiting_msg.message_id)
        inline_markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(text='📅Записаться на ремонт',callback_data="test_click")
        inline_markup.add(btn)
        bot.send_message(message.chat.id, ai_responce, reply_markup=inline_markup)
    except Exception as e:
        bot.delete_message(message.chat.id, waiting_msg.message_id)
        bot.send_message(message.chat.id, f"❌ Не удалось связаться с ИИ-мастнром. Ошибка: {e}")       

@bot.callback_query_handler(func=lambda call: call.data == "test_click")
def show_calendar(call):
    bot.answer_callback_query(call.id)
    all_hours = ["09:00", "12:00", "15:00", "17:00"]
    local_conn = sqlite3.connect(db_path)
    local_cursor = local_conn.cursor()
    local_cursor.execute("SELECT booking_time FROM orders WHERE booking_date = '08.07'") 
    busy_rows = local_cursor.fetchall()
    local_conn.close()

    busy_hours = [row[0] for row in busy_rows]
    time_markup = types.InlineKeyboardMarkup()

    for hour in all_hours:
        if hour in busy_hours:
            btn = types.InlineKeyboardButton(text=f"❌ {hour} (Занято)", callback_data="busy_time")
        else:
            btn = types.InlineKeyboardButton(text=f"🟢 {hour}", callback_data=f"book_{hour}")
        time_markup.add(btn)   
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📅 Доступное время для записи на сегодня (08.07):\n🟢 — Свободно\n❌ — Занято",
        reply_markup=time_markup
    )
@bot.callback_query_handler(func=lambda call: call.data.startswith("book_"))
def save_booking_to_sql(call):
    bot.answer_callback_query(call.id)
    selected_time = call.data.replace("book_", "")
    local_conn = sqlite3.connect(db_path)
    local_cursor = local_conn.cursor()
    local_cursor.execute("SELECT client_name, car_model FROM clients WHERE user_id = ?", (call.message.chat.id,))
    client_data = local_cursor.fetchone()
    if client_data:
        name = client_data[0]
        car = client_data[1]
    else:
        name = "Неизвестный"
        car = "Автомобиль"
    local_cursor.execute(
        "INSERT INTO orders (user_id, client_name, car_model, service_name, booking_date, booking_time) VALUES (?, ?, ?, ?, ?, ?)",
        (call.message.chat.id, name, car, "Комплексный ремонт/ТО", "08.07", selected_time)
    )
    local_conn.commit()
    local_conn.close()
 
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"🥳 **Успешная запись на ремонт!**\n\n👤 **Мастер принял заявку на имя**: {name}\n🚗 **Автомобиль**: {car}\n📅 *Дата**: 08.07 (Сегодня)\n⏰ **Точное время**: {selected_time}\n\nЖдём ВАС в нашем автотехцентре!",
        reply_markup=None
    )

bot.infinity_polling()

print("🚀 База данных автосервиса успешно создана! Бот готов к программированию.")
