import re
import os
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from time import sleep

from flask import Flask, request, make_response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

account_sid = os.environ.get('TWILIO_SID')
auth_token = os.environ.get('TWILIO_AUTH')

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

@app.route("/sms", methods=['GET', 'POST'])
def sms():
    first_time = request.cookies.get(Cookies.FIRST_TIME) != 'False'
    stage = int(request.cookies.get(Cookies.STAGE, 0))
    body = request.form['Body'].lower().strip()
    from_num = request.form['To']
    to_num = request.form['From']
    print('STAGE -------- ', stage)
    if stage == 13 or stage == 14:
        stage = 12

    if body == 'pineapple':
        return opt_out()

    if first_time:
        return first_time_response()

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
    message1 = 'Welcome to  Sesame Seeds, powered by Vroom.'
    message2 = 'This is a proof-of-concept demonstration to show the kinds of experiences families will share in Jordan, Lebanon, Iraq and Syria. We are not collecting any data and you can opt-out of messages at any time by texting ‘stop’.'
    message3 = 'In this demo, you will play the part of a caregiver of a child under the age of 6. Respond OK when ready.'
    from_num = request.form['To']
    to_num = request.form['From']

    client.messages.create(
        to=to_num,
        from_=from_num,
        body=message1,
    )
    sleep(1.5)

    twilio_resp = MessagingResponse()
    client.messages.create(
        to=to_num,
        from_=from_num,
        body=message2,
    )
    sleep(1.5)

    twilio_resp.message(message3)

    resp = make_response(str(twilio_resp))
    resp.set_cookie(Cookies.FIRST_TIME, str(False))
    resp.set_cookie(Cookies.STAGE, str(1))

    return resp

def opt_in():
    user_response = request.form['Body'].lower()
    if user_response not in ['ok', 'yes']:
        return opt_out()

    message1 = 'اَلسَّلَامُ عَلَيْكُ! You have what it takes to nurture a young child’s brain.'
    message2 = 'Let’s get started. First, what’s your child’s name?'

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
    resp.set_cookie(Cookies.STAGE, str(2))
    resp.set_cookie(Cookies.OPT_IN, str(True))

    return resp

def opt_out():
    twilio_resp = MessagingResponse()
    twilio_resp.message('No worries.')

    resp = make_response(str(twilio_resp))
    resp.set_cookie(Cookies.FIRST_TIME, str(True))
    resp.set_cookie(Cookies.STAGE, str(0))
    resp.set_cookie(Cookies.OPT_IN, str(False))

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
        pronoun = 'his' if gender is 'boy' else 'her'
        message = 'What’s {} birthday? Use dd/mm/yy'.format(pronoun)
        twilio_resp = MessagingResponse()
        twilio_resp.message(message)

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.GENDER, gender)
        resp.set_cookie(Cookies.STAGE, str(4))
        return resp

    if stage == 4: # Finish setup
        r = re.compile('^\d\d\/\d\d\/\d\d$')
        birthday = request.form['Body']
        name = request.cookies.get(Cookies.NAME)

        if not r.search(birthday):
            twilio_resp = MessagingResponse()
            twilio_resp.message('Please respond with a date formatted dd/mm/yy')
            return str(twilio_resp)

        message = check_birthday(birthday)
        message += '''
        Great! You will receive age-tailored activities for you and {} to do together. And we’ll teach you the science behind it all!”

        If you need help, text “help.” If you want to opt out, text ‘stop’ and we’ll unenroll you immediately.
        '''.format(name)
        twilio_resp = MessagingResponse()
        twilio_resp.message(message)

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.BIRTHDAY, str(birthday))
        resp.set_cookie(Cookies.STAGE, str(5))
        return resp

    return opt_out()

def check_birthday(birthday):
    birthday_date = datetime.strptime(birthday, '%d/%m/%y')

    if birthday_date.date() == datetime.today().date():
        return 'Happy Birthday!\n'
    return ''



def a_game(stage):
    name = request.cookies.get(Cookies.NAME)
    from_num = request.form['To']
    to_num = request.form['From']
    if stage == 5: # Intro game
        now = datetime.now().strftime('%A, %B %dth')
        message = 'It’s {}. Time for today’s game! Today, we’ll do Hide and Seek, which is great for children like {}. Text “OK” to get started.'.format(now, name)
        twilio_resp = MessagingResponse()
        twilio_resp.message(message)

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.STAGE, str(6))
        return resp
    if stage == 6: # Confirm start
        response = request.form['Body']
        if response.lower() != 'ok':
            message = 'No worries! Text back later when you\'re ready'
            twilio_resp = MessagingResponse()
            twilio_resp.message(message)

            resp = make_response(str(twilio_resp))
            resp.set_cookie(Cookies.STAGE, str(5))
            return resp

        name = request.cookies.get(Cookies.NAME)
        message1 = 'This one is simple, but teaches object permanence. Cover your face with a cloth and then…'
        message2 = 'Let us know when you finish the activity! Did {} like the activity? Text ‘yes’ or ‘no”'.format(name)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message1,
        )
        sleep(1.5)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body='https://s3.amazonaws.com/vroom-chicago-demo/hideandseek_lower.mp4',
            # media_url='https://s3.amazonaws.com/vroom-chicago-demo/hideandseek_lower.mp4',
        )
        sleep(1.5)
        twilio_resp = MessagingResponse()
        twilio_resp.message(message2)

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.STAGE, str(7))
        return resp
    if stage == 7 or stage == 8:
        response = request.form['Body']
        twilio_resp = MessagingResponse()
        if response.lower() == 'yes':
            twilio_resp.message('Great! We’ll send you more like this.')
        else:
            twilio_resp.message('Sorry to hear it! Maybe {} will like the next one better'.format(name))

        resp = make_response(str(twilio_resp))
        resp.set_cookie(Cookies.STAGE, str(9))
        new_loop.call_soon_threadsafe(b_game, stage, to_num, from_num, name, 30)
        return resp

def b_game(stage, to_num='', from_num='', name='', time=0):
    now = datetime.now().strftime('%A, %B %dth')
    if stage == 8:
        sleep(time)
        message = 'It’s {}th. Time for today’s game! Today, we’ll do 1-2-3 Jump, which is great for children like {}. Text “OK” to get started'.format(now, name)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message,
        )
        return
    name = request.cookies.get(Cookies.NAME)
    from_num = request.form['To']
    to_num = request.form['From']
    if stage == 9:
        message1 = 'This one is simple, but teaches executive function. Watch this video and give it a try!'
        message3 = 'Let us know when you finish the activity! Did {} like the activity? Text ‘yes’ or ‘no”'.format(name)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message1,
        )
        sleep(1.5)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body='https://s3.amazonaws.com/vroom-chicago-demo/123jump.mp4',
            # media_url='https://s3.amazonaws.com/vroom-chicago-demo/123jump.mp4',
        )
        sleep(1.5)
        twilio_resp = MessagingResponse()
        twilio_resp.message(message3)

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
        resp.set_cookie(Cookies.STAGE, str(12))
        new_loop.call_soon_threadsafe(c_game, 11, to_num, from_num, name, 30)
        return resp

def c_game(stage, to_num='', from_num='', name='', time=0):
    if stage == 11:
        sleep(time)
        message = 'You’re doing a great job—don’t forget to take care of yourself too! Slow breathing is a good way to relax. We can call you and guide you through it. Want to try it? Text “yes,” “no” or “later”'
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message,
        )
        return
    from_num = request.form['To']
    to_num = request.form['From']
    if stage == 12:
        answer = request.form['Body'].lower().strip()
        if answer == 'yes':
            # Initiate Call
            client.calls.create(
                to=to_num,
                from_=from_num,
                url="http://demo.twilio.com/docs/voice.xml" # TODO: Change this
            )

            twilio_resp = MessagingResponse()
            resp = make_response(str(twilio_resp))
            resp.set_cookie(Cookies.STAGE, str(14))
            new_loop.call_soon_threadsafe(d_game, stage, to_num, from_num, name, 30)
            return resp
        if answer == 'no':
            # Go to D
            twilio_resp = MessagingResponse()

            resp = make_response(str(twilio_resp))
            resp.set_cookie(Cookies.STAGE, str(14))
            new_loop.call_soon_threadsafe(d_game, stage, to_num, from_num, name, 30)
            return resp
        if answer == 'later':
            # wait 30 seconds and do this over again
            twilio_resp = MessagingResponse()

            resp = make_response(str(twilio_resp))
            resp.set_cookie(Cookies.STAGE, str(12))
            new_loop.call_soon_threadsafe(c_game, 11, to_num, from_num, name, 30)
            return resp

def d_game(stage, to_num='', from_num='', name='', time=0):
    sleep(time)
    message = 'Tonton’s friend will be coming to visit you tomorrow at 12:15! You can call this number if you need to reschedule: xxxxxx-xxx.'
    client.messages.create(
        to=to_num,
        from_=from_num,
        body=message,
    )
    new_loop.call_soon_threadsafe(e_game, 14, to_num, from_num, name, 30)

def e_game(stage, to_num='', from_num='', name='', time=0):
    if stage == 14:
        sleep(time)
        message = 'It’s bedtime! Tonton has a new lullaby for {}. Want her to call now? Text ‘yes’, ’no’, or later.”'.format(name)
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
                url="http://demo.twilio.com/docs/voice.xml" # TODO: Change this
            )

            twilio_resp = MessagingResponse()
            resp = make_response(str(twilio_resp))
            resp.set_cookie(Cookies.STAGE, str(0))
            new_loop.call_soon_threadsafe(end, stage, to_num, from_num, name, 30)
            return resp
        if answer == 'no':
            # Go to  End of Demo
            twilio_resp = MessagingResponse()

            resp = make_response(str(twilio_resp))
            resp.set_cookie(Cookies.STAGE, str(0))
            new_loop.call_soon_threadsafe(end, stage, to_num, from_num, name, 30)
            return resp
        if answer == 'later':
            # wait 30 seconds and do this over again
            twilio_resp = MessagingResponse()

            resp = make_response(str(twilio_resp))
            resp.set_cookie(Cookies.STAGE, str(115))
            new_loop.call_soon_threadsafe(e_game, 14, to_num, from_num, name, 30)
            return resp

def end(stage, to_num='', from_num='', name='', time=0):
        sleep(time)
        message1 = 'Thanks for trying this demonstration of Sesame Seeds, powered by Vroom. To learn more about this groundbreaking intervention, visit sesameworkshop.org/refugee.”'
        message2 = 'To learn more about Vroom, visit joinvroom.org. To get a look at our design process, check out [Parenting in Displacement]'
        message3 = 'You won’t receive any further messages from us.'

        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message1,
        )
        sleep(30)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message2,
        )
        sleep(30)
        client.messages.create(
            to=to_num,
            from_=from_num,
            body=message3,
        )
