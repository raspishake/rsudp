import os
import json
from rsudp import COLOR


class Settings(dict):
    @staticmethod
    def read_settings(loc: str):
        '''
        Reads settings from a specific location.

        :param str loc: location on disk to read json settings file from
        :return: settings dictionary read from JSON, or ``None``
        :rtype: dict or NoneType
        '''
        settings = None
        settings_loc = os.path.abspath(os.path.expanduser(loc)).replace('\\', '/')
        with open(settings_loc, 'r') as f:
            try:
                data = f.read().replace('\\', '/')
                settings = Settings(json.loads(data))
            except Exception as e:
                print(f'{COLOR['red']}ERROR: Could not load settings file. Perhaps the JSON is malformed?{COLOR['white']}')
                print(f'{COLOR['red']}       detail: {e}{COLOR['white']}')
                print(f'{COLOR['red']}       If you would like to overwrite and rebuild the file, you can enter the command below:{COLOR['white']}')
                print(f'{COLOR['red']}       shake_client -d {loc}{COLOR['white']}')
                exit(2)
        return settings
