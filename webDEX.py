from flask import Flask, render_template, request, redirect, jsonify
from mm2_calls import *
import random
import concurrent.futures

# this function retrieves the actual coin prices from the oracle (coinpaprika.com) synchronically (standard)
# for async price fetching you need some proxy ips as the coinpaprika api doesn't allow many parallel requests from one ip
def fetch_prices(urls, asynchronous):
    out = []
    CONNECTIONS = len(urls)
    TIMEOUT = 15

    def load_url(url, timeout):
        proxies = {
        }
        print(url)
        ans = requests.get(url, timeout=timeout, proxies=proxies)
        return ans

    if asynchronous:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONNECTIONS) as executor:
            future_to_url = (executor.submit(load_url, url, TIMEOUT) for url in urls)
            time1 = time.time()
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    data = future.result()
                except Exception as exc:
                    data = str(type(exc))
                finally:
                    try:
                        out.append(json.loads(data.text))
                    except AttributeError:
                        out.append(json.loads('{"error": "proxy timeout"}'))
                        print(str(json.loads('{"error": "proxy timeout"}')))
                    except Exception:
                        out.append(json.loads('{"error": "bad url"}'))

            time2 = time.time()

        print(f'Took {time2 - time1:.2f} s')
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
        return out

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
    time2 = time.time()
    print(f'Took {time2 - time1:.2f} s')
    return out

def html_frame(head, body):
    return """<!DOCTYPE html>
               <html>
               <head>
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
        base_amount = float(request.form.get('baseAmount')) - 0.00000001
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
              <meta http-equiv="refresh" content="2; URL=../my-open-orders" />"""
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

    while len(orderbook_json[0]) < 16:
        stop_mm2()
        time.sleep(5)
        start_mm2('mm2.log')
        time.sleep(8)
        activate_all()
        orderbook_json = get_orders_json()

    for i in range(len(orderbook_json)):
        try:
            j = i
            while orderbook_json[i]['pair'] == base_rel_ask[j-1] and float(orderbook_json[i]['price']) < ask_prices[j-1]:
                j -= 1
            base_rel_ask.insert(j, orderbook_json[i]['pair'])
            ask_prices.insert(j, float(orderbook_json[i]['price']))
            rez_ask_prices.insert(j, 1 / float(orderbook_json[i]['price']))
            ask_volume.insert(j, float(orderbook_json[i]['volume']))
            bid_volume.insert(j, int(float(orderbook_json[i]['volume']) * float(orderbook_json[i]['price']) * 100000000) / 100000000)
        except IndexError:
            base_rel_ask.append(orderbook_json[i]['pair'])
            ask_prices.append(float(orderbook_json[i]['price']))
            rez_ask_prices.append(1 / float(orderbook_json[i]['price']))
            ask_volume.append(float(orderbook_json[i]['volume']))
            bid_volume.append(int(float(orderbook_json[i]['volume']) * float(orderbook_json[i]['price']) * 100000000) / 100000000)

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

    data = fetch_prices(urls, False)

    # get kmd_price
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
    
    # appending oracle (coinpaprika) coin prices
    for i in range(len(base_ask)):
        for j in range(len(data)):
            try:
                if base_ask[i] == data[j]['symbol']:
                    base_usd_prices.append(float(data[j]['quotes']['USD']['price']))
                    break
            # SAI price is not availible at coinpaprika so getting its price from coingecko (base side)
            except KeyError:
                if base_ask[i] == "SAI":
                    data = requests.get("https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses=0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359&vs_currencies=usd", timeout=5).text
                    data = json.loads(data)
                    try:
                        sai_price = float(data['0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359']['usd'])
                    except KeyError:
                        sai_price = 1
                    base_usd_prices.append(sai_price)
                # some coin prices are chosen manually as a factor of KMD price (base side)
                try:
                    if base_ask[i] == "DEX":
                        base_usd_prices.append(17.5 * kmd_price)
                    elif base_ask[i] == "SUPERNET":
                        base_usd_prices.append(30 * kmd_price)
                    elif base_ask[i] == "CHIPS":
                        base_usd_prices.append(0.11 * kmd_price)
                    elif base_ask[i] == "REVS":
                        base_usd_prices.append(2 * kmd_price)
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
                # SAI price is not availible at coinpaprika so getting its price from coingecko (rel side)
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
                # some coin prices are chosen manually as a factor of KMD price (rel side)
                try:
                    if rel_ask[i] == "DEX":
                        rel_usd_prices.append(17.5 * kmd_price)
                    elif rel_ask[i] == "SUPERNET":
                        rel_usd_prices.append(30 * kmd_price)
                    elif rel_ask[i] == "CHIPS":
                        rel_usd_prices.append(0.11 * kmd_price)
                    elif rel_ask[i] == "REVS":
                        rel_usd_prices.append(2 * kmd_price)
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
