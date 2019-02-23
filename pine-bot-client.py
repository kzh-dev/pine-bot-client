# coding=utf-8

import sys

## Python version check
version = sys.version_info
if version[0] != 3 or version[1] < 6:
    vstr = sys.version.split()[0]
    print(f"*** Use Python 3.6 or above: now={vstr} ***")
    sys.exit(1)

from logging import getLogger
logger = getLogger(__name__)

from util.parameters import load_parameters, load_param_file

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
            load_param_file(sys.argv[3])
        except Exception as e:
            raise CommandLineError(f"fail to load parameter file: {e}") from e

    return (command, pine_fname, pine_str, params)


## Run as a script
if __name__ == '__main__':
    from util.logging import notify, enable_logfile, enable_discord
    from command.init import do_init
    from command.run import do_run
    try:
        command, pine_fname, pine_str, params = handle_command_line()
    except CommandLineError as e:
        logger.error(e)
        logger.info('Type `python {} help` for usage'.format(sys.argv[0]))
        sys.exit(1)

    if command == 'help':
        do_help()

    try:
        if command == 'init':
            params = load_parameters(params)
            do_init(params, pine_fname, pine_str)
        elif command == 'run':
            params = load_parameters(params, pine_fname)
            logger.enable_logfile(pine_fname, params)
            logger.enable_discord(params)
            notify("=== %s ver.%s start ===", BOT_NAME, VERSION)
            do_run(params, pine_fname, pine_str)
    except Exception as e:
        logger.critical("fail to execute '%s: %s", command, e, exc_info=e)
        sys.exit(1)
