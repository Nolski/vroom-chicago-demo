from flask import Flask, request, make_response
from datetime import datetime, timedelta
from twilio.twiml.messaging_response import MessagingResponse

 
app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def sms():
    print(request.form['Body'])

    message_count = int(request.cookies.get('message_count', 0))
    message_count += 1

    tresp = MessagingResponse()
    tresp.message("Hello world! {}".format(message_count))

    resp = make_response(str(tresp))
    resp.set_cookie('message_count', str(message_count))

    return resp
