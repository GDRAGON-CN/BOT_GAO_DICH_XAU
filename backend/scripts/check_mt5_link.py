import sys
try:
    import MetaTrader5 as mt5
    print("MetaTrader5 python package is installed.")
    if mt5.initialize():
        term = mt5.terminal_info()
        acc = mt5.account_info()
        print(f"MT5 Connected! Terminal build: {term.build if term else 'N/A'}")
        if acc:
            print(f"Account: {acc.login} | Server: {acc.server} | Balance: {acc.balance} {acc.currency}")
        mt5.shutdown()
    else:
        print(f"MT5 Initialize failed. Error: {mt5.last_error()}")
except ImportError:
    print("MetaTrader5 package is not installed on this Python environment.")
