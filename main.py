import os
import imaplib
import time
import sqlite3
from dotenv import load_dotenv

from googlecalendar import GoogleCalendar


# Загрузка переменных окружения
load_dotenv()

# Подключение к базе данных
db = sqlite3.connect('database.db')
databaseCursor = db.cursor()

obj = GoogleCalendar

def add_to_calendar(info: list):
    event = {
        'start': {
            'dateTime': info[4],
            "timeZone": "Asia/Yekaterinburg"
        },
        'end': {
            'dateTime': info[5],
            "timeZone": "Asia/Yekaterinburg"
        },
        "summary": info[0],
        "location": info[1],
        "description": info[3] + ' ' + info[2]
    }

    obj.add_event(calendar_id=os.getenv('CALENDAR_ID'), body=event)
    print(f"{datetime.now()} : Новое событие добавлено в календарь!")
    # pprint.pprint(obj.get_calendar_list())

def add_event_to_database(info: list):
    query = "INSERT INTO events (summary, description, start, end, location) VALUES(?, ?, ?, ?, ?)"
    summary: str = info[0]
    description: str = info[3] + ' ' + info[2]
    start: str = info[4]
    end: str = info[5]
    location: str = info[1]
    databaseCursor.execute(query, (summary, description, start, end, location))

    db.commit()

    print(f"{datetime.now()}. Произведена запись события из базы данных")

def delete_event_from_database(info: list):
    query = 'DELETE FROM events WHERE summary = ? AND description = ? AND start = ? AND end = ? AND location = ?'
    summary: str = info[0]
    description: str = info[3] + ' ' + info[2]
    start: str = info[4]
    end: str = info[5]
    location: str = info[1]

    databaseCursor.execute(query, (summary, description, start, end, location))

    db.commit()

    print(f"{datetime.now()}. Произведено удаление событие из базы данных")

def parse_message(message) -> list:
    try:
        # task = (message[message.index('Занятие'):message.index('Адрес')]).rstrip()
        task = "Занятие Тренировка с тренером"
        address = (message[message.index('Адрес'):message.index('Тренер')].split('Адрес ')[1]).rstrip()
        client = (message[message.index('Клиент'):message.index('Телефон')]).rstrip()
        phoneNumber = message[message.index('клиента'):message.index('Дата')].split(' ')[1]
        date = (message[message.index('Дата'):message.index('Доступ')].split('Дата ')[1]).rstrip()
    except ValueError:
        print("Не удалось собрать информацию")
    # info = [task, address, date, client, phoneNumber]

    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M')
    iso_date_str = date_obj.isoformat()

    end_date_obj = date_obj + timedelta(hours=1)
    end = end_date_obj.isoformat()
    print(f"Функция parse_message: {[task, address, client, phoneNumber, iso_date_str, end]}")
    return [task, address, client, phoneNumber, iso_date_str, end]


events = obj.get_events(os.getenv('CALENDAR_ID'))
for event in events.get('items', []):
    print(f"Event ID: {event['id'], event['summary'], event['description'], event['start'], event['end']}")

# Подключение к серверу IMAP
conn = imaplib.IMAP4_SSL(os.getenv('IMAP_SERVER'))
conn.login(os.getenv('EMAIL_ADDRESS'), os.getenv('IMAP_PASSWORD'))

def mail():

    # Выбор папки (INBOX)
    status, messages = conn.select('Inbox')
    if status != 'OK':
        print('Ошибка при выборе почтового ящика')
        exit()

    # Поиск непрочитанных сообщений от определенного отправителя
    sender_email = os.getenv('EMAIL_CHECK')
    search_criteria = f'(UNSEEN FROM "{sender_email}")'

    status, messages_ids = conn.search(None, search_criteria)

    # Обработка найденных сообщений
    if status == 'OK':
        for num in messages_ids[0].split():
            typ, data = conn.fetch(num, '(RFC822)')

            # Преобразование байтовых данных в строку
            msg_data = data[0][1]
            msg = BytesParser().parsebytes(msg_data)
            print(f"Новое сообщение от {sender_email}: {msg['subject']}")

            text_part = None
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    text_part = part.get_payload(decode=True).decode('utf-8')

                    with open('text.html', 'a', encoding='utf-8') as file:
                        file.write(text_part)
                        print("Файл успешно записан")
                    break
            if text_part:
                if 'Поступила заявка на запись на занятие' in ' '.join(text_part.split()):
                    print('Текст сообщения:')
                    print(' '.join(text_part.split()))
                    email_current = ' '.join(text_part.split())
                    try:
                        info = parse_message(email_current)
                        body: list = info
                        add_to_calendar(body)
                        add_event_to_database(info)
                    except Exception as e:
                        print(f"Произошла ошибка, событие не добавлено, либо же клиент отменил заявку. Код ошибки: {e}")
                elif 'Клиент отменил занятие' in ' '.join(text_part.split()):
                    print('Текст сообщения:')
                    print(' '.join(text_part.split()))
                    email_current = ' '.join(text_part.split())
                    try:
                        info = parse_message(email_current)
                        body: list = info
                        events_ = obj.get_events(os.getenv('CALENDAR_ID'))

                        for googleEvent in events_.get('items', []):
                            if googleEvent['summary'] == info[0] and googleEvent['description'] == info[3] + ' ' + info[2] and \
                                    googleEvent['start'] == info[4] and googleEvent['end'] == info[5] and googleEvent['location'] == info[1]:

                                obj.delete_event(calendar_id=os.getenv('CALENDAR_ID'), eventId=googleEvent['id'])
                                delete_event_from_database(info)
                    except Exception as e:
                        print(f"Произошла ошибка, событие не добавлено, либо же клиент отменил заявку. Код ошибки: {e}")
            else:
                print('Сообщение не содержит текстовой части')
    else:
        print("Ошибка при поиске сообщений")

    conn.close()

while True:
    mail()
    time.sleep(5)
    print(f"{datetime.now()}. Проведена проверка почты, новых писем не найдено")
