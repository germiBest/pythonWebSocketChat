import asyncio
import json
import logging
import websockets

logging.basicConfig()

USERS = dict()

def users_event():
    return json.dumps({"type": "users", "count": len(USERS)})

async def notify_message(text, nick):
    if USERS:
        if text:
            message = json.dumps({"type": "message", "nick": nick, "text": text})
            await asyncio.wait([user.send(message) for user in USERS])

async def notify_system(text):
    if USERS:
        message = json.dumps({"type": "system", "text": text})
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_users():
    if USERS:
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def register(websocket):
    USERS[websocket] = ""
    await notify_users()

async def unregister(websocket):
    del USERS[websocket]
    await notify_users()

async def counter(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["action"] == "message":
                if data["data"].find('/nick ', 0, (-1)*(len(data["data"]) - 6)) != -1:
                    newnick = data["data"][6:]
                    if newnick in USERS.values():
                        await asyncio.wait([websocket.send(json.dumps({"type": "system", "text": "Nickname is already occupied"}))])
                    elif len(newnick) > 32:
                        await asyncio.wait([websocket.send(json.dumps({"type": "system", "text": "Nicname is more than 32 characters"}))])
                    else:
                        if USERS[websocket] != "":
                            await notify_system(USERS[websocket] + " nickname is changed to " + newnick)
                        else:
                            await notify_system(newnick + " is connected")
                        USERS[websocket] = newnick
                else:
                    if(USERS[websocket] == ''):
                        await asyncio.wait([websocket.send(json.dumps({"type": "system", "text": "Your nickname is empty"}))])
                    else:
                        await notify_message(data["data"], USERS[websocket])

            else:
                logging.error("unsupported event: {}", data)
    finally:
        await unregister(websocket)


start_server = websockets.serve(counter, "139.180.184.160", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
