import re
import os
import asyncio
import requests
from datetime import datetime, timedelta, date
from threading import Thread
from time import sleep

from flask import Flask, request, make_response, Response, stream_with_context
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import Play, VoiceResponse
from twilio.rest import Client

account_sid = os.environ.get('TWILIO_SID')
auth_token = os.environ.get('TWILIO_AUTH')
STATUS_URL = 'https://glacial-hollows-80092.herokuapp.com/checkgame'

client = Client(account_sid, auth_token)

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()
new_loop = asyncio.new_event_loop()
t = Thread(target=start_loop, args=(new_loop,))
t.start()

class Cookies():
    FIRST_TIME = 'first_time'
    STAGE = 'stage'
    OPT_IN = 'opt_in'
    NAME = 'name'
    GENDER = 'gender'
    BIRTHDAY = 'birthday'

app = Flask(__name__)

@app.route('/soundsgame.xml', methods=['GET', 'POST'])
def soundsgame_xml():
    response = VoiceResponse()
    response.play('https://vroom-chicago-demo.s3.amazonaws.com/soundsgame.mp3')
    return Response(str(response), mimetype='text/xml')

@app.route('/checkgame', methods=['GET', 'POST'])
def checkgame():
        name = request.cookies.get(Cookies.NAME)
        twilio_resp = MessagingResponse()
        if request.values.get('SmsStatus') == 'delivered':
            message = 'Did they like the activity? Reply YES/NO'
            from_num = request.form['From']
            to_num = request.form['To']
            client.messages.create(
                to=to_num,
                from_=from_num,
                body=message,
            )

        resp = make_response(str(twilio_resp))
        return resp

@app.route("/sms", methods=['GET', 'POST'])
def sms():
    first_time = request.cookies.get(Cookies.FIRST_TIME) != 'False'
    stage = int(request.cookies.get(Cookies.STAGE, 0))
    body = request.form['Body'].lower().strip()
    from_num = request.form['To']
    to_num = request.form['From']
    print('STAGE -------- ', stage)

    if body == 'restart':
        return end()

    if body == 'menu':
        return menu()
    if body == 'lullaby':
        return lullaby()
    if body == 'appointment':
        return appointment()
    if body == 'resume':
        stage = stage - 1

    if first_time and body == 'sesame':
        return first_time_response()

    if stage == 0:
        twilio_resp = MessagingResponse()
        resp = make_response(str(twilio_resp))
        return resp

    if stage == 1:
        return opt_in()

    if stage < 5:
        return setup_account(stage)

    if stage < 9:
        return a_game(stage)

    if stage < 11:
        return b_game(stage)

    if stage < 13:
        return c_game(stage)

    if stage == 15:
        return e_game(stage)


def first_time_response():
    message = 'Welcome to the Sesame Seeds Home proof-of-concept. Text “STOP” at any time. Text “OK” to begin.'
    twilio_resp = MessagingResponse()
    twilio_resp.message(message)

    resp = make_response(str(twilio_resp))
    resp.set_cookie(Cookies.FIRST_TIME, str(False))
    resp.set_cookie(Cookies.STAGE, str(1))

    return resp

def opt_in():
    user_response = request.form['Body'].lower()
    if user_response not in ['ok', 'yes']:
        return end()

    message = 'Assalamualaikum! Let’s get started: what is your child’s name?'
    twilio_resp = MessagingResponse()
    twilio_resp.message(message)

    resp = make_response(str(twilio_resp))
    resp.set_cookie(Cookies.STAGE, str(5))
    resp.set_cookie(Cookies.OPT_IN, str(True))

    return resp

def setup_account(stage):
    if stage == 2: # Ask gender
        name = request.form['Body']
        message = 'Is {} a boy or girl?'.format(name)
        twilio_resp = MessagingResponse()
        twilio_resp.message(message)

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.NAME, name)
        resp.set_cookie(Cookies.STAGE, str(3))
        return resp

    if stage == 3: # Ask birthday
        gender = request.form['Body'].lower()
        if gender not in ['boy', 'girl']:
            twilio_resp = MessagingResponse()
            twilio_resp.message('Please respond "boy" or "girl"')
            return str(twilio_resp)
        pronoun = 'his' if gender == 'boy' else 'her'
        message = 'What’s {} birthday? Use dd/mm/yy'.format(pronoun)
        twilio_resp = MessagingResponse()
        twilio_resp.message(message)

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.GENDER, gender)
        resp.set_cookie(Cookies.STAGE, str(4))
        return resp

    if stage == 4: # Finish setup
        birthday = request.form['Body']
        name = request.cookies.get(Cookies.NAME)
        try:
            birthday_date = datetime.strptime(birthday, '%d/%m/%y')
        except:
            twilio_resp = MessagingResponse()
            twilio_resp.message('Please respond with a date formatted dd/mm/yy')
            return str(twilio_resp)

        birthday_date = datetime.strptime(birthday, '%d/%m/%y')
        message1 = check_birthday(birthday_date)
        message1 += 'Great! You will receive age-tailored activities for you and {} to do together. And we’ll teach you the science behind it all!'.format(name)
        message2 = 'If you need help, text `HELP` If you want to opt out, text `STOP` and we’ll unenroll you immediately.'

        from_num = request.form['To']
        to_num = request.form['From']
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message1,
        )
        sleep(1.5)

        twilio_resp = MessagingResponse()
        twilio_resp.message(message2)

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.BIRTHDAY, str(birthday))
        resp.set_cookie(Cookies.STAGE, str(5))
        return resp

    return end()

def check_birthday(birthday_date):
    now = datetime.today()

    if birthday_date.month == now.month and birthday_date.day == now.day:
        return 'Happy Birthday!\n'
    return ''


def menu():
    message = '''Options:

    1. Quit
    2. Restart
    3. Resume'''
    twilio_resp = MessagingResponse()
    twilio_resp.message(message)
    return make_response(str(twilio_resp))

def lullaby():
    from_num = request.form['To']
    to_num = request.form['From']
    client.calls.create(
        to=to_num,
        from_=from_num,
        url="https://glacial-hollows-80092.herokuapp.com/soundsgame.xml" # TODO: Change this
    )
    twilio_resp = MessagingResponse()
    return make_response(str(twilio_resp))

def appointment():
    name = request.cookies.get(Cookies.NAME) if request.cookies.get(Cookies.NAME) else 'you'
    tdate = date.today() + timedelta(days=1)
    tomorrow = tdate.strftime('%A, %B %dth')
    message = f'Good evening! Myriam will visit you tomorrow, {tomorrow} at 12:15pm. She will bring a new storybook for {name}.'
    twilio_resp = MessagingResponse()
    twilio_resp.message(message)
    return make_response(str(twilio_resp))


def a_game(stage):
    name = request.cookies.get(Cookies.NAME)
    from_num = request.form['To']
    to_num = request.form['From']
    if False: # Intro game
        name = request.form['Body'].strip()
        now = datetime.now().strftime('%A, %B %dth')
        message = 'It’s {}. Time for today’s game! Today, we’ll do Hide and Seek, which is great for children like {}. Text “OK” to get started.'.format(now, name)
        twilio_resp = MessagingResponse()
        twilio_resp.message(message)

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.STAGE, str(6))
        resp.set_cookie(Cookies.NAME, name)
        return resp
    if stage == 5 or stage == 6: # Confirm start
        name = request.form['Body'].strip()
        now = datetime.now().strftime('%A, %B %dth')
        message1 = f'It’s {now}. Time for today’s activity! Hiding games are fun for all ages. For babies, briefly hide your face behind your hands or a cloth.  WATCH how Tonton plays: http://bit.ly/2koa0Hj'
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message1,
        )
        sleep(1.5)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body='',
            media_url='https://user-images.githubusercontent.com/541325/33525186-c816c084-d865-11e7-8eff-2a25e5498c33.jpg',
            status_callback=STATUS_URL,
        )
        sleep(1.5)
        twilio_resp = MessagingResponse()
        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.STAGE, str(7))
        resp.set_cookie(Cookies.NAME, name)
        return resp
    if stage == 7 or stage == 8:
        response = request.form['Body'].strip()
        twilio_resp = MessagingResponse()
        if response.lower() == 'yes':
            message = f'Great! We will send more like this for you and {name}.'
        else:
            message = f'Sorry to hear it! Maybe {name} will like the next one better'

        return b_game(8, to_num, from_num, name)

def b_game(stage, to_num='', from_num='', name='', time=0):
    now = datetime.now().strftime('%A, %B %dth')
    name = request.cookies.get(Cookies.NAME)
    from_num = request.form['To']
    to_num = request.form['From']
    response = request.form['Body']
    if stage == 8 or stage == 9:
        if response.lower() == 'yes':
            resp_message = 'Great! We’ll send you more like this.'
        else:
            resp_message = f'Sorry to hear it! Maybe {name} will like the next one better'
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=resp_message,
        )

        message1 = f'It’s {now}. Time for today’s activity, 123 Jump. WATCH: http://bit.ly/2BBp2Ng'
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message1,
        )
        sleep(1.5)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body='',
            media_url='https://user-images.githubusercontent.com/541325/33525189-c931aa10-d865-11e7-8eb0-26faa1b8b065.png',
            status_callback=STATUS_URL,
        )
        sleep(1.5)
        twilio_resp = MessagingResponse()
        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.STAGE, str(10))
        return resp
    if stage == 10:
        response = request.form['Body']
        twilio_resp = MessagingResponse()
        if response.lower() == 'yes':
            twilio_resp.message('Great! We’ll send you more like this.')
        else:
            twilio_resp.message('Sorry to hear it! Maybe {} will like the next one better'.format(name))

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.STAGE, str(15))
        new_loop.call_soon_threadsafe(c_game, 11, to_num, from_num, name, 2)
        return resp

def c_game(stage, to_num='', from_num='', name='', time=0):
    if stage == 11:
        sleep(time)
        tomorrow = date.today() + timedelta(days=1)
        tomorrow = tomorrow.strftime('%A, %B %dth')
        message = 'Good evening! Myriam will visit you tomorrow, {} at 12:15pm. She will bring a new storybook for {}.'.format(tomorrow, name)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message,
        )
        new_loop.call_soon_threadsafe(e_game, 14, to_num, from_num, name, 2)

def e_game(stage, to_num='', from_num='', name='', time=0):
    if stage == 14:
        sleep(time)
        message = 'It’s bedtime! Tonton has a new lullaby for {}. Want her to call now? Text ‘YES’ or ’NO’.”'.format(name)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message,
        )
        return
    from_num = request.form['To']
    to_num = request.form['From']
    if stage == 15:
        answer = request.form['Body'].lower().strip()
        if answer == 'yes':
            # Initiate Call
            client.calls.create(
                to=to_num,
                from_=from_num,
                url="https://glacial-hollows-80092.herokuapp.com/soundsgame.xml" # TODO: Change this
            )

            return end()
        if answer == 'no':
            # Go to  End of Demo
            twilio_resp = MessagingResponse()

            return end()

def end():
    from_num = request.form['To']
    to_num = request.form['From']
    message1 = 'Thanks for trying this demo, powered by Vroom. To learn more about Vroom and our design process, visit http://bit.ly/link3. To learn more about Sesame Seeds, visit http://sesameworkshop.org/refugees.'
    message3 = 'You won’t receive any further messages from us. Text SESAME to restart.'

    client.messages.create(
        to=to_num,
        from_=from_num,
        body=message1,
    )
    sleep(1.5)
    twilio_resp = MessagingResponse()
    twilio_resp.message(message3)

    resp = make_response(str(twilio_resp))
    resp.set_cookie(Cookies.FIRST_TIME, '', expires=0)
    resp.set_cookie(Cookies.STAGE, '', expires=0)
    resp.set_cookie(Cookies.OPT_IN, '', expires=0)
    resp.set_cookie(Cookies.NAME, '', expires=0)
    resp.set_cookie(Cookies.GENDER, '', expires=0)
    resp.set_cookie(Cookies.BIRTHDAY, '', expires=0)
    return resp

    client.messages.create( # TODO: Fix this
        to=to_num,
        from_=from_num,
        body=message3,
    )
