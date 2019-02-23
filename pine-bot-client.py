# coding=utf-8

import sys
import os

## Python version check
PYTHON_VERSION = sys.version.split()[0]
version = sys.version_info
if version[0] != 3 or version[1] < 6:
    print(f"*** Use Python 3.6 or above: now={PYTHON_VERSION} ***")
    sys.exit(1)

## CCXT version check
try:
    import ccxt
except ImportError:
    print(f"*** CCXT is not found!! ***")
    sys.exit(1)
CCXT_VERSION = 'builtin'
if not os.path.exists('ccxt'):
    CCXT_VERSION = 'unknown'
    try:
        import pip
        ccxt = list(filter(lambda pkg: pkg.key == 'ccxt', pip.get_installed_distributions()))
        if ccxt:
            ccxt = ccxt[0]
            CCXT_VERSION = ccxt.version
            ver = [int(n) for n in ccxt.version.split('.')]
            if ver < [1, 17, 376]:
                print(f"Recommend CCXT 1.17.376 or above: now={CCXT_VERSION}")
    except:
        pass

## setup
from logging import getLogger
logger = getLogger(__name__)

from util.parameters import load_parameters, load_param_file

BOT_NAME = 'pine-bot'
VERSION = '0.0'

## do_help
def do_help ():
    s = '''\
[Usage] python pine-bot-client.py <command> [<argument>, ...]

 <command> := help|support|init|run

<support>
 support
   Display supported exchanges
 
 support <exchange>
   Display supported markets

 support <exchange> <market>
   Check given exchange/markt pair is supported

<init>
 init <pine script>
   Generate parameter json file unde the same directory of given pine script

<run>
 run <pine script>
   Run Pine script

 run <pine script> <additiona parameter json file>
   Run Pine script with additional parameters.
'''
    print(s)
    sys.exit(0)


## Handling command line arguments
class CommandLineError (Exception):
    pass

def handle_command_line ():
    argc = len(sys.argv)
    if argc < 2:
        raise CommandLineError("missing <command>. ('help' to show usge)")

    # command
    command = sys.argv[1]
    if command not in ('run', 'init', 'help', 'support'):
        raise CommandLineError("invalid command: {}".format(command))
    if command == 'help':
        return (command, None, None, None)
    if command == 'support':
        exchange = market = None
        if argc > 2:
            exchange = sys.argv[2]
        if argc > 3:
            market = sys.argv[3]
        return (command, exchange, market, None)

    # pine script
    if argc < 3:
        raise CommandLineError("missing <pine script>")
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
    from util.logging import enable_logfile
    from command.support import do_support
    from command.init import do_init
    from command.run import do_run
    try:
        command, *args = handle_command_line()
    except CommandLineError as e:
        logger.error(e)
        logger.info('Type `python {} help` for usage'.format(sys.argv[0]))
        sys.exit(1)

    if command == 'help':
        do_help()

    try:
        if command == 'support':
            params = load_parameters()
            do_support(params, args[0], args[1])
        else:
            pine_fname, pine_str, params = args
            if command == 'init':
                params = load_parameters(params)
                do_init(params, pine_fname, pine_str)
            elif command == 'run':
                params = load_parameters(params, pine_fname)
                enable_logfile(pine_fname, params)
                logger.info(logger, f"=== {BOT_NAME} ver.{VERSION} start ===")
                do_run(params, pine_fname, pine_str)
    except Exception as e:
        logger.critical("fail to execute '%s: %s", command, e, exc_info=e)
        sys.exit(1)
