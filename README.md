# Автономный ИИ-Приемщик и SQL-CRM для Автотехцентра / AI Service Advisor & SQL CRM

Разработчик / Developer: Дмитрий (Zlatoust, Russia)
Бизнес-горизонт / Strategy: SAAS Platform 2026-2031

---

## 🇷🇺 Описание проекта (Russian)
Интеллектуальная CRM-система и автоматический робот-приемщик для автосервиса под управлением AI, полностью автоматизирующий воронку продаж, расчет стоимости ремонта и бронирование времени.

### Основной функционал:
*   **Двухуровневый SQL-Прайс (SQLite3):** Python-движок сканирует динамическую таблицу `price_list`, автоматически разделяет автомобили на эконом и премиум-классы (включая Touareg, Lexus, BMW) и на лету вычисляет итоговую стоимость работы и запчастей по тысячам наименований ремонта.
*   **Интерактивный SQL-Календарь (`orders`):** Живая сетка времени с кнопками `InlineKeyboardMarkup`. Бот считывает занятые часы из базы, выводит клиенту свободные окна (`🟢`), а после клика хирургически блокирует выбранный час (`❌`) через SQL-команды, исключая дубликаты.
*   **Маркетинговая воронка (Актуализация боли):** ИИ-клиент (GPT-4o-mini) жестко зажат в тиски системного промпта. Робот не просто называет цену, а отрабатывает возражения, объясняет последствия неисправности (например, разрушение тормозной системы) и закрывает сделку кнопкой записи прямо под ответом.
*   **Абсолютная безопасность:** Изоляция API-ключей и баз данных через переменные окружения (`.env`) и сквозной щит `.gitignore`. Полная защита путей Windows через `os.path.abspath`.

---

## 🇺🇸 Project Description (English)
An advanced, production-ready Telegram bot and SQL CRM that fully automates the sales funnel, service cost estimation, and real-time bay scheduling for automotive service centers.

### Key Features:
*   **Multi-Tier SQL Price Engine:** Dynamically queries the `price_list` table, auto-classifies vehicles into Standard/Premium classes, and computes total turn-key repair costs.
*   **Interactive SQL Booking Calendar:** Dynamic inline time-slot matrix (`orders`). Displays open slots (`🟢`), blocks reserved slots (`❌`), and wipes the interface upon checkout to prevent double-booking.
*   **Sales Funnel & AI Advisor (GPT-4o-mini):** Programmed to inject proactive urgency (e.g., brake system failure consequences) alongside custom price hydration, maximizing booking conversion rates.

---

### Технологический стек / Tech Stack:
Python 3.14, pyTelegramBotAPI (Telebot), SQLite3, OpenAI API (ProxyAPI), Python-dotenv, Git, GitHub.
