import random
import vk_api
from flask import Flask, request, json
from datetime import timedelta, datetime, time

app = Flask(__name__)

vk = vk_api.VkApi(token='your_token')

# ----------------Variables----------------

curriculum_builders = set()  # Словарь id бесед, где составляют расписание
curriculum_reseters = set()
classes_curriculum = {}  # Словарь id бесед, значением которых является расписание
classes_subjects = {}  # Словарь id бесед со значениями множеств предметов
days = ('mo', 'tu', 'we', 'th', 'fr', 'sa', 'su')
rus_days = ('Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье')
curriculum_eg = "Русский язык,\n" \
                "Алгебра,\n" \
                "Геометрия,\n" \
                "\n" \
                "Английский язык,\n" \
                "Французский язык,\n" \
                "Геометрия,\n" \
                "\n" \
                "Геометрия,\n" \
                "Биология,\n" \
                "География,\n" \
                "Обществознание,\n" \
                "\n" \
                "Геометрия,\n" \
                "История,\n" \
                "Русский язык,\n" \
                "\n" \
                "Алгебра,\n" \
                "Русский язык"
classes_home_tasks = {}  # Словарь id бесед, с домашним заданием формата (<предмет>, <дата урока, на который задан>): <задание>

# ----------------Variables----------------


def get_now_date():
    return (datetime.now() + timedelta(hours=5)).date()


def get_next_lesson_date(subject, curriculum):
    today_weekday = get_now_date().weekday()
    curriculum += [[] for i in range(7 - len(curriculum))]
    ordered_curriculum = curriculum[today_weekday + 1:] + curriculum[:today_weekday]
    for i, day in enumerate(ordered_curriculum):
        if subject in day:
            return get_now_date() + timedelta(days=i + 1)
    return get_now_date()


def send_message(peer_id, msg):
    vk.method('messages.send', {
        'peer_id': peer_id,
        'message': msg,
        'random_id': random.randint(1, 99999),
    })


def send_message_i_dont_understand(peer_id):
    vk.method('messages.send', {
        'peer_id': peer_id,
        'message': 'Я тебя не понял :(',
        'random_id': random.randint(1, 99999),
    })


@app.route('/', methods=['POST'])
def main():
    global curriculum_reseters, curriculum_builders, classes_curriculum, classes_subjects, classes_home_tasks
    data = json.loads(request.data)
    if data['type'] == 'confirmation':
        return '2b3ebffb'
    elif data['type'] == 'message_new':
        if data['secret'] == 'cffhjbb67hy':
            vk_object = data['object']
            peer_id = vk_object['peer_id']
            body = vk_object['text']
            if peer_id in curriculum_builders:
                try:
                    curriculum = []
                    subjects_set = set()
                    now_day_lessons = []
                    subjects = body.split('\n')
                    assert 0 <= len([a for a in subjects if a == '']) <= 6
                    for subj in subjects:
                        if subj != '':
                            if subj[-1] == ',':
                                subj = subj[:-1]
                            now_day_lessons.append(subj)
                            subjects_set.add(subj)
                        else:
                            curriculum.append(now_day_lessons)
                            now_day_lessons = []
                    curriculum.append(now_day_lessons)
                    classes_curriculum[peer_id] = curriculum
                    classes_subjects[peer_id] = subjects_set
                    send_message(peer_id, 'Я записал ваше расписание в базу данных!')
                    curriculum_builders.discard(peer_id)
                except AssertionError:
                    send_message(peer_id, 'Произошла ошибка. Скорее всего, вы некорректно ввели расписание')
            elif peer_id in curriculum_reseters:
                if body.lower() == 'да':
                    del classes_curriculum[peer_id]
                    curriculum_reseters.discard(peer_id)
                    send_message(
                        peer_id,
                        'Я успешно удалил ваше расписание из базы данных, теперь введите новое расписание\n\n' +
                        'Пример:\n' +
                        curriculum_eg
                    )
                    curriculum_builders.add(peer_id)
                elif body.lower() == 'нет':
                    curriculum_reseters.discard(peer_id)
                    send_message(
                        peer_id,
                        'Хорошо, я не буду убирать ваше расписание из базы данных'
                    )
                else:
                    send_message_i_dont_understand(peer_id)
            else:
                if body.lower() == 'привет':
                    send_message(peer_id, 'Привет, друг!')
                elif body.lower() == 'скинь домашку':
                    if peer_id in classes_home_tasks:
                        home_task_for_tomorrow = ['Задание на следующий учебный день:']
                        for key, task in filter(lambda x: x[1] == get_now_date(), classes_home_tasks[peer_id]):
                            subject = key[0]
                            home_task_for_tomorrow.append(f'{subject} - {task}')
                        send_message(peer_id, '\n'.join(home_task_for_tomorrow))
                    else:
                        send_message(peer_id, 'У вас нет домашнего задания на завтра!')
                elif body.lower() == 'составь наше расписание':
                    if peer_id not in classes_curriculum:
                        send_message(
                            peer_id,
                            "Введите ваше расписание в одном сообщении, разделяя дни двойным enter'ом\n\n" +
                            "Пример:\n" +
                            curriculum_eg
                        )
                        curriculum_builders.add(peer_id)
                    else:
                        send_message(
                            peer_id,
                            'У вас уже есть расписание, вы хотите его перезаписать? (да / нет)'
                        )
                        curriculum_reseters.add(peer_id)
                elif body.lower() == 'скинь наше расписание':
                    if peer_id in classes_curriculum:
                        curriculum = classes_curriculum[peer_id][:]
                        for i, day in enumerate(curriculum):
                            day.insert(0, f'{rus_days[i]}:')
                        message = '\n\n'.join(['\n'.join(day) for day in curriculum])
                    else:
                        message = 'Вы еще не записали свое расписание в базу данных'
                    send_message(
                        peer_id,
                        message
                    )
                elif body.count(': ') == 1:
                    subject, task = body.split(': ')
                    subject = subject.capitalize()
                    task = task.capitalize()
                    if peer_id in classes_curriculum:
                        if subject in classes_subjects[peer_id]: # внутри этогго ифа происходит ошибка
                            peer_curr = classes_curriculum[peer_id]
                            next_lesson = get_next_lesson_date(subject, peer_curr[:])
                            if peer_id in classes_home_tasks:
                                classes_home_tasks[peer_id][(subject, next_lesson)] = task
                            else:
                                classes_home_tasks[peer_id] = {}
                                classes_home_tasks[peer_id][(subject, next_lesson)] = task
                            send_message(peer_id, f'Записал ваше дз:\n{subject} - {task}')
                        else:
                            send_message(peer_id, 'У вас нет такого предмета!')
                    else:
                        send_message(peer_id, 'Вы еще не записали свое расписание в базу данных!')
                else:
                    send_message_i_dont_understand(peer_id)
            return 'ok'
# При отправке домашки бот ничего не пишет
