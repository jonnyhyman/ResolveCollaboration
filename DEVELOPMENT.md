# Development todo list:
_(many things here may be in code TODOs or not)_


---

Common:
- Time-based salt in the encryption of packets
    
Client:
- Configuration reset option on client

Server:
- Admin features in an executable without `sudo .app`
    - sudo commands should be offloaded to individual subprocess runs, rather than one big sudo call on the .py

- Give admin the option of __Route all traffic__ (`AllowedIPs = 0.0.0.0/0, ::/0`) or __Resolve traffic only__ (`AllowedIPs = {wireguard subnet}`)
