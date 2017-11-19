from datetime import datetime, timedelta
import re

from flask import Flask, request, make_response
from twilio.twiml.messaging_response import MessagingResponse

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
    body = request.form['Body'].lower()

    if body is 'pineapple':
        return opt_out()

    if first_time:
        return first_time_response()

    if stage == 1:
        return opt_in()

    return setup_account(stage)

def first_time_response():
    message = '''
    Welcome to  Sesame Seeds, powered by Vroom.

    This is a proof-of-concept demonstration to show the kinds of experiences families will share in Jordan, Lebanon, Iraq and Syria. We are not collecting any data and you can opt-out of messages at any time by texting ‘stop’.

    In this demo, you will play the part of a caregiver of a child under the age of 6. Respond OK when ready.
    '''
    twilio_resp = MessagingResponse()
    twilio_resp.message(message)

    resp = make_response(str(twilio_resp))
    resp.set_cookie(Cookies.FIRST_TIME, str(False))
    resp.set_cookie(Cookies.STAGE, str(1))

    return resp

def opt_in():
    user_response = request.form['Body'].lower()
    if user_response not in ['ok', 'yes']:
        return opt_out()

    message = 'اَلسَّلَامُ عَلَيْكُ! You have what it takes to nurture a young child’s brain. \
    Let’s get started. First, what’s your child’s name?'

    twilio_resp = MessagingResponse()
    twilio_resp.message(message)

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
