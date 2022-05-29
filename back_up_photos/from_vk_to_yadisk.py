import json
import api
import requests
from datetime import datetime
import os

BASE_PATH = os.getcwd()
LOGS_DIR_NAME = 'logs'
LOGS_FILE_NAME = 'log.txt'

file_path = os.path.join(BASE_PATH, LOGS_DIR_NAME, LOGS_FILE_NAME)

folder_name = 'photos_from_vk'
user_id = 'begemot_korovin'


def write_to_log(data: str, file_path: str = file_path):
    with open(file_path, 'a') as file_log:
        str_log = f'{datetime.now()} | {data} \n'
        file_log.write(str_log)


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def upload(self, url_path: str, file_path: str):
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        dict_header = {'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        dict_params = {"path": file_path, "url": url_path}
        resp = requests.post(url, headers=dict_header, params=dict_params)
        resp.raise_for_status()
        if resp.status_code == 202:
            write_to_log(f'Success, photo {file_path} uploaded.')
        else:
            write_to_log(f'Something wrong, photo {file_path} not uploaded. Status code: {resp.status_code}')

    def create_folder(self, folder_name: str):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        dict_header = {'Accept': 'application/json', 'Authorization': f'OAuth {self.token}'}
        dict_params = {"path": folder_name}
        resp = requests.put(url, headers=dict_header, params=dict_params)
        if resp.status_code == 409:
            write_to_log(f'Folder {folder_name} already exists.')
        elif resp.status_code == 201:
            write_to_log(f'Success, folder {folder_name} created.')
        else:
            write_to_log(f'Something wrong. Folder {folder_name}. Status code: {resp.status_code}')


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token: str, version: str):
        self.params = {
            'access_token': token,
            'v': version
        }

    def get_user_id(self, owner_id: str):
        get_user_id_url = self.url + 'users.get'
        get_user_id_params = {
            'user_ids': owner_id,
        }
        req = requests.get(get_user_id_url, params={**self.params, **get_user_id_params}).json()
        return req['response'][0]['id']

    def get_photos(self, owner_id: str, count: int = 5, album_id: str = 'profile'):
        owner_id = self.get_user_id(owner_id)
        get_photos_url = self.url + 'photos.get'
        get_photos_params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'count': count,
            'extended': '1',
            'photo_sizes': '1'
        }
        req = requests.get(get_photos_url, params={**self.params, **get_photos_params}).json()

        items = req['response']['items']
        list_of_photos = []
        likes_dict = {}
        for photo in items:
            temp_dict = {}
            sizes_list = photo['sizes']
            url_photo = sizes_list[-1]['url']
            size_photo = sizes_list[-1]['type']
            temp_dict['size'] = size_photo
            likes = photo['likes']
            likes_count = str(likes['count'])
            if likes_count not in likes_dict:
                likes_dict[likes_count] = 1
                file_name = f'{likes_count}'
            else:
                if likes_dict[likes_count] == 1:
                    file_name = f"{likes_count}_{datetime.now().strftime('%Y%m%d')}"
                else:
                    file_name = f"{likes_count}_{datetime.now().strftime('%Y%m%d')}_{likes_dict[likes_count] - 1}"
                likes_dict[likes_count] += 1
            temp_dict['file_name'] = f'{file_name}.jpg'
            temp_dict['url_photo'] = url_photo
            list_of_photos.append(temp_dict)
        return list_of_photos


def main():
    yadisk_token = api.yadisk_token
    uploader = YaUploader(yadisk_token)
    uploader.create_folder(folder_name)

    vk_token = api.vk_token
    vk_client = VkUser(vk_token, '5.131')

    photos_list = vk_client.get_photos(user_id)
    for photo in photos_list:
        url_photo = photo.pop('url_photo')
        uploader.upload(url_photo, f'{folder_name}/{photo["file_name"]}')

    file_path_json = os.path.join(BASE_PATH, 'photos.json')
    with open(file_path_json, 'w') as file_json:
        json.dump(photos_list, file_json, indent=2)


if __name__ == '__main__':
    main()