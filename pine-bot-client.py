# coding=utf-8

import sys
import os

## Python version check
version = sys.version_info
if version[0] != 3:
    print("Use Python3!")
    sys.exit(1)

import requests
import json

BOT_NAME = 'pine-bot'
VERSION = '0.0'

## do_help
def do_help ():
    s = '''\
[Usage] python pine-bot-client.py <command> [<pine script>] [<parameter files>]

 <command> := help|init|run

 [init] Generate configuration file for the specifed pine script.
 [run]  Run the script. By default, it automatically reads a paramter file with same basename.
        You can specify different paramter file as optional command line argument.
'''
    print(s)
    sys.exit(0)


## Handling command line arguments
class CommandLineError (Exception):
    pass
def handle_command_line ():
    argc = len(sys.argv)
    if argc < 2:
        raise CommandLineError("Need <command>")

    # command
    command = sys.argv[1]
    if command not in ('run', 'init', 'help'):
        raise CommandLineError("invalid command: {}".format(command))
    if command == 'help':
        return (command, None, None, None)

    # pine script
    if argc < 3:
        raise CommandLineError("Need <command> and <pine script>")
    pine_fname = sys.argv[2]
    pine_str = ''
    try:
        with open(pine_fname) as f:
            pine_str = f.read()
    except Exception as e:
        raise CommandLineError("fail to read pine script: {}".format(e)) from e
    
    # explicit configuration
    params = None
    if argc > 3:
        try:
            with open(sys.argv[3]) as f:
                params = json.loads(f.read())
        except Exception as e:
            raise CommandLineError("fail to load configuration file: {}".format(e)) from e

    return (command, pine_fname, pine_str, params)


## Run as a script
if __name__ == '__main__':
    from util.logger import initialize_logger, critical
    from util.parameters import load_parameters
    from command.init import do_init
    from command.run import do_run
    try:
        command, pine_fname, pine_str, params = handle_command_line()
    except CommandLineError as e:
        print(e)
        print('Type `python {} help` for usage'.format(sys.argv[0]))
        sys.exit(1)

    if command == 'help':
        do_help()

    try:
        logger = initialize_logger(BOT_NAME)
        if command == 'init':
            params = load_parameters(params)
            do_init(params, pine_fname, pine_str)
        else:
            params = load_parameters(params, pine_fname)

            logger.enable_file(pine_fname)
            discord_url = params.get('DISCORD_URL', None)
            if discord_url:
                logger.enable_discord(discord_url)

            do_run(params, pine_fname, pine_str)
    except Exception as e:
        critical("fail to execute '{}: {}".format(command, e), exc_info=e)
        sys.exit(1)
