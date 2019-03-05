# Pine Bot Client

[日本語](https://github.com/kzh-dev/pine-bot-client/blob/master/README.ja.md)

## What's this?

This is a **client** implementation of trading program(bot) which can use Pine script langauge used in [TradingView](http://tradingview.com/) to define a strategy.

 * (Currently) Only support crypto trading using ccxt and cryptowatch API.
 * Work with server module (which is not public)
  * Pine script is processed on server-side.
  * Client module collects price information (OHLCV) adn make an order. (API key and secret information won't be sent to server.)
  
### Exchange/Market support
This program uses ccxt to make an order and use cryptowatch API to acquire price information to reduce the number API calls of exchange.  It means you can trade any pairs at any exchanges which are supported by both modules theortically.

However the above two system often diffrent symbol name for identical market, so we need to translate it (by implementing).
Your feedback and request are appreciated.

## Restrictions in Pine language

(In server-side,) an original Pine runtime is implemented and used.  So far it has supported subset of Pine language and here are notable restrictions.

 * Version 3 is supported
 * Not implemented builtin functions
   * `security()` 
   * `strategy.order()`
   * Many others...(Your request is appreciated)
 * Syntax
   * Multiple assignment statement
 * Order
   * Limit order
   * Stop/Stop-limit order
   * Pyramiding
 * `starategy.risk` builtin variables

## Installation
Just extract released tarball/zip file.

Here are prerequistics:
 * Python >= 3.6 (Mandaotry)
 * ccxt >= 1.17.376 (Recommendation)

## How to use

#### 1. Move to the directory made by tarball extractio.
``` sh
$ cd pine-bot-client-xxxx
```

#### 2. Prepare global parameter file from template.
``` sh
$ mv global-parameters.json.tmpl global-parameters.json
```
Supported parameters are explained in different section.  You set API key in this file usually.

### 3. Generate Pine local paramter file.
``` sh
$ python pine-bot-client.py init <your Pine script>
```
If finished successfully, it generates `<Pine script>.json` file.  You usually set exchange, market, time resolution and order lot with the parameters you defined by `input()` function in the Pine script.

### 4. Run
``` sh
$ python pine-bot-client.py run <your Pine script>
```
It outputs log files under `log/` directory with console output.

### Other commands
In the above section, `init` and `run` commands are introduced.  There are other commands, `help` to show usage and `support` command to output exchange/market support information.

Show usage
``` sh
$ python pine-bot-client.py help
```

Show list of supported exchange
``` sh
$ python pine-bot-client.py support
```

Supported symbols in an exchange.
``` sh
$ python pine-bot-client.py support <exchange>
```
You can specify an identifier of supported exchange.

This is a simple output.
``` sh
$ python pine-bot-client.py support bitflyer
BTC/JPY: ['BTC/JPY', 'BTCJPY', 'BTC_JPY']: True: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w']
FX_BTC_JPY: ['FX_BTC_JPY', 'FXBTCJPY']: True: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w']
ETH/BTC: ['ETH/BTC', 'ETHBTC', 'ETH_BTC']: True: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w']
BCH/BTC: ['BCH/BTC', 'BCHBTC', 'BCH_BTC']: True: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w']
BTCJPY29MAR2019: ['BTCJPY29MAR2019']: False: []
BTCJPY01MAR2019: ['BTCJPY01MAR2019']: False: []
BTCJPY08MAR2019: ['BTCJPY08MAR2019']: False: []
BTC/USD: ['BTC/USD', 'BTCUSD', 'BTC_USD']: True: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w']
BTC/EUR: ['BTC/EUR', 'BTCEUR', 'BTC_EUR']: True: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w']
```
The first column is symbol name. You can also use aliases show in next column surronded by `[]`.

Next column including `True/False` show whether price infomration is availabe with cryptowatch API (with successful tranlation of symbol names).

Last column is supported time resolution.  If it's empty, the symbole is not available.

### Notes
The clock of the box where this bot client is running should be accurate enough even if this program calibrates internally using server-side clock. (The observed delay is shown in log information as `jitter=`.
 
## Configuration files
This bot uses three kinds of JSON-format configuration files.
 * `glogal-parameters.json` under current working directory.
 * `<pine script name`>.json` next to Pine script file to run.
 * Additonal file specified as last optional argument of `run` command.
You can write all configuration itmes in any of these files because they are merged into single object before running.

In merging, it follows following priority order.
```
 global-parameters.json < <pine script>.json < run command json
```

### Configuration Items

#### Top-level items
 * **exchange** (string) - Exchange id.
 * **symbol** (string) - Market symbol.
 * **resolution** (string,integer) - Time resolution. Something like shown as `support` command or integer value in minute.
 
#### inputs
Under this item, you can specify paramters defined by `input()` function.  You need to follow `type` defined in `input()` function.

#### strategy
Under this item, you can change paramters defined in `strategy()` function.  Most relavant one should be `default_qty_value`.
 * **default_qty_value** (float) - Order lot **Currently `default_qty_type` is ignored and this value is directly used as order size in each market.**

#### ccxt
You can specify options to give to `ccxt` library.  Please refer to ccxt document for details.  Here are most relavant options.
 * **apiKey** (string) - API key
 * **secret** (string) - API secret
 
#### <exchange id>
You can use different `ccxt` parameters for different exchanges.  It's useful to write API key/secret informations for all exchanges in `global-parameters.json`.

#### discord
Items for push notification using Discord
 * **name** (string) - Notification name
 * **url** (string) - URL for notification issued by Discord
 * **avatar_url** (string) - URL for avatar image

