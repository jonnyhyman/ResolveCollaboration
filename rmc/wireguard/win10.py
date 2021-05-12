from ipaddress import ip_address, ip_network
from subprocess import Popen, PIPE
from auth import keys
from pathlib import Path
import subprocess
import os

class WireguardServer_Windows:
    """ Performs all setup for a Wireguard Windows 10 server. Must be run as Admin """

    def __init__(self, force_reset=False, config=None,
                        port=51820, subnet = "9.0.0.0/24"):

        if config is not None and force_reset==False:
            self.subnet = config['auth']['subnet']
            self.port = config['wireguard']['port']
            self.pk = config['wireguard']['pk']
            self.Pk = config['wireguard']['Pk']
            return

        self.subnet = subnet
        self.port = port

        # -------- Setup :

        Path("C:/Wireguard").mkdir(parents=True, exist_ok=True)
        Path("C:/Windows/System32/WindowsPowerShell/v1.0/Modules/wireguard/").mkdir(parents=True, exist_ok=True)

        # install function to give the wireguard tunnel internet access
        with open("C:/Windows/System32/WindowsPowerShell/v1.0/Modules/wireguard/wireguard.psm1", 'w') as psm1:
            psm1.write(enablesharing_powershell)

        # install VBS script to clean up WMI sharing instances
        with open("C:/Windows/System32/WindowsPowerShell/v1.0/Modules/wireguard/cleanwmi.vbs", 'w') as vbs:
            vbs.write(cleanwmi_vbs)

        print("... Wrote system scripts")

        # -------- Configure

        self.pk, self.Pk = self.pk_Pk_pair()

        print("... Generated new keys")

    def run_return(self, cmd):
        """ Run a command, capture output, don't crash"""
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return out # empty if successful
        except subprocess.CalledProcessError as e:
            return f"Command {cmd} returned error {e.returncode}"

    def update_config(self, userlist):
        ''' Overwrite the config with the current userlist'''

        first_ip = next(ip_network(self.subnet).hosts())

        # Interface always first
        server_config = (f"""
[Interface]
# Substitute with the subnet you chose for Wireguard earlier.
Address = {first_ip}/32
# Substitute with your *server's* private key
PrivateKey = {self.pk}
# If you chose a different port earlier when setting up port
# forwarding on your router, update the port here to match.
ListenPort = {self.port}
# This prevents IPv4 & IPv6 DNS leaks when browsing the web on the VPN
DNS = 1.1.1.1, 8.8.8.8, 2001:4860:4860::8888
        """)

        print(f">>> Added Server to config")

        # Peers

        for n, user in enumerate(userlist[1:]):

            # Authentication occured?
            if user['Pk'] != "":

                print(f">>> Added {user['name']}, {user['Pk']}, {user['ip']} to config")

                server_config += (f"""

# USER {n}: {user['name']}
[Peer]
# Substitute with *this peer*'s public key
PublicKey = {user['Pk']}
# Chose a unique IP within the Wireguard subnet you defined earlier
# that this particular peer will use when connected to the VPN.
AllowedIPs = {user['ip']}/32
                """)

        if self.state:
            self.down()
            do_up = True
        else:
            do_up = False

        with open("C:/Wireguard/Wireguard_rmcs.conf", 'w') as conf:
            conf.write(server_config)

        print("... Saved configuration")

        if do_up:
            self.up()

    @property
    def state(self):
        proc = Popen(['wg','show'], stdout=PIPE, stderr=PIPE)
        wg, err = proc.communicate()
        wg = str(wg,'utf-8')
        return wg != ""

    def up(self, debug=True):

        # already up?
        if self.state:
            # Don't go up if already up
            print('... Wireguard is already up')
            return
        else:

            cmd = '''"C:/Program Files/WireGuard/wireguard.exe" /installtunnelservice "C:/Wireguard/Wireguard_rmcs.conf"'''
            out = str(self.run_return(cmd))
            print(f"... Installed configuration", out=="b''")
            if debug: print(out)#; print(str(out,'utf-8'))

            # Set the network profile to be in Private category
            cmd = ('''powershell $NetworkProfile = Get-NetConnectionProfile -InterfaceAlias "Wireguard_rmcs"; '''
                    '''$NetworkProfile.NetworkCategory = 'Private'; '''
                    '''Set-NetConnectionProfile -InputObject $NetworkProfile''')

            out = str(self.run_return(cmd)) # empty if successful
            print(f"... Set profile to Private", out=="b''")
            if debug: print(out)#; print(str(out,'utf-8'))

            #Enable NAT
            cmd = '''powershell Set-NetConnectionSharing "Wireguard_rmcs" $true'''
            out = str(self.run_return(cmd)) # text DONE if successful
            print(f"... Enabled connection sharing", "DONE" in out)
            if debug: print(out)#; print(str(out,'utf-8'))

    def show(self):
        show = subprocess.check_output("wg show", shell=True, stderr=subprocess.STDOUT)
        show = str(show, 'utf-8', errors='ignore')
        print(show)

    def down(self, debug=True):
        if not self.state:
            print('... Wireguard is already down')
            return

        # Disable NAT
        cmd = '''powershell Set-NetConnectionSharing "Wireguard_rmcs" $false'''
        out = str(self.run_return(cmd)) # empty if successful
        print("... Disabled connection sharing", "DONE" in out)
        if debug: print(out)#; print(str(out,'utf-8'))

        # Uninstall tunnel service
        cmd = '''"C:/Program Files/WireGuard/wireguard.exe" /uninstalltunnelservice Wireguard_rmcs'''
        out = str(self.run_return(cmd))
        print("... Uninstalled configuration", out=="b''")
        if debug: print(out)#; print(str(out,'utf-8'))

    def pk_Pk_pair(self):
        pk = keys.PrivateKey.generate()
        Pk = pk.public_key()

        return pk, Pk

    def peers(self):
        """ Returns a dict containing all peers in the Server config.
                like: {Pk: {'ip':'...', 'handshake': True}}
        """

        proc = Popen(['wg','show'], stdout=PIPE, stderr=PIPE)
        wg, err = proc.communicate()
        wg = str(wg,'utf-8')

        peers = {}

        if "peer: " in wg:
            peers_conf = wg.split("peer: ")

            # [1:] because interface/server is 0
            for peer in peers_conf[1:]:

                Pk = peer.split('\n')[0].strip()
                handshake = False

                for row in peer.split('\n'):
                    if 'allowed ips' in row:
                        ip = row.strip().split(':')[1].strip()

                    if 'handshake' in row:
                        handshake = True

                peers[Pk] = {"ip": ip, 'handshake':handshake}

        return peers

cleanwmi_vbs = """'Clean up WMI Entries so we can make a new one
'https://github.com/billchaison/Windows-Trix
Wscript.Echo ">>> WMI Cleanup"

set WMI = GetObject("WinMgmts:/root/Microsoft/HomeNet")
set objs1 = WMI.ExecQuery("SELECT * FROM HNet_ConnectionProperties WHERE IsIcsPrivate = TRUE")
for each obj in objs1
   obj.IsIcsPrivate = FALSE
   obj.Put_
next
set objs2 = WMI.ExecQuery("SELECT * FROM HNet_ConnectionProperties WHERE IsIcsPublic = TRUE")
for each obj in objs2
   obj.IsIcsPublic = FALSE
   obj.Put_
next
"""

enablesharing_powershell = """Function Set-NetConnectionSharing
{
    Param
    (
        [Parameter(Mandatory=$true)]
        [string]
        $LocalConnection,

        [Parameter(Mandatory=$true)]
        [bool]
        $Enabled
    )

    Begin
    {
        $netShare = $null

        try
        {
            # Create a NetSharingManager object
            $netShare = New-Object -ComObject HNetCfg.HNetShare
        }
        catch
        {
            # Register the HNetCfg library (once)
            regsvr32 /s hnetcfg.dll

            # Create a NetSharingManager object
            $netShare = New-Object -ComObject HNetCfg.HNetShare
        }
    }

    Process
    {
		#Clear Existing Share
		$oldConnections = $netShare.EnumEveryConnection |? {
            $netShare.INetSharingConfigurationForINetConnection.Invoke($_).SharingEnabled -eq $true
        }

		foreach($oldShared in $oldConnections)
        {
            Write-Output "... Clearing old connection"
            $oldConfig = $netShare.INetSharingConfigurationForINetConnection.Invoke($oldShared)
            $oldConfig.DisableSharing()
        }

        # Clean up WMI
        # https://github.com/billchaison/Windows-Trix
        if ($Enabled)
        {
            & cscript /nologo "C:/Windows/System32/WindowsPowerShell/v1.0/Modules/wireguard/cleanwmi.vbs"
        }

        # Find connections
        $InternetConnection = Get-NetRoute | ? DestinationPrefix -eq '0.0.0.0/0' | Get-NetIPInterface | Where ConnectionState -eq 'Connected'
        $publicConnection = $netShare.EnumEveryConnection |? { $netShare.NetConnectionProps.Invoke($_).Name -eq $InternetConnection.InterfaceAlias }
        $privateConnection = $netShare.EnumEveryConnection |? { $netShare.NetConnectionProps.Invoke($_).Name -eq $LocalConnection }

        # Get sharing configuration
        $publicConfig = $netShare.INetSharingConfigurationForINetConnection.Invoke($publicConnection)
        $privateConfig = $netShare.INetSharingConfigurationForINetConnection.Invoke($privateConnection)

        if ($Enabled)
        {
            # Enable sharing (0 - public, 1 - private)
            $publicConfig.EnableSharing(0)
            $privateConfig.EnableSharing(1)
        }
        else
        {
            $publicConfig.DisableSharing()
            $privateConfig.DisableSharing()
            & cscript /nologo "C:/Windows/System32/WindowsPowerShell/v1.0/Modules/wireguard/cleanwmi.vbs"
        }

        Write-Output ">>> DONE"

        $publicConfig = $netShare.INetSharingConfigurationForINetConnection.Invoke($publicConnection)
        $privateConfig = $netShare.INetSharingConfigurationForINetConnection.Invoke($privateConnection)

        Write-Output $publicConfig
        Write-Output $privateConfig
    }
}
"""
