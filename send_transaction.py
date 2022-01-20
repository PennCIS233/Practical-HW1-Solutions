from algosdk.v2client import algod
import algosdk

# connect to algo client
algod_client = algod.AlgodClient(
    algod_token="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    algod_address="http://localhost:4001",
)

# setup account variables
my_address = "LJVQEK7SPGL6FKHHFQ4DC6D4DE5NLCN4UJDZ4THKHDKODL6AU2AMY7SNMI"
mneumonic = "crystal cart accuse novel hammer visit history olive crop access process lemon decline dune rabbit cattle friend mix enroll rug crime grunt betray abandon devote"
private_key = algosdk.mnemonic.to_private_key(mneumonic)
account_info = algod_client.account_info(my_address)
print("Account balance: {} microAlgos".format(account_info.get('amount')) + "\n")

# build transaction
from algosdk.future.transaction import PaymentTxn
params = algod_client.suggested_params()
receiver = "DPKE4VCXDRHAUB4ZCIYHQ42NSKHBVFIUVPRNJIQ7F5KV4LA74HZCZ6XKAQ"
note = "Hello World".encode()
unsigned_txn = PaymentTxn(my_address, params, receiver, 1000000, None, note)

# sign transaction
signed_txn = unsigned_txn.sign(private_key)

import json
import base64

#submit transaction
txid = algod_client.send_transaction(signed_txn)
print("Successfully sent transaction with txID: {}".format(txid))

# utility function for waiting on a transaction confirmation
def wait_for_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    Args:
        transaction_id (str): the transaction to wait for
        timeout (int): maximum number of rounds to wait    
    Returns:
        dict: pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return 
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:  
            raise Exception(
                'pool error: {}'.format(pending_txn["pool-error"]))
        client.status_after_block(current_round)                   
        current_round += 1
    raise Exception(
        'pending tx not found in timeout rounds, timeout value = : {}'.format(timeout))

# wait for confirmation 
try:
    confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
except Exception as err:
    print(err)
    exit()

print("Transaction information: {}".format(
    json.dumps(confirmed_txn, indent=4)))
print("Decoded note: {}".format(base64.b64decode(
    confirmed_txn["txn"]["txn"]["note"]).decode()))
