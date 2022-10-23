import json
import random
import requests
from bs4 import BeautifulSoup as bs
champ_audios = {}

rs = bs(requests.get(
    'https://leagueoflegends.fandom.com/wiki/Category:LoL_Champion_audio').text)


def check_audio_category(audio, category):
    siblings = list(audio.parent.parent.parent.parent.previous_siblings)
    for sibling in siblings:
        if sibling.name == 'h2' and category.lower() in sibling.text.lower():
            return True
    return False


def is_sentence(audio):
    try:
        is_sentence = '"' in list(list(
            list(audio.parent.parent.parent.next_siblings)[-1].children)[-1].children)[0]
        if is_sentence:
            return True
    except:
        return '"' in list(
            list(audio.parent.parent.next_siblings)[-1].children)[-1]


def filter_audios(audios, champion_name, action):
    filtered_audios = []
    if champion_name == 'Aurelion Sol':
        champion_name = 'AurelionSol'
    for a in audios:
        try:
            if not is_sentence(a):
                continue
            mwtitle = a.attrs['data-mwtitle']
            if len(mwtitle.split('.')) == 2:
                if (check_audio_category(a, action)):
                    if len(mwtitle.split('_')) == 2 and (mwtitle.split('_')[0].lower() == champion_name.lower() or mwtitle.split('_')[0].lower() == f'{champion_name.lower()}original'):
                        filtered_audios.append(a)
                        continue
                    if mwtitle.lower().startswith(f'{champion_name.lower()}original') or mwtitle.lower().startswith(f'{champion_name.lower()}_original'):
                        filtered_audios.append(a)
            else:
                if mwtitle.lower().startswith(f'{champion_name.lower()}') and check_audio_category(a, action):
                    filtered_audios.append(a)
        except Exception as e:
            pass
    return filtered_audios


for champion_element in rs.findAll('a', class_="category-page__member-link"):
    try:
        champion_name = champion_element.contents[0].split('/')[0]
        if champion_name == 'User:AnataBakka' or champion_name == 'Category:Champion audio':
            continue
        champion_audio_page_response = requests.get(
            f'https://leagueoflegends.fandom.com{champion_element.attrs["href"]}')
        audio_bs = bs(champion_audio_page_response.text)
        all_audio = audio_bs.findAll(name='audio')
        attack_audios = filter_audios(all_audio, champion_name, 'attack')
        random_attacks = random.sample(
            attack_audios, min(len(attack_audios), 5))
        random_attack_audios = list(
            map(lambda a: list(a.children)[0].attrs['src'], random_attacks))
        move_audios = filter_audios(all_audio, champion_name, 'move')
        random_moves = random.sample(move_audios, min(len(move_audios), 5))
        random_move_audios = list(
            map(lambda a: list(a.children)[0].attrs['src'], random_moves))
        if len(random_attack_audios) < 5:
            print(f'{champion_name} has less than 5 attack audios')
        if len(random_move_audios) < 5:
            print(f'{champion_name} has less than 5 move audios')
        champ_audios[champion_name] = {
            'move': random_move_audios, 'attack': random_attack_audios}
    except Exception as e:
        print(f'Error with {champion_name}, {e}')

with open('lol_voices.json', 'w') as f:
    f.write(json.dumps(champ_audios))
