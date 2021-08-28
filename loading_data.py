import requests
import json
import datetime
from time import sleep
from collections import defaultdict

usernames = set()
user_ratings = defaultdict(dict)

offset = 61000
size = 10000

with open('data/june_2019_users.txt') as fin:
  line = 0
  for player in fin:
    line += 1
    if line < offset:
      continue
    usernames.add(player.strip())
    if line == offset + size:
      break

for index, user in enumerate(usernames):
  resp = requests.get(f'https://lichess.org/api/user/{user}/rating-history')
  sleep(0.5)
  if resp.status_code != 200: continue

  for game_type in resp.json():
    user_ratings[user][game_type['name']] = \
      [{'date': str(datetime.date(point[0], point[1]+1, point[2])),
        'rating': point[3]} for point in game_type['points']]
  if index % 10 == 0:
    print(f'Analyzed user {index + 1} of {len(usernames)}...\nRoughly {int(0.9*(len(usernames)-index))} seconds remaining.')

with open(f'data/rating_histories/ratings_{offset}_to_{offset+size-1}.json', 'w') as fout:
  json.dump(user_ratings, fout)

