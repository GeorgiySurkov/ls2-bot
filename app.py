import random
import vk_api
from flask import Flask, request, json

app = Flask(__name__)

vk = vk_api.VkApi(token='your_token')

# ----------------Variables----------------

curriculum_builders = set()  # Словарь id бесед, где составляют расписание
curriculum_reseters = set()
classes_curriculum = {}  # Словарь id бесед, значением которых является список предметов
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

# ----------------Variables----------------


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
                    day_i = 0
                    curriculum = {}
                    subjects = body.split('\n')
                    for subj in subjects:
                        now_day = days[day_i]
                        if subj != '':
                            if subj[-1] == ',':
                                subj = subj[:-1]
                            if now_day in curriculum:
                                curriculum[now_day].append(subj)
                            else:
                                curriculum[now_day] = []
                                curriculum[now_day].append(subj)
                        else:
                            day_i += 1
                    classes_curriculum[peer_id] = curriculum
                    send_message(peer_id, 'Я записал ваше расписание в базу данных!')
                    curriculum_builders.discard(peer_id)
                except KeyError:
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
                    send_message(
                        peer_id,
                        'Пока такой функции у меня нет, я только могу отвечать на самые простые сообщения'
                    )
                elif body.lower() == 'составь расписание':
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
                        curriculum = classes_curriculum[peer_id]
                        curr_list = []
                        for i in range(len(curriculum)):
                            curr_list.append([rus_days[i] + ':'] + curriculum[days[i]])
                        message = '\n\n'.join(['\n'.join(day) for day in curr_list])
                    else:
                        message = 'Вы еще не записали свое расписание в базу данных'
                    send_message(
                        peer_id,
                        message
                    )
                else:
                    send_message_i_dont_understand(peer_id)
            return 'ok'
