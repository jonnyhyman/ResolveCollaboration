# Resolve Collaboration
## Discoveries

### Database

Users are logged in by the `public."Sm2SysIdEntry"` table of the Project Server, and look like this:

```
   ('Sm2SysIdEntry_id', '6b90968e-cbb4-4000-afca-757bcffe31c6'),
   ('DbType', 'Sm2SysIdEntry'),
   ('SysId', 'f8b156a21693'),
   ('Name', 'Philharmonic'),
   ('LastSeen', 1617299214),
   ('FieldsBlob', <memory at 0x000001F677E2CC48>),
   ('ClientAddr', None),
   ('UserDefinedClientName', ''),
   ('UserDefinedClientIconId', 0),
   ('ClientMachineType', 0)]),
```

- When a user connects to the server, it changes the `ClientAddr` field to save the IP address of the connection.
    - Connected   : `('ClientAddr', '127.0.0.1')`
    - Disconnected: `('ClientAddr', None)`

- `ClientMachineType`
    - 0 for Windows
    - 4 for Mac


- `FieldsBlob`
    - If user not in a collab project : `FieldsBlob`, decoded from bytes reads `0 0 1 0 0 0 1 0 0 0 26 0 TcpListenPort 0 0 0 2 0 0 0 0 0`
    - If user is in a collab project : `FieldsBlob`, decoded from bytes reads `0 0 1 0 0 0 1 0 0 0 26 0 TcpListenPort 0 0 0 2 0 0 0 195 139`
    - This is not seemingly guaranteed though, I've had some computers stay at the "not in project" state and others have thesame FieldsBlob as another

In `public."SM_Project"` a project with collaboration users logged in has entries for `SysIds`:
- `SysIds`:`f8b156a21693,3C22FB9CB594,ACBC32B39E0D` these are the `SysId`s of the users on the project

# Messages

Collaboration messages occur peer-to-peer over TCP, on a number of ports:
- `50059` whoever connects to a project first gets this port
- Ports from `50059 to 63166` have been observed, all somewhat randomly. It's not clear that there's a pattern to the port grabbing

Collaboration messages capture the following data:
- Connections to Projects ```@`{ClientAddr}${SM_Project_id} {version}``` gets sent to other user(s); then they reply with something like `${SM_Project_id} {version}{SysId}`
- Live Chat Messages `@{SysId} {Message content} `
- Playhead position updates `@< {SysId} `

The largest known packet was ~160 bytes, but the true buffer size is still somewhat unknown
