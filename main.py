
import sys
from glob import glob
import base64
from time import sleep
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError
from pykakasi import kakasi
import unicodedata
import json

start_from = ''
# check_start_from = True
check_start_from = False
OVERWRITE_CURRENT = False

def convert_code(original_code: str) -> str:
    kks = kakasi()
    kks.setMode("H","a")
    kks.setMode("K","a")
    kks.setMode("J","a")
    kks.setMode("r","Passport")

    conv = kks.getConverter()
    result = conv.do(original_code)
    if (original_code != result):
        return result + '-ja'
    return original_code
query = gql("""
    mutation($code: String!, $image: String!) {
        createCustomEmoji(input: {
            emojiCode: $code
            imageDataUrl: $image
            clientMutationId: $code
        }) { clientMutationId }
    }
""")

getEmojiIdQuery = gql("""
    query test ($code: String!) { 
        customEmojiFromCode(code: $code) {
            id
        }
    }
""")

deleteEmojiQuery = gql("""
    mutation teste($id: ID!) {
    deleteCustomEmoji(input: { customEmojiId: $id}) {
        clientMutationId
    }
}
""")

def delete(client, emoji_code: str) -> bool:
    try:
        result = client.execute(getEmojiIdQuery, variable_values={"code": emoji_code})
    except TransportQueryError as e:
        pass
        print('notfound')
    else:
        sleep(0.1)
        id = result['customEmojiFromCode']['id']
        client.execute(deleteEmojiQuery, variable_values={"id": id})
        print('deleted')

                 

def upload(team_name: str, api_token : str, folder_name='emojis') -> bool:
    client = Client(
        transport=RequestsHTTPTransport(
            url=f"https://{team_name}.kibe.la/api/v1",
            use_json=True,
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f"Bearer {api_token}"
            }
        ))
    for file_name in glob(f"./{folder_name}/*"):
        code, ext = file_name.split('/')[-1].split('.')
        converted_code = convert_code(unicodedata.normalize('NFKC', code))

        if(check_start_from):
            if(converted_code == start_from):
                check_start_from = False
            continue
    
        with open(file_name, "rb") as image_file:
            data = base64.b64encode(image_file.read())
        
        if OVERWRITE_CURRENT:
            delete(client, converted_code)
            sleep(0.1)

        client.execute(query, variable_values={"code": converted_code, "image": f"data:image/{ext};base64,{data.decode('UTF-8')}" })
        print(f"Uploaded {converted_code}")
        sleep(0.1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Error - Missing arguments')
        print('Usage: python main.py  <team name> <api token> <foloder name(optional)>')
        exit()
    upload(sys.argv[1], sys.argv[2])
