# webDEX

### Build upon pytomicDEX. Shout out to smk762.

### A Python Application for using [Komodo Platform](https://komodoplatform.com/)'s [atomicDEX](https://atomicdex.io/) in the browser.

![webDEX Orderbook](https://i.imgur.com/zY0brx8.png)

![webDEX Orderbook](https://i.imgur.com/qwIFx2r.png)

#### Requirements  
Python 3.6+

#### Dependencies
```
python3 -m pip install requests python-bitcoinlib flask
```

### Downloads
```
git clone https://github.com/5aubermann/webDEX
cd webDEX && wget https://raw.githubusercontent.com/jl777/coins/master/coins && wget https://github.com/KomodoPlatform/atomicDEX-API/releases/download/beta-2.0.1781/mm2-21b8a576f-Linux-Release.zip && unzip mm2-21b8a576f-Linux-Release.zip && rm mm2-21b8a576f-Linux-Release.zip
```

#### Recommended reading  
https://developers.atomicdex.io/  
https://developers.komodoplatform.com/  
https://komodoplatform.com/atomic-swaps/  


## Setup  

### MM2.json
This file needs to be edited with your own wallet passphrase (seed) and any rpc_password.

See MM2_example.json example.
```
{
"gui":"MM2GUI",
"netid":9999,
"rpc_password":"ENTER SECURE RPC PASSWORD",
"passphrase":"ENTER SECURE PASSPHRASE"
}
```

## Usage

#### Download and Run
run application by starting webDEX.py
```
python3 ~/webDEX/webDEX.py
```

... wait one minute until everything runs properly

start your browser
```
Orderbook:
http://localhost:5000/orderbook
```
- In the search bar seperate the coins you look for with space
- For example the search for - btc eth kmd - shows you all available order combinations of these coins between each other
- Press 'Enter' to show only cheap orders
- Click on a cointag highlights all coins with this tag in blue color
- Oracle price feed is from coinpaprika.com (prices for DEX, CHIPS, REVS and SUPERNET are chosen manually)
- Autorefresh every 5 minutes
```
Addresses:
http://localhost:5000/my-addresses
```
```
Balances:
http://localhost:5000/my-balances
```
```
Cancel all open orders:
http://localhost:5000/cancel-all-orders
```
```
Cancel order by uuid:
http://localhost:5000/cancel-order
```
```
Open orders:
http://localhost:5000/my-open-orders
```
```
Recent Swaps:
http://localhost:5000/my-recent-swaps
```
