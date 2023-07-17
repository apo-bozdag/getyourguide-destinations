# -*- coding: utf-8 -*-
""" FileDescription """
__author__ = 'abdullahbozdag'
__creation_date__ = '17.07.2023'

import json

read_file_name = 'new_city.json'
new_file_name = 'shorex-list.json'

# read json file
with open(read_file_name, 'r') as f:
    data = json.load(f)

# create new json file
new_data = []
for item in data:
    for city in item.get('cities', []):
        new_data.append({
            'name': city.get('name'),
            'coordinate': {
                'lat': 0,
                'lng': 0
            },
            'must_tastes': [],
            'country': {
                'name': item.get('country'),
                'continent': {
                    'name': item.get('continent')
                }
            },
            'image': {
                'url': city.get('image'),
            }
        })

with open(new_file_name, 'w') as f:
    json.dump(new_data, f, indent=4)

print('done')
