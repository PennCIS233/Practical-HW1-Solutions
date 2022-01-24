# Not the best code out there (lots of repetition), but should be clear enough for grading purposes
from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk.future.transaction import PaymentTxn, AssetConfigTxn, AssetTransferTxn, LogicSigTransaction
from algosdk import mnemonic, encoding
import json
import base64

account_A_address = "DDVX24NBBFJPMNBZGIVRPPF62EK454ZRS6EA6YAIT2RRLJSAHMNOGBIPY4"
account_A_mnemonic = "nature grunt jewel shadow super art frost turn bind want chimney novel plate scout basic enough doctor pudding supreme verify odor sign news absent void"
account_A_private_key = mnemonic.to_private_key(account_A_mnemonic)

account_B_address = "VISPGMRINHK3YAJM3XE2CLS5YKAEZSADJCMNZFYKVGZB2RZUTBC7NHSXNU"
account_B_mnemonic = "bacon frozen mistake treat file bleak another canvas ugly orient amount stove clown venue fall awake bag crew camera father frequent wool ankle absent admit"
account_B_private_key = mnemonic.to_private_key(account_B_mnemonic)


def print_created_asset(algodclient, account, assetid):
    account_info = algodclient.account_info(account)
    idx = 0;

    for my_account_info in account_info['created-assets']:
        scrutinized_asset = account_info['created-assets'][idx]
        idx = idx + 1

        if (scrutinized_asset['index'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['index']))
            print(json.dumps(my_account_info['params'], indent=4))
            break


def print_asset_holding(algodclient, account, assetid):
    account_info = algodclient.account_info(account)
    idx = 0

    for _ in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1

        if (scrutinized_asset['asset-id'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['asset-id']))
            print(json.dumps(scrutinized_asset, indent=4))
            break


def wait_for_confirmation(client, transaction_id, timeout):
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
            raise Exception('pool error: {}'.format(pending_txn["pool-error"]))

        client.status_after_block(current_round)
        current_round += 1

    raise Exception('pending tx not found in timeout rounds, timeout value = : {}'.format(timeout))


def get_client():
    return algod.AlgodClient(
        algod_token="",
        algod_address="https://testnet-algorand.api.purestake.io/ps2",
        headers={"X-API-Key": "1iMSUP8Kz94umVOCuQHxC3NnMEHgVjOH12cliIto"}
    )

def get_default_params(client):
    params = client.suggested_params()
    params.flat_fee = True
    params.fee = 1000
    return params


# Different from tutorial - modified to receive note from user
def first_transation_example(private_key, my_address, note=""):
    algod_client = get_client()

    account_info = algod_client.account_info(my_address)
    print("Account balance: {} microAlgos".format(account_info.get('amount')) + "\n")

    params = get_default_params(algod_client)

    receiver = "4O6BRAPVLX5ID23AZWV33TICD35TI6JWOHXVLPGO4VRJATO6MZZQRKC7RI"

    unsigned_txn = PaymentTxn(my_address, params, receiver, 1420000, None, note.encode())
    signed_txn = unsigned_txn.sign(private_key)

    txid = algod_client.send_transaction(signed_txn)
    print("Successfully sent transaction with txID: {}".format(txid))

    try:
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)
    except Exception as err:
        print(err)
        return

    print("Transaction information: {}".format(json.dumps(confirmed_txn, indent=4)))
    print("Decoded note: {}".format(base64.b64decode(confirmed_txn["txn"]["txn"]["note"]).decode()))



def create_asset(creator_address, creator_private_key):
    algod_client = get_client()
    params = get_default_params(algod_client)

    txn = AssetConfigTxn(
        sender=creator_address,
        sp=params,
        total=10,
        default_frozen=False,
        unit_name="XMR",
        asset_name="monero",
        manager=creator_address,
        reserve=creator_address,
        freeze=creator_address,
        clawback=creator_address,
        url="https://path/to/my/asset/details",
        decimals=0,
    )

    signed_txn = txn.sign(creator_private_key)
    txid = algod_client.send_transaction(signed_txn)
    print(txid)

    wait_for_confirmation(algod_client, txid, 5)

    pending_txn = algod_client.pending_transaction_info(txid)
    asset_id = pending_txn["asset-index"]
    print_created_asset(algod_client, creator_address, asset_id)
    print_asset_holding(algod_client, creator_address, asset_id)

    return asset_id


def opt_in_to_asset(asset_id, address, private_key):
    algod_client = get_client()
    params = get_default_params(algod_client)

    account_info = algod_client.account_info(address)
    idx = 0
    for _ in account_info["assets"]:
        scrutinized_asset = account_info["assets"][idx]
        idx = idx + 1
        if scrutinized_asset["asset-id"] == asset_id:
            return

    txn = AssetTransferTxn(
        sender=address,
        sp=params,
        receiver=address,
        amt=0,
        index=asset_id,
    )
    signed_txn = txn.sign(private_key)
    txid = algod_client.send_transaction(signed_txn)

    wait_for_confirmation(algod_client, txid, 5)
    print("\n\nAccount {} opted in to {}".format(address, asset_id))
    print_asset_holding(algod_client, address, asset_id)


def send_asset(asset_id, sender_address, sender_private_key, receiver_address):
    algod_client = get_client()
    params = get_default_params(algod_client)

    txn = AssetTransferTxn(
        sender=sender_address,
        sp=params,
        receiver=receiver_address,
        amt=1,
        index=asset_id,
    )

    signed_txn = txn.sign(sender_private_key)
    txid = algod_client.send_transaction(signed_txn)
    print(txid)

    wait_for_confirmation(algod_client, txid, 5)
    print_asset_holding(algod_client, receiver_address, asset_id)


def transfer_atomically(asset_id, asset_sender_address, asset_sender_private_key, asset_receiver_address, asset_receiver_private_key, value=4120000, step5=False):
    algod_client = get_client()
    params = get_default_params(algod_client)

    payment_for_asset_txn = PaymentTxn(asset_receiver_address, params, asset_sender_address, value)
    asset_transfer_txn = AssetTransferTxn(
        sender=asset_sender_address,
        sp=params,
        receiver=asset_receiver_address,
        amt=1,
        index=asset_id,
    )

    group_id = transaction.calculate_group_id([payment_for_asset_txn, asset_transfer_txn])
    payment_for_asset_txn.group = group_id
    asset_transfer_txn.group = group_id

    payment_for_asset_txn_signed = payment_for_asset_txn.sign(asset_receiver_private_key)
    asset_transfer_txn_signed = None

    if step5:
        with open("step5.lsig", "rb") as f:
            lsig = encoding.future_msgpack_decode(base64.b64encode(f.read()))
        asset_transfer_txn_signed = LogicSigTransaction(asset_transfer_txn, lsig)
    else:
        asset_transfer_txn_signed = asset_transfer_txn.sign(asset_sender_private_key)

    signed_group = [payment_for_asset_txn_signed, asset_transfer_txn_signed]

    txid = algod_client.send_transactions(signed_group)
    print(group_id)
    print(txid)

    wait_for_confirmation(algod_client, txid, 5)
    print_asset_holding(algod_client, asset_receiver_address, asset_id)


def step2():
    first_transation_example(account_A_private_key, account_A_address, "my first Algorand transaction")
    first_transation_example(account_B_private_key, account_B_address, "my second Algorand transaction")


def step3():
    try:
        asset_id = create_asset(account_A_address, account_A_private_key)
        opt_in_to_asset(asset_id, account_B_address, account_B_private_key)
        send_asset(asset_id, account_A_address, account_A_private_key, account_B_address)
    except Exception as err:
        print(err)
        return


def step4():
    # from step3
    asset_id = 66582200
    try:
        transfer_atomically(
            asset_id,
            account_A_address,
            account_A_private_key,
            account_B_address,
            account_B_private_key,
        )
    except Exception as err:
        print(err)
        return


def step5():
    try:
        opt_in_to_asset(14035004, account_A_address, account_A_private_key)
        transfer_atomically(
            14035004,
            "4O6BRAPVLX5ID23AZWV33TICD35TI6JWOHXVLPGO4VRJATO6MZZQRKC7RI",
            "",
            account_A_address,
            account_A_private_key,
            int(4.2 * 10**6),
            True,
        )
    except Exception as err:
        print(err)
        return


# step2()
# step3()
# step4()
# step5()
