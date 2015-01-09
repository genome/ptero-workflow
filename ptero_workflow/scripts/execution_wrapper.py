import argparse
import json
import os
import requests
import subprocess
import sys

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--command-line', dest='command_line',
                        help='The command line to be executed')
    parser.add_argument('--inputs-url', dest='inputs_url',
                        help='The URL to GET inputs from')
    parser.add_argument('--outputs-url', dest='outputs_url',
                        help='The URL to PUT the outputs to')
    return parser.parse_args()

def get_from_url(url):
    r = requests.get(url)
    return r.content

def put_to_url(url, data):
    r = requests.put(url, json=data)
    return r.status_code

def main():
    args = parse_arguments()
    command = json.loads(args.command_line)
    input = None
    if args.inputs_url:
        input = get_from_url(args.inputs_url)
    p = subprocess.Popen( command, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = p.communicate(input)

    if put_to_url(args.outputs_url, json.loads(stdout_data)) != 200:
        sys.exit(os.EX_CANTCREAT)

    sys.exit( p.wait() )
