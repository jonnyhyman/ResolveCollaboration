from wgnlpy import WireGuard, PrivateKey

# ------------- INPUTS
UNAME = "Jonny"
PKEYS = "TkUgP5YntnMghc9fs+2+SYJ55AZc6Yotl6qOrCmPLVQ="
IP_ASSIGNED = "9.0.0.4"
S_IP = "127.0.0.1"

pk = PrivateKey.generate()
Pk = pk.public_key()

print("... KEYS:", pk, Pk)

conf = f"""
[Interface]
PrivateKey = {pk}
Address = {IP_ASSIGNED}/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {PKEYS}
AllowedIPs = 0.0.0.0/0
Endpoint = {S_IP}:51820
"""

print(conf)

with open(f"WireGuard_Configuration_{UNAME}.conf", "w") as conffile:
    conffile.write(conf)
