from aiogram import Bot, Dispatcher, executor, types
import json
import urllib.request
import sqlite3

#подгрузка настроек
settingsFile = open("settings.json", encoding="utf-8")
settings = json.load(settingsFile)

#вввод токена из json
bot = Bot(token=settings["token"])
dispatcher = Dispatcher(bot)

#переменные для проверки админского доступа
isBeginAdding = False
isAdmin = False
adminid = settings["adid"]


#извлечение user id и города из базы данных
def get_weather_user(user: int):
    conn = sqlite3.connect('db/sqlbase_tele.db', check_same_thread=False)
    cursor = conn.cursor()
    print("write-id",user)
    for location, in cursor.execute('SELECT location FROM maintabl WHERE user_id = ?', (user,)):
        place=location
    cursor.close()
    return(get_weather(place))

#запрос города и парсинг нужных параметров json
def get_weather(place: str):
    weather = json.loads(urllib.request.urlopen(f'http://api.openweathermap.org/data/2.5/'
                                                f'weather?q={place}&units=metric&appid=a15417c7ebe0bcce38f2aabdd96f2549&lang=ru').read())
    return(settings["texts"]["weather"].format(str(weather["name"]), str(weather["main"]["temp"]),
                                                             str(weather["wind"]["speed"]),
                                                             str(weather["weather"][0]["description"])))

#регистрация пользователя в бд
def db_table_val(user_id: int, location: str):
    print("start addingg")
    conn = sqlite3.connect('db/sqlbase_tele.db', check_same_thread=False)
    cursor = conn.cursor()
    addin=(user_id, location)
    cursor.execute("INSERT OR REPLACE INTO maintabl (user_id, location) VALUES (?, ?)", addin)
    conn.commit()
    print("ready")
    cursor.close()

#проверка админских прав
@dispatcher.message_handler(commands=['check'])
async def check(message: types.Message):
    global isAdmin
    usr_id = message.from_user.id
    if (str(usr_id) == str(adminid)):
        isAdmin = True
        await message.answer("Доступ разрешён. Функции:\n/regular_send - рассылка всем зарегистрированным пользователям")
    else:
        isAdmin = False
        await message.answer("Доступ запрещён")


#список всех команд
@dispatcher.message_handler(commands=['help'])
async def hellp(message: types.Message):
    await message.answer("Комманды пользователя:\n/start - Начало работы с ботом\n/show_weather - Погода в локации в данный момент\n/register - Регистрация города\n\nФункции админа:\n/check - проверка прав\n")

#вывод погоды
@dispatcher.message_handler(commands=['show_weather'])
async def show(message: types.Message):
    us_id = message.from_user.id
    await message.answer(get_weather_user(us_id))


#рассылка для всех зарегистрированных пользователей
@dispatcher.message_handler(commands=['regular_send'])
async def check_2(message: types.Message):
    global isAdmin
    if isAdmin:

        conn = sqlite3.connect('db/sqlbase_tele.db', check_same_thread=False)
        cursor = conn.cursor()
        print(1)
        userlist=[]
        for user in cursor.execute('SELECT user_id from maintabl'):
            print(1)
            print(*user)
            userlist.append(user)
        for user_id in userlist:
            await bot.send_message(*user_id, get_weather_user(*user_id))
        cursor.close()


#начало работы с ботом
@dispatcher.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Начните с регистрации -> /register\nСписок всех доступных команд -> /help")

#регистрация города
@dispatcher.message_handler(commands=['register'])
async def start(message: types.Message):
    global isBeginAdding
    await message.answer("Введите город на английском, в котором вы проживаете (Пример: Moscow)")
    isBeginAdding = True

#получение user id и города
@dispatcher.message_handler()
async def adding_city(message: types.Message):
    global isBeginAdding
    if isBeginAdding:
        isBeginAdding = False
        input_txt = message.text
        try:
            us_id = message.from_user.id
            location = input_txt
            try:
                await message.answer(get_weather(location))
            except:
                await message.answer('Введённого города не существует или в названии ошибка\nПопробуйте ещё раз:')
                isBeginAdding = True
                return()
            db_table_val(user_id=us_id, location=location)

        except:
            pass



if __name__ == '__main__':
    executor.start_polling(dispatcher, skip_updates=True)

