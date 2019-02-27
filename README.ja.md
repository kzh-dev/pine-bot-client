# Pine Bot Client

## これは何？

[TradingView](http://tradingview.com/) でサポートされる Pine スクリプト言語でロジックを指定できる自動取引システムの**クライアント**です。

以下の特徴があります。
 * (現在のところ)仮想通貨取引に対応
 * クライアント・サーバシステムで動作
  * Pine スクリプトの処理はサーバ側で対応 (サーバ側はサービスとして提供されます)
  * クライアントは価格情報の取得と発注処理を担当(APIキー等はクライアント側でのみ使用され、サーバに送信されないため安全です)
  
### 対応取引所について
このシステムでは注文処理は ccxt、価格情報の取得は API 負荷軽減のために可能な限り cryptowatch を使用するようにしています。
そのため両システムに対応している、取引所・通貨ペアであれば原則的に取引は可能です。

しかし、これらのシステム間でのシンボル名の違い等は網羅的に対応したわけではありません(というかほとんどチェックしていない)のでうまく動作しない可能性はあります。。
フィードバックを歓迎します。

## Pine スクリプトの制限

独自の Pine 処理系を実装しているため、全ての Pine スクリプトが実行可能なわけではありません。以下のような制約があります。

 * 非対応な関数・変数
  * `security()` 
  * `strategy.order()`
  * 多くのビルトイン関数・変数(要望のあるものから対応していきます)
 * Pine 文法
  * 多重代入
 * 注文
  * 指値注文
  * stop/stop-limit 注文
  * ピラミッディング
 * `starategy.risk` パラメータ

## インストール
リリースされたアーカイブを展開するだけです。以下の依存性があります。
 * Python >= 3.6 (必須)
 * ccxt >= 1.17.376 (推奨)

## 使用方法

#### 1. インストールで展開したディレクトリ内に入ります
``` sh
$ cd pine-bot-client-xxxx
```

#### 2. グローバル設定ファイルを作成します。
``` sh
$ mv global-parameters.json.tmpl global-parameters.json
```
設定ファイルの中身は後述しますが、通常こちらに API キー等を設定することになるでしょう。

### 3. Pine スクリプトからスクリプトごとの設定ファイルを作成します。
``` sh
$ python pine-bot-client.py init <your Pine script>
```
これを実行すると、指定した Pine スクリプトファイルと同じ場所に、同名で拡張子に `.json` がついたファイルが作成されます。
このファイルでは通常、取引所やシンボル、足の長さ、と共に `input()` 関数で変更可能なパラメータを設定できます。

### 4. 実行します。
``` sh
$ python pine-bot-client.py run <your Pine script>
```
実行すると、端末及び `logs/` ディレクトリ以下に実行ログが出力されます。

### おまけ
上記では `init`, `run` コマンドがありましたが、他にもヘルプメッセージを表示する `help`、サポートする取引所情報を出力する `support` コマンドがあります。

ヘルプ情報の表示
``` sh
$ python pine-bot-client.py help
```

サポートする取引所一覧を表示
``` sh
$ python pine-bot-client.py support
```

シンボルのサポート情報を表示
``` sh
$ python pine-bot-client.py support <exchange>
```

`exchange` にはサポートされている取引所名を指定いてください。このコマンドでは取引所ごとに以下のような表示が行われます。

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
最初のカラムがシンボル名です。次の`[]`で囲まれたものはエイリアスでこれらも使用できます。

次の `True/False` のカラムは cryptowatch からの情報の取得が可能かを表しています。
単なる cryptowatch の対応状況以外に、シンボル名の読み替えがうまく行われているかも考慮されています。

最後のカラムは対応している時間足になります。ここが空になっているものは実行できません。

### 注意点など
 * 実行マシンの時計のズレはできるだけサーバ側の時計を使って補正しますが、できるだけ正確に合わせておくことをお勧めします。(ズレはログ中に `jitter=` として表示されます。
 
## 設定ファイル
このプログラムでは三種類の JSON フォーマットの設定ファイルを利用します。
 * 実行時のカレントディレクトリの `glogal-parameters.json`
 * 実行する Pine スクリプトと同じディレクトリの `<pine script name`>.json`
 * `run` コマンドの最後に指定した設定ファイル
それぞれのファイルに記述できる内容は全く同一で、実行前にこれらは一つにマージされます。

優先度は
```
 global-parameters.json < <pine script>.json < run コマンド時の json>
```
となります。

### 設定項目について

#### トップレベル項目
 * **exchange** (string) - 取引所名
 * **symbol** (string) - シンボル名
 * **resolution** (string,integer) - 足の長さ。`support` コマンドで表示される様な文字列 or 分単位の整数
 
#### inputs
このサブ項目の下に `input()` 関数で変更可能なパラメータを指定します。`type` で指定する型に従った形式で指定してください。

#### strategy
`strategy()` 関数で指定する内容を変更できます。恐らく最も重要なのは注文ロットを指定する `default_qty_value` でしょう。
 * **default_qty_value** (float) - 取引ロット **現在 default_qty_type は無視されるので各マーケットの取引単位での数字になります**

#### ccxt
ccxt ライブラリに指定するオプションを指定できます。詳細は ccxt のマニュアルを参照してください。重要なものは以下の二つです。
 * **apiKey** (string) - API キー
 * **secret** (string) - 秘密鍵
 
#### 取引所
bitmex などの取引所名のキーを指定して、上記 ccxt のオプションを取引所毎に設定することができます。`global-parameters.json` 内に全取引所の設定を一括で指定できるので便利です。

#### discord
Disocrd 通知についての設定項目になります。
 * **name** (string) - 通知名
 * **url** (string) - Discord 上で発行した通知用 URL
 * **avatar_url** (string) - Avatar アイコン画像の URL
