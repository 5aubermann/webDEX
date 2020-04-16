from flask import Flask, render_template, request, jsonify, redirect, url_for
from bs4 import BeautifulSoup
from mm2_calls import *
import concurrent.futures

price_prev = {'BET/KMD': None,
              'BOTS/KMD': None,
              'CHIPS/KMD': None,
              'COQUI/KMD': None,
              'CRYPTO/KMD': None,
              'DEX/KMD': None,
              'HODL/KMD': None,
              'LABS/KMD': None,
              'REVS/KMD': None,
              'RFOX/KMD': None}

# this function retrieves the actual coin prices from the oracle (coinpaprika.com) asynchronically (standard)
def fetch_prices(urls, asynchronous):
    out = []
    CONNECTIONS = 6
    TIMEOUT = 10

    def load_url(url, timeout):
        print(url)
        ans = requests.get(url, timeout=timeout)
        return ans
    
    dexstats = None
    if asynchronous:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
            future_to_url = (executor.submit(load_url, url, TIMEOUT) for url in urls)
           # time1 = time.time()
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    data = future.result()
                except Exception as exc:
                    data = str(type(exc))
                finally:
                    try:
                        if data.text[:7] == "<table>":
                            dexstats = data.text
                        else:
                            out.append(json.loads(data.text))
                    except AttributeError:
                        out.append(json.loads('{"error": "api timeout"}'))
                        print(str(json.loads('{"error": "api timeout"}')))
                    except Exception:
                        out.append(json.loads('{"error": "bad url"}'))

           # time2 = time.time()

       # print(f'Took {time2 - time1:.2f} s')
        for i in range(len(out) - 1, -1, -1):
            symbol = urls[i].split("/")[-1].split("-")[0].upper()
            for j in range(len(out) - 1, -1, -1):
                try:
                    if symbol == out[j]['symbol']:
                        urls.__delitem__(i)
                except KeyError:
                    out.__delitem__(j)

        for url in urls:
            out.append(json.loads('{"symbol": "' + url.split("/")[-1].split("-")[0].upper() + '"}'))
        return out, dexstats

    time1 = time.time()
    for url in urls:
        try:
            data = load_url(url, TIMEOUT).text
            if str(json.loads(data)) == "{'error': 'id not found'}":
                symbol = url.split("/")[-1].split("-")[0].upper()
                out.append(json.loads('{"symbol": "' + symbol + '"}'))
            else:
                out.append(json.loads(data))
        except Exception:
            symbol = url.split("/")[-1].split("-")[0].upper()
            out.append(json.loads('{"symbol": "' + symbol + '"}'))
   # time2 = time.time()
   # print(f'Took {time2 - time1:.2f} s')
    return out

def get_assetchain_prices(rows, pair1, pair2, price_prev):
    price = None
    volume = 0
    volume_price = 0
    for row in rows:
        cells = row.find_all('td')
        if cells[1].get_text() == pair1 or cells[1].get_text() == pair2:
            if cells[1].get_text() == pair1:
                volume += float(cells[2].get_text())
                volume_price += float(cells[2].get_text()) * float(cells[4].get_text())
            if cells[1].get_text() == pair2:
                volume += float(cells[3].get_text())
                volume_price += float(cells[3].get_text()) * (1 / float(cells[4].get_text()))
            try:
                price = volume_price / volume
                price_prev = price
            except ZeroDivisionError:
                price = price_prev
    return price, price_prev


def html_frame(head, body):
    return """<!DOCTYPE html>
               <html>
               <head>
               <link rel="shortcut icon" href="/static/icon.png">
               {}
               </head>
               <body>
               {}
               </body>
               </html>""" \
            .format(head, body)
            

app = Flask(__name__)

@app.route('/new-order', methods=['POST'])
def new_order():
    try:
        base = request.form.get('base').upper()
        rel = request.form.get('rel').upper()
        base_amount = request.form.get('baseAmount')
        rel_amount = request.form.get('relAmount')
        price = float(rel_amount) / float(base_amount)
        order = buy(base, rel, base_amount, "%.8f" % price)
        return jsonify(json.loads(order.text))
    except Exception as e:
        return str(e)

@app.route('/cancel-order')
def cancel_order():
    head = "<title>Cancel Order</title>"
    body = """<form action="/cancelled-order" method="post">
              <input type="text" id="uuid" name="uuid" placeholder="uuid">
              <input type="submit" value="Cancel Order">
              </form>"""
    return html_frame(head, body)

@app.route('/cancelled-order', methods=['POST'])
def cancelled_order():
    head = """<title>Cancelled Order</title>
              <meta http-equiv="refresh" content="4; URL=../my-open-orders" />"""
    body = cancel_uuid(request.form.get('uuid')).text
    return html_frame(head, body)

@app.route('/my-balances')
def my_balances():
    balances = "["
    for coin in coinslib.coins:
        try:
            if not json.loads(my_balance(coin).text)['balance'] == "0":
                balances += my_balance(coin).text + ","
        except KeyError:
            print(coin + " not available")
    balances = balances[:-1] + "]"
    return jsonify(json.loads(balances))

@app.route('/my-addresses')
def my_addresses():
    balances = "["
    for coin in coinslib.coins:
        balances += my_balance(coin).text + ","
    balances = balances[:-1] + "]"
    return jsonify(json.loads(balances))

@app.route('/cancel-all-orders')
def cancel_my_orders():
    orders = cancel_all()
    return jsonify(json.loads(orders.text))

@app.route('/my-recent-swaps')
def recent_swaps():
    swaps = my_recent_swaps()
    return jsonify(json.loads(swaps.text))

@app.route('/my-open-orders')
def open_orders():
    orders = my_orders()
    return jsonify(json.loads(orders.text))

@app.route('/webdex/withdraw')
def withdraw():
    head = "<title>Withdraw</title>"
    body = """<form action="/webdex/withdrawal" method="post">
              <input type="text" id="cointag" name="cointag" placeholder="Cointag">
              <input type="text" id="address" name="address" placeholder="Address">
              <input type="submit" value="Withdraw all">
              </form>"""
    return html_frame(head, body)

@app.route('/webdex/withdrawal', methods=['POST'])
def withdrawal():
    try:
        cointag = request.form.get('cointag').upper()
        address = request.form.get('address')
        tx_hex = withdraw_all(cointag, address).text
        try:
            send_raw_transaction(cointag, json.loads(tx_hex)['tx_hex'])
            return jsonify(json.loads(tx_hex))
        except KeyError:
            return jsonify(json.loads(tx_hex))
    except Exception as e:
        return str(e)

@app.route('/orderbook')
def index():
    get_orderbook()
    return render_template('index.html')

def get_orderbook():
    with open(os.path.dirname(os.path.abspath(__file__)) + "/coins") as j:
        coinsjson = json.load(j)

    orderbook_json = get_orders_json()
    base_rel_ask = []
    base_ask = []
    base_ask_name = []
    rel_ask = []
    rel_ask_name = []
    ask_prices = []
    base_usd_prices = []
    rel_usd_prices = []
    ratio_prices = []
    rez_ask_prices = []
    ask_volume = []
    bid_volume = []
    urls = []
    
    """
    while len(orderbook_json) < 16:
        stop_mm2()
        time.sleep(5)
        start_mm2('mm2.log')
        time.sleep(8)
        activate_all()
        orderbook_json = get_orders_json()
        """
    
    for i in range(len(orderbook_json)):
        try:
            j = i
            while orderbook_json[i]['pair'] == base_rel_ask[j-1] and float(orderbook_json[i]['price']) < ask_prices[j-1]:
                j -= 1
            base_rel_ask.insert(j, orderbook_json[i]['pair'])
            ask_prices.insert(j, float(orderbook_json[i]['price']))
            rez_ask_prices.insert(j, 1 / float(orderbook_json[i]['price']))
            ask_volume.insert(j, int(float(orderbook_json[i]['volume']) * 100000000) / 100000000)
            bid_volume.insert(j, float(orderbook_json[i]['volume']) * float(orderbook_json[i]['price']))
        except IndexError:
            base_rel_ask.append(orderbook_json[i]['pair'])
            ask_prices.append(float(orderbook_json[i]['price']))
            rez_ask_prices.append(1 / float(orderbook_json[i]['price']))
            ask_volume.append(int(float(orderbook_json[i]['volume']) * 100000000) / 100000000)
            bid_volume.append(float(orderbook_json[i]['volume']) * float(orderbook_json[i]['price']))

    for i in range(len(base_rel_ask)):
        if base_rel_ask[i].find("/"):
            for j, w in enumerate(base_rel_ask[i]):
                if w == "/":
                    base_ask.append(base_rel_ask[i][:j])
                    for k in range(len(coinsjson)):
                        if coinsjson[k]['coin'] == base_rel_ask[i][:j]:
                            base_ask_name.append(coinsjson[k]['fname'].replace(" ", "-")
                                                 .replace("Verus", "Verus-")
                                                 .replace("Raven", "Ravencoin")
                                                 .replace("Multi-collateral-", "")
                                                 .replace("Paxos", "Paxos-Standard-Token")
                                                 .replace("Chips", "Pangea")
                                                 .replace("ChainZilla", "Zilla"))
                    rel_ask.append(base_rel_ask[i][j + 1:])
                    for k in range(len(coinsjson)):
                        if coinsjson[k]['coin'] == base_rel_ask[i][j+1:]:
                            rel_ask_name.append(coinsjson[k]['fname'].replace(" ", "-")
                                                .replace("Verus", "Verus-")
                                                .replace("Raven", "Ravencoin")
                                                .replace("Multi-collateral-", "")
                                                .replace("Paxos", "Paxos-Standard-Token")
                                                .replace("Chips", "Pangea")
                                                .replace("ChainZilla", "Zilla"))

    for i in range(len(base_ask)):
        if "https://api.coinpaprika.com/v1/tickers/" + base_ask[i] + "-" + base_ask_name[i] not in urls:
            urls.append("https://api.coinpaprika.com/v1/tickers/" + base_ask[i] + "-" + base_ask_name[i])
        if "https://api.coinpaprika.com/v1/tickers/" + rel_ask[i] + "-" + rel_ask_name[i] not in urls:
            urls.append("https://api.coinpaprika.com/v1/tickers/" + rel_ask[i] + "-" + rel_ask_name[i])
    urls.append('https://dexstats.info/tradevolume.php')
    
    data, r = fetch_prices(urls, True)

    # assetchain_prices
    try:
        soup = BeautifulSoup(r, 'html.parser')
        rows = soup.find_all('tr')
        bet_price, price_prev['BET/KMD'] = get_assetchain_prices(rows, "BET/KMD", "KMD/BET", price_prev['BET/KMD'])
        bots_price, price_prev['BOTS/KMD'] = get_assetchain_prices(rows, "BOTS/KMD", "KMD/BOTS", price_prev['BOTS/KMD'])
        chips_price, price_prev['CHIPS/KMD'] = get_assetchain_prices(rows, "CHIPS/KMD", "KMD/CHIPS", price_prev['CHIPS/KMD'])
        coqui_price, price_prev['COQUI/KMD'] = get_assetchain_prices(rows, "COQUI/KMD", "KMD/COQUI", price_prev['COQUI/KMD'])
        crypto_price, price_prev['CRYPTO/KMD'] = get_assetchain_prices(rows, "CRYPTO/KMD", "KMD/CRYPTO", price_prev['CRYPTO/KMD'])
        dex_price, price_prev['DEX/KMD'] = get_assetchain_prices(rows, "DEX/KMD", "KMD/DEX", price_prev['DEX/KMD'])
        hodl_price, price_prev['HODL/KMD'] = get_assetchain_prices(rows, "HODL/KMD", "KMD/HODL", price_prev['HODL/KMD'])
        labs_price, price_prev['LABS/KMD'] = get_assetchain_prices(rows, "LABS/KMD", "KMD/LABS", price_prev['LABS/KMD'])
        revs_price, price_prev['REVS/KMD'] = get_assetchain_prices(rows, "REVS,KMD", "KMD/REVS", price_prev['REVS/KMD'])
        rfox_price, price_prev['RFOX/KMD'] = get_assetchain_prices(rows, "RFOX,KMD", "KMD/RFOX", price_prev['RFOX/KMD'])
    except TypeError:
        bet_price = None
        bots_price = None
        chips_price = None
        coqui_price = None
        crypto_price = None
        dex_price = None
        hodl_price = None
        labs_price = None
        revs_price = None
        rfox_price = None

    # kmd_price
    kmd_price = None
    for i in range(len(base_ask)):
        for j in range(len(data)):
            try:
                if base_ask[i] == data[j]['symbol']:
                    if base_ask[i] == "KMD":
                        kmd_price = float(data[j]['quotes']['USD']['price'])
                        break
            except KeyError:
                continue

    for i in range(len(base_ask)):
        for j in range(len(data)):
            try:
                if base_ask[i] == data[j]['symbol']:
                    base_usd_prices.append(float(data[j]['quotes']['USD']['price']))
                    break
            except KeyError:
                if base_ask[i] == "SAI":
                    data = requests.get("https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses=0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359&vs_currencies=usd", timeout=5).text
                    data = json.loads(data)
                    try:
                        sai_price = float(data['0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359']['usd'])
                    except KeyError:
                        sai_price = 1
                    base_usd_prices.append(sai_price)
                try:
                    if base_ask[i] == "DEX":
                        base_usd_prices.append(dex_price * kmd_price)
                    elif base_ask[i] == "SUPERNET":
                        base_usd_prices.append(30 * kmd_price)
                    elif base_ask[i] == "CHIPS":
                        base_usd_prices.append(chips_price * kmd_price)
                    elif base_ask[i] == "REVS":
                        base_usd_prices.append(revs_price * kmd_price)
                    elif base_ask[i] == "RFOX":
                        base_usd_prices.append(rfox_price * kmd_price)
                    elif base_ask[i] == "BOTS":
                        base_usd_prices.append(bots_price * kmd_price)
                    elif base_ask[i] == "BET":
                        base_usd_prices.append(bet_price * kmd_price)
                    elif base_ask[i] == "HODL":
                        base_usd_prices.append(hodl_price * kmd_price)
                    elif base_ask[i] == "LABS":
                        base_usd_prices.append(labs_price * kmd_price)
                    elif base_ask[i] == "COQUI":
                        base_usd_prices.append(coqui_price * kmd_price)
                    elif base_ask[i] == "CRYPTO":
                        base_usd_prices.append(crypto_price * kmd_price)
                    else:
                        base_usd_prices.append(None)
                except TypeError:
                    base_usd_prices.append(None)
                break

        for j in range(len(data)):
            try:
                if rel_ask[i] == data[j]['symbol']:
                    rel_usd_prices.append(float(data[j]['quotes']['USD']['price']))
                    break
            except KeyError:
                if rel_ask[i] == "SAI":
                    try:
                        rel_usd_prices.append(sai_price)
                    except NameError:
                        data = requests.get("https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses=0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359&vs_currencies=usd", timeout=5).text
                        data = json.loads(data)
                        try:
                            sai_price = float(data['0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359']['usd'])
                        except KeyError:
                            sai_price = 1
                        base_usd_prices.append(sai_price)
                try:
                    if rel_ask[i] == "DEX":
                        rel_usd_prices.append(dex_price * kmd_price)
                    elif rel_ask[i] == "SUPERNET":
                        rel_usd_prices.append(30 * kmd_price)
                    elif rel_ask[i] == "CHIPS":
                        rel_usd_prices.append(chips_price * kmd_price)
                    elif rel_ask[i] == "REVS":
                        rel_usd_prices.append(revs_price * kmd_price)
                    elif rel_ask[i] == "RFOX":
                        rel_usd_prices.append(rfox_price * kmd_price)
                    elif rel_ask[i] == "BOTS":
                        rel_usd_prices.append(bots_price * kmd_price)
                    elif rel_ask[i] == "BET":
                        rel_usd_prices.append(bet_price * kmd_price)
                    elif rel_ask[i] == "HODL":
                        rel_usd_prices.append(hodl_price * kmd_price)
                    elif rel_ask[i] == "LABS":
                        rel_usd_prices.append(labs_price * kmd_price)
                    elif rel_ask[i] == "COQUI":
                        rel_usd_prices.append(coqui_price * kmd_price)
                    elif rel_ask[i] == "CRYPTO":
                        rel_usd_prices.append(crypto_price * kmd_price)
                    else:
                        rel_usd_prices.append(None)
                except TypeError:
                    rel_usd_prices.append(None)
                break

    for i in range(len(base_usd_prices)):
        try:
            ratio_prices.append(base_usd_prices[i] / rel_usd_prices[i])
        except Exception:
            ratio_prices.append("")

    app.jinja_env.globals.update(get_orderbook=get_orderbook, base_rel_ask=base_rel_ask, base_ask=base_ask,
                                 base_ask_name=base_ask_name, rel_ask=rel_ask, rel_ask_name=rel_ask_name,
                                 ask_volume=ask_volume, bid_volume=bid_volume, ask_prices=ask_prices,
                                 rez_ask_prices=rez_ask_prices, base_usd_prices=base_usd_prices,
                                 rel_usd_prices=rel_usd_prices, ratio_prices=ratio_prices)
    return ""


app.run(port=5000, debug=False)
