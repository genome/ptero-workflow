#!/usr/bin/env python

import argparse
import json
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

def execute_command_line(command, input=None):
    p = subprocess.Popen( command, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate(input)

args = parse_arguments()
command = json.loads(args.command_line)
input = None
if args.inputs_url:
    input = get_from_url(args.inputs_url)
stdout_data, stderr_data = execute_command_line(command, input)
sys.stdout.write(stdout_data)
sys.stderr.write(stderr_data)
