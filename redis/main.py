import redis
import keyboard

client = redis.Redis(host='localhost', port=6379, db=0)

def on_key(event):
    if event.event_type == 'down':
        
        i = client.get('typing').decode('utf-8') + event.name
        client.set('typing', i)

        print( client.get('typing').decode('utf-8') )


keyboard.hook(on_key)

keyboard.wait('esc')

