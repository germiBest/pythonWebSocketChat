import asyncio
import json
import logging
import websockets
import color

logging.basicConfig()

USERS = dict()

def users_event():
    list = [t for t in USERS.values() if t[0] != '']
    return json.dumps({"type": "users", "list": list})

async def notify_message(text, nick):
    if USERS:
        if text:
            message = json.dumps({"type": "message", "nick": nick, "text": text})
            await asyncio.wait([user.send(message) for user in USERS])

async def notify_system(text):
    if USERS:
        message = json.dumps({"type": "system", "text": text})
        await asyncio.wait([user.send(message) for user in USERS])
        await notify_users()

async def notify_users():
    if USERS:
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def register(websocket):
    USERS[websocket] = ["", ""]
    await notify_users()

async def unregister(websocket):
    await notify_system(USERS[websocket][0] + " is disconnected")
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
                        if USERS[websocket][0] != "":
                            old = USERS[websocket][0]
                            USERS[websocket][0] = newnick
                            await notify_system(old + " nickname is changed to " + USERS[websocket][0])
                        else:
                            USERS[websocket][0] = newnick
                            USERS[websocket][1] = color.random_color()
                            await notify_system(newnick + " is connected")
                elif data["data"].find('/color ', 0, (-1)*(len(data["data"]) - 7)) != -1:
                    coloruser = data["data"][7:]
                    if color.check_color(coloruser):
                        USERS[websocket][1] = coloruser
                    else:
                        await asyncio.wait([websocket.send(json.dumps({"type": "system", "text": "Your color is invalid, formate is /color FFFFFF"}))])
                else:
                    if(USERS[websocket][0] == ''):
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
