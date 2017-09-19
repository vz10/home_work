from collections import Counter
import json

from flask import Flask, request
from flask import jsonify
import requests

from excepts import ApiError


RANDOM_WORD_URL = 'http://setgetgo.com/randomword/get.php'
WIKIPEDIA_URL = 'https://en.wikipedia.org/w/api.php'
DEFALUT_WIKIPEDIA_PARAMS = {'format': 'json',
                            'action': 'query',
                            'prop': 'extracts'}
RANDOM_JOKES_URL = 'http://api.icndb.com/jokes/random'
WORD_STATISTICS = Counter() # coutnter for word statistics


app = Flask(__name__)

@app.errorhandler(ApiError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/randoarticle/")
def reandom_word():
    '''
    Api for getting random word and wiki article for it

    Optional query parameter:
    len: define the length of the word that you want returned,
    must be an int between 3 and 20.
    '''
    params = {}
    length = request.args.get('len')
    # check if length is digign and within limits
    if str(length).isdigit() and 3 < int(length) < 20:
        params['len'] = length
    # getting random word from the API
    response = requests.get(RANDOM_WORD_URL, params=params)
    if response.status_code != 200:
        raise ApiError('Something went wrong on the API side', status_code=400)
    word = response.content
    # getting wiki article for the random word
    wiki_params = {'titles': word}.update(DEFALUT_WIKIPEDIA_PARAMS)
    response = requests.get(WIKIPEDIA_URL, params=wiki_params)
    if response.status_code != 200:
        raise ApiError('Something went wrong on the API side', status_code=400)
    # increase coutnter for the workd in statistics
    WORD_STATISTICS[word] += 1
    return jsonify({'word': word, 'article': response.content})

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
        raise ApiError('Non relevant n amount', status_code=400)

@app.route('/randomjoke/')
def random_joke():
    '''
    Api for getting random joke

    Optional query parameter:
    last_name: last name of the joke character or it will Noriss
    first_name: first name of the joke character or it will Chuck
    '''
    params = {'firstName': request.args.get('first_name') or '',
              'lastName': request.args.get('last_name') or ''}
    response = requests.get(RANDOM_JOKES_URL, params=params)

    if response.status_code != 200:
        raise ApiError('Something went wrong on the API side', status_code=400)
    try:
        joke = json.loads(response.content)['value']['joke']
    except KeyError:
        raise ApiError('No joke in the API resoponse, sorry', status_code=400)

    return jsonify({'joke': joke})


if __name__ == "__main__":
    app.run(debug=True)
