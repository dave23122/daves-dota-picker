import requests
import json
import os

HEROES_DIR = "hero_data"
HEROES_JSON = "hero_data/heroes.json"

# Add your STRATZ API token to the file mentioned in "file_path" variable. Get a token from https://stratz.com/api
file_path = 'token.txt'
with open(file_path, 'r') as file:
    API_TOKEN = file.read()

# GraphQL endpoint
URL = "https://api.stratz.com/graphql"

# GraphQL query to get matchups
query = """
query Matchups($heroId: Short!) {
  heroStats {
    heroVsHeroMatchup(heroId: $heroId, matchLimit: 0) {
      advantage {
        heroId
        matchCountVs
        matchCountWith
        vs {
          heroId1
          heroId2
          matchCount
          winCount
        }
        with {
          heroId1
          heroId2
          matchCount
          winCount
        }
      }
    }
  }
}
"""

# Set headers including the authorization token
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    'User-Agent': 'STRATZ_API',
    "Content-Type": "application/json"
}

# Create individual hero data
print("Creating individual hero data...")
os.makedirs(f'{HEROES_DIR}/individual', exist_ok=True)
with open(HEROES_JSON, "r") as file:
  heroes = json.load(file)
  for i in heroes['heroes']:
    with open(f'{HEROES_DIR}/individual/{i["hero_id"]}.json', 'w') as f:
      # Set variables for the query
      variables = {
        "heroId": i['hero_id']
      }

      # Build the request payload
      payload = {
          "query": query,
          "variables": variables
      }

      # Send the POST request
      response = requests.post(URL, headers=headers, json=payload)
      data=response.json()
      
      json.dump(data, f)

  # Create win rate data
  print("Creating winrate data...")
  winRateFile = f"{HEROES_DIR}/winRateData.json"

  winRateList = []

  data = {}

  for y in heroes['heroes']:
    with open(f'{HEROES_DIR}/individual/{y["hero_id"]}.json', "r") as heroFile:
      heroData = json.load(heroFile)
      for i in heroes['heroes']:
        if y['hero_id'] != i['hero_id']:
          for x in heroData['data']['heroStats']['heroVsHeroMatchup']['advantage'][0]['vs']:
            if x['heroId2'] == i['hero_id']:
              winRateVs = (x['winCount'] / x['matchCount'] - 0.5)
          for z in heroData['data']['heroStats']['heroVsHeroMatchup']['advantage'][0]['with']:
            if z['heroId2'] == i['hero_id']:
              winRateWith = (z['winCount'] / z['matchCount'] - 0.5)
          item = {"hero": i['hero_id'], "winRateVs": winRateVs, "winRateWith": winRateWith}
          winRateList.append(item)
    data[y['hero_id']] = winRateList
    winRateList = []

  with open(winRateFile, "w") as f:
      json.dump(data, f, indent=4)


# ******************Create Role data******************
print("Creating role data...")
query = """
query HeroesMetaPositions {
  heroesAll: heroStats {
    stats(
      positionIds: [POSITION_1, POSITION_2, POSITION_3, POSITION_4, POSITION_5]
      groupByPosition: true
    ) {
      heroId
      matchCount
      position
    }
  }
}
"""

with open(f'{HEROES_DIR}/positionCounts.json', 'w') as f:
  # Build the request payload
  payload = {
      "query": query,
  }

  # Send the POST request
  response = requests.post(URL, headers=headers, json=payload)
  data=response.json()
  
  json.dump(data, f)

with open(HEROES_JSON, "r") as file:
  heroes = json.load(file)

with open(f'{HEROES_DIR}/positionCounts.json', 'r') as f:
  positionData = json.load(f)

singleHeroData = []
for y in heroes['heroes']:
  for i in positionData['data']['heroesAll']['stats']:
    if i['heroId'] == y['hero_id']:
      singleHeroData.append(i)
  sorted_data = sorted(singleHeroData, key=lambda x: x['matchCount'], reverse=True)
  y['roles'] = [sorted_data[0]['position'], sorted_data[1]['position']]
  with open(HEROES_JSON, 'w') as writeFile:
    json.dump(heroes, writeFile, indent=4)
  singleHeroData = []
