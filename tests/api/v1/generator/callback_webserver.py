#!/usr/bin/env python

from flask import Flask, request
import argparse
import requests
import signal
import simplejson
import sys


_REMAINING_CALLBACKS_EXPECTED = None
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-callbacks', type=int, default=1)
    parser.add_argument('--port', type=int, default=5113)
    parser.add_argument('--stop-after', type=int, default=10)

    arguments = parser.parse_args()

    global _REMAINING_CALLBACKS_EXPECTED
    _REMAINING_CALLBACKS_EXPECTED = arguments.expected_callbacks

    return arguments


app = Flask(__name__)


@app.route('/<path:callback_name>', methods=['PUT'])
def log_request(callback_name):
    try:
        print callback_name
        sys.stdout.flush()

        sys.stderr.write("URL: %s\n" % request.url)
        sys.stderr.write("  HEADERS:\n")
        for k, v in request.headers.items():
            sys.stderr.write("    %s: %s\n" % (k, v))
        sys.stderr.write("  DATA:\n    '%s'\n" % request.data)
        sys.stderr.write("  ARGS: %s\n" % request.args)
        sys.stderr.write("  JSON:\n    %s\n" % request.get_json())

        decrement_callback_count()
        send_request(request.args)

        return ''
    except:
        sys.stderr.write(traceback.format_exc())
        raise


def decrement_callback_count():
    global _REMAINING_CALLBACKS_EXPECTED
    _REMAINING_CALLBACKS_EXPECTED -= 1
    if _REMAINING_CALLBACKS_EXPECTED <= 0:
        shutdown_server()


def send_request(request_args):
    if 'response_name' in request_args:
        url = request.get_json().get('response_links').get(request_args['response_name'])
        data = dict(request_args)
        del data['response_name']

        request_data = {}
        for k, v in data.iteritems():
            request_data[k] = v[0]  # always take the first element
        response = requests.put(url, data=simplejson.dumps(request_data),
                headers={'Content-Type': 'application/json'})
        sys.stderr.write('  Callback response: %s\n' % response)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


if __name__ == '__main__':
    arguments = parse_arguments()
    signal.alarm(arguments.stop_after)
    app.run(port=arguments.port)
