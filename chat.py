import asyncio
import json
import logging
import websockets
import color
import time

logging.basicConfig()

USERS = dict()

MESSAGES = []

def add_message(time, user, message):
    if len(MESSAGES) >= 50:
        MESSAGES.pop(0)
        MESSAGES.append((time, user, message))
    else:
        MESSAGES.append((time, user, message))

def users_event():
    list = [t for t in USERS.values() if t[0] != '']
    return json.dumps({"type": "users", "list": list})

async def notify_message(text, user):
    if USERS:
        if text:
            add_message(int(time.time()*1000), user, text)
            message = json.dumps({"type": "message", "time": int(time.time()*1000), "user": user, "text": text})
            await asyncio.wait([user.send(message) for user in USERS])

async def notify_system(text):
    if USERS:
        message = json.dumps({"type": "system", "time": int(time.time()*1000), "text": text})
        await asyncio.wait([user.send(message) for user in USERS])
        await notify_users()

async def notify_users():
    if USERS:
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def register(websocket):
    await asyncio.wait([websocket.send(json.dumps({"type": "msglist", "list": MESSAGES}))])
    USERS[websocket] = ["", ""]
    await notify_users()

async def unregister(websocket):
    if USERS[websocket][0] != "":
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
