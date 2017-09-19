import json
import logging
from collections import Counter

import requests
from flask import Flask, jsonify, request

from excepts import ApiError

logger = logging.getLogger('home_work')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('logging.log')
logger.addHandler(fh)

RANDOM_WORD_URL = 'http://setgetgo.com/randomword/get.php'
WIKIPEDIA_URL = 'https://en.wikipedia.org/w/api.php'
DEFAULT_WIKIPEDIA_PARAMS = {'format': 'json',
                            'action': 'query',
                            'prop': 'extracts'}
RANDOM_JOKES_URL = 'http://api.icndb.com/jokes/random'
WORD_STATISTICS = Counter() # counter for word statistics


app = Flask(__name__)

@app.errorhandler(ApiError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/randomword/")
def random_word():
    '''
    Api for getting random word

    Optional query parameter:
    len: define the length of the word that you want to be returned,
    must be an int between 3 and 20.
    '''
    return jsonify(get_random_word(length=request.args.get('len')))

@app.route("/article/")
def article():
    '''
    Api for getting wiki article

    Optional query parameter:
    title: define the title of the article otherwise getting
    random word as a title
    '''
    params = {}
    title = request.args.get('title')
    # check there any title in request
    if not title:
        # getting random word from the API
        title = get_random_word()['word']
    # getting wiki article
    wiki_params = {'titles': title}.update(DEFAULT_WIKIPEDIA_PARAMS)
    response = requests.get(WIKIPEDIA_URL, params=wiki_params)
    # I wanted to use is_success method but it's not from vanilla Flask
    if not 200 <= response.status_code < 300:
        error_raising(request, response)
    return jsonify({'title': title, 'article': response.content})

@app.route("/commonwords/")
def common_words():
    '''
    Api for getting most popular words from randomword API
    Query parameter:
    n - amount of top popular words
    '''
    amount = request.args.get('n') or request.args.get('N')
    if str(amount).isdigit() and int(amount) > 0:
        most_common = [
            {'word': key, 'frequency': value}
            for key, value in WORD_STATISTICS.most_common(int(amount))
        ]
        return jsonify({'popular': most_common})
    else:
        raise ApiError('Non relevant n amount')

@app.route('/randomjoke/')
def random_joke():
    '''
    Api for getting random joke

    Optional query parameter:
    last_name: last name of the joke character or it will Norris
    first_name: first name of the joke character or it will Chuck
    '''
    params = {'firstName': request.args.get('first_name') or 'Chuck',
              'lastName': request.args.get('last_name') or 'Norris'}
    response = requests.get(RANDOM_JOKES_URL, params=params)
    # I wanted to use is_success method but it's not from vanilla Flask=
    if not 200 <= response.status_code < 300:
        error_raising(request, response)
    try:
        joke = json.loads(response.content)['value']['joke']
    except KeyError:
        error_raising(request, response, 'No joke in the API resoponse, sorry')

    return jsonify({'joke': joke})

def get_random_word(length=None):
    params = {}
    # check if length is digit and within limits
    if str(length).isdigit() and 3 < int(length) < 20:
        params['len'] = length
    # getting random word from the API
    response = requests.get(RANDOM_WORD_URL, params=params)
    # I wanted to use is_success method but it's not from vanilla Flask
    if not 200 <= response.status_code < 300:
        error_raising(request, response)
    WORD_STATISTICS[response.content] += 1
    return {'word': response.content}

def error_raising(request, response, message='Something went wrong on the API side'):
    logger.error(
        '%s, status %s, error message %s, request args %s, request url %s' %
        (message,
         response.status_code,
         response.content,
         request.args,
         request.url)
        )
    raise ApiError(message)

if __name__ == "__main__":
    app.run(debug=True)
