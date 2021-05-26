import configparser
import json
import asyncio
import re
import operator
from datetime import date, datetime
import matplotlib.pyplot as plt

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)


def remove_emojis(data):
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    return re.sub(emoj, '', data)



def getMsgDetails(msg):
    details = {}
    #print(msg)
    data = remove_emojis(msg['message'])
    if operator.contains(data, "ETH"):
        details['date'] = msg['date'].date().strftime("%Y-%m-%d")
        #print(details['date'])
        str = data.split()
        #print(str)
        details['token'] = str[1].replace('#','')
        details['amount'] = int(str[2].strip("(").replace(',',''));
        details['from_acct'] = str[6].replace('#','')
        details['to_acct'] = str[8].replace('#','')
#x = txt.strip("\ud83d\udea8 ")
    #print(details)
    return details


def mergeData(dict):
    final_dict = {};
    for entry in dict:
        key = entry['token']+'_'+entry['date']
        val=1;
        if(entry['from_acct']=='unknown'):
            val=-1;
        if(key in final_dict.keys()):
            final_dict[key] = final_dict.get(key)+val*entry['amount'];
        else:
            final_dict[key] = val*entry['amount']; 
    #print(final_dict)      
    return final_dict  

# some functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

async def main(phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if await client.is_user_authorized() == False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    me = await client.get_me()

    user_input_channel = 'https://t.me/whale_alert_io'

    if user_input_channel.isdigit():
        entity = PeerChannel(int(user_input_channel))
    else:
        entity = user_input_channel

    my_channel = await client.get_entity(entity)

    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0

    while total_messages<400:
        print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
        history = await client(GetHistoryRequest(
            peer=my_channel,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            processed_msg = getMsgDetails(message.to_dict())
            if processed_msg:
                all_messages.append(processed_msg)
        offset_id = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break

    final_dict = mergeData(all_messages)
    lists = sorted(final_dict.items()) # sorted by key, return a list of tuples
    x, y = zip(*lists) # unpack a list of pairs into two tuples
    plt.plot(x, y)
    plt.show()
    #print(final_dict)
    # with open('/Users/sahilsingla/Desktop/channel_messages.json', 'w+') as outfile:
    #     json.dump(all_messages, outfile, cls=DateTimeEncoder)

with client:
    client.loop.run_until_complete(main(phone))