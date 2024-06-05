import mysql.connector
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext

# Функция для подключения к базе данных
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            database="shop_db"
        )
        return connection
    except mysql.connector.Error as error:
        print("Ошибка подключения к базе данных:", error)
        return None

# Функция для получения списка продуктов из базы данных
def get_products():
    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT product_id, name, price FROM products")
        products = cursor.fetchall()
        cursor.close()
        connection.close()
        return products
    else:
        return None

# Функция для проверки наличия продукта на складе
def check_product_availability(product_id):
    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT stock FROM products WHERE product_id = %s", (product_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        if result:
            stock = result[0]
            return stock > 0
        else:
            return False
    else:
        return False

# Словарь для хранения корзин пользователей
user_carts = {}

# Асинхронная функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Я бот вашего интернет-магазина. Используйте /help для получения списка доступных команд.')

# Асинхронная функция для обработки команды /products
async def products(update: Update, context: CallbackContext) -> None:
    products = get_products()
    if products:
        response = "Список товаров:\n"
        for product in products:
            product_id = product[0]
            name = product[1]
            price = product[2]
            response += f"{product_id}. {name}: {price} руб."
    else:
        response = "Произошла ошибка при получении списка товаров из базы данных."
    await update.message.reply_text(response)

# Асинхронная функция для добавления продукта в корзину
async def add_to_cart(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Проверяем, передан ли product_id
    if context.args:
        try:
            product_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Пожалуйста, укажите корректный product_id.")
            return

        # Проверяем наличие продукта на складе
        if check_product_availability(product_id):
            # Инициализируем корзину пользователя, если её нет
            if user_id not in user_carts:
                user_carts[user_id] = []
            # Добавляем продукт в корзину пользователя
            user_carts[user_id].append(product_id)
            await update.message.reply_text(f"Продукт с product_id {product_id} добавлен в вашу корзину.")
        else:
            await update.message.reply_text("Товара нет в наличии.")
    else:
        await update.message.reply_text("Пожалуйста, укажите product_id для добавления в корзину.")

# Асинхронная функция для просмотра корзины
async def view_cart(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cart = user_carts.get(user_id, [])

    if not cart:
        await update.message.reply_text("Ваша корзина пуста.")
    else:
        connection = connect_to_db()
        if connection:
            cursor = connection.cursor()
            cart_details = []
            for product_id in cart:
                cursor.execute("SELECT name, price FROM products WHERE product_id = %s", (product_id,))
                product = cursor.fetchone()
                if product:
                    cart_details.append(product)
            cursor.close()
            connection.close()

            response = "Ваша корзина:\n"
            for product in cart_details:
                name = product[0]
                price = product[1]
                response += f"{name}: {price} руб.\n"

            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Произошла ошибка при получении информации о корзине.")

# Функция для оформления заказа
def create_order(user_id, cart):
    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()

        try:
            # Рассчитываем общую стоимость заказа
            total = 0
            for product_id in cart:
                cursor.execute("SELECT price FROM products WHERE product_id = %s", (product_id,))
                product = cursor.fetchone()
                if product:
                    total += product[0]

            # Создаем новый заказ
            cursor.execute("INSERT INTO orders (user_id, total) VALUES (%s, %s)", (user_id, total))
            order_id = cursor.lastrowid

            # Добавляем детали заказа
            for product_id in cart:
                cursor.execute("SELECT price FROM products WHERE product_id = %s", (product_id,))
                product = cursor.fetchone()
                if product:
                    price = product[0]
                    cursor.execute(
                        "INSERT INTO order_details (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                        (order_id, product_id, 1, price)
                    )

            connection.commit()
            return order_id
        except mysql.connector.Error as error:
            connection.rollback()
            print("Ошибка создания заказа:", error)
            return None
        finally:
            cursor.close()
            connection.close()
    else:
        return None

# Асинхронная функция для обработки команды /checkout
async def checkout(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cart = user_carts.get(user_id, [])

    if not cart:
        await update.message.reply_text("Ваша корзина пуста.")
    else:
        order_id = create_order(user_id, cart)
        if order_id:
            user_carts[user_id] = []  # Очищаем корзину после успешного оформления заказа
            await update.message.reply_text(f"Ваш заказ успешно оформлен! Номер заказа: {order_id}")
        else:
            await update.message.reply_text("Произошла ошибка при оформлении заказа.")

# Основная функция для запуска бота
def main():
    # Проверяем подключение к базе данных перед запуском бота
    if not connect_to_db():
        return

    # Создайте экземпляр ApplicationBuilder и передайте ему токен вашего бота
    application = ApplicationBuilder().token("6968827207:AAH1OMak9Waf8QTYx_tjy3U9XsJTRo6SU3A").build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("products", products))
    application.add_handler(CommandHandler("add_to_cart", add_to_cart))
    application.add_handler(CommandHandler("view_cart", view_cart))
    application.add_handler(CommandHandler("checkout", checkout))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
