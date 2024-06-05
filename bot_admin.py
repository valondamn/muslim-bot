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

# Словарь для хранения корзин пользователей
user_carts = {}

# Асинхронная функция для добавления продукта
async def add_product(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 5:
        await update.message.reply_text("Использование: /add_product <name> <description> <price> <stock> <image>")
        return

    name = context.args[0]
    # Описание продукта - это все аргументы между именем продукта и ценой
    description = ' '.join(context.args[1:-3])
    price = context.args[-3]
    stock = context.args[-2]
    image = context.args[-1]

    print(f"Adding product with: name={name}, description={description}, price={price}, stock={stock}, image={image}")

    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO products (name, description, price, stock, image) VALUES (%s, %s, %s, %s, %s)",
                (name, description, price, stock, image)
            )
            connection.commit()
            await update.message.reply_text(f"Продукт {name} добавлен успешно.")
        except mysql.connector.Error as error:
            await update.message.reply_text(f"Ошибка при добавлении продукта: {error}")
        finally:
            cursor.close()
            connection.close()
    else:
        await update.message.reply_text("Ошибка подключения к базе данных.")
# Асинхронная функция для удаления продукта
async def delete_product(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 1:
        await update.message.reply_text("Использование: /delete_product <product_id>")
        return

    product_id = context.args[0]

    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
            connection.commit()
            await update.message.reply_text(f"Продукт с ID {product_id} удален успешно.")
        except mysql.connector.Error as error:
            await update.message.reply_text(f"Ошибка при удалении продукта: {error}")
        finally:
            cursor.close()
            connection.close()
    else:
        await update.message.reply_text("Ошибка подключения к базе данных.")

# Асинхронная функция для редактирования продукта
async def edit_product(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 5:
        await update.message.reply_text("Использование: /edit_product <product_id> <name> <description> <price> <stock> <image>")
        return

    product_id = context.args[0]
    name = context.args[1]
    description = context.args[2]
    price = context.args[3]
    stock = context.args[4]
    image = context.args[5]

    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE products SET name = %s, description = %s, price = %s, stock = %s, image = %s WHERE product_id = %s",
                (name, description, price, stock, image, product_id)
            )
            connection.commit()
            await update.message.reply_text(f"Продукт с ID {product_id} обновлен успешно.")
        except mysql.connector.Error as error:
            await update.message.reply_text(f"Ошибка при редактировании продукта: {error}")
        finally:
            cursor.close()
            connection.close()
    else:
        await update.message.reply_text("Ошибка подключения к базе данных.")

# Основная функция для запуска бота
def main():
    # Проверяем подключение к базе данных перед запуском бота
    if not connect_to_db():
        return

    # Создайте экземпляр ApplicationBuilder и передайте ему токен вашего бота
    application = ApplicationBuilder().token("7323825444:AAEZ2tXnNjyKHkRPvImH2fBMoOt_E_506sc").build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("add_product", add_product))
    application.add_handler(CommandHandler("delete_product", delete_product))
    application.add_handler(CommandHandler("edit_product", edit_product))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
