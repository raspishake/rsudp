import os
import json
from rsudp import COLOR


class Settings(dict):
    """
    .. versionadded:: 2.0.1

    Сlass processes configuration files.
    """
    def dump(self, loc: str):
        '''
        Dumps a default settings file to a specified location.

        :param str loc: The location to create the new settings JSON.
        '''
        print(f'Creating a default settings file at {loc}')
        with open(loc, 'w+') as f:
            f.write(self.json)
            f.write('\n')

    @property
    def json(self):
        '''
        Convert Settings to json string

        :return: JSON string
        :rtype: str
        '''
        return json.dumps(self, indent=2)

    @staticmethod
    def read_settings(loc: str):
        '''
        Reads settings from a specific location.

        :param str loc: location on disk to read json settings file from
        :return: settings dictionary read from JSON, or ``None``
        :rtype: Settings or NoneType
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
                print(f'{COLOR['reexitd']}       If you would like to overwrite and rebuild the file, you can enter the command below:{COLOR['white']}')
                print(f'{COLOR['red']}       shake_client -d {loc}{COLOR['white']}')
                exit(2)
        return settings


    def set_default_values(self):
        default_settings = Settings.default_settings()
        for key,value in default_settings.items():
            if self.get(key, None) is None:
                self[key] = value
            if type(value) == dict:
                for s_key,s_value in value.items():
                    if self[key].get(s_key, None) is None:
                        self[key][s_key] = s_value

    @staticmethod
    def default_settings(output_dir='%s/rsudp' % os.path.expanduser('~').replace('\\', '/'), verbose=True):
        '''
        Returns a Settings dict of default settings.

        :param str output_dir: the user's specified output location. defaults to ``~/rsudp``.
        :param bool verbose: if ``True``, displays some information as the string is created.
        :return: Settings
        :rtype: Settings
        '''
        settings = Settings()

        # settings section
        settings["settings"] = {}
        settings["settings"]["port"] = 8888
        settings["settings"]["station"] = "Z0000"
        settings["settings"]["output_dir"] = "output_dir"
        settings["settings"]["debug"] = True

        # printdata section
        settings["printdata"] = {}
        settings["printdata"]["enabled"] = False

        # write section
        settings["write"] = {}
        settings["write"]["enabled"] = False
        settings["write"]["channels"] = ["all"]

        # plot section
        settings["plot"] = {}
        settings["plot"]["enabled"] = True
        settings["plot"]["duration"] = 90
        settings["plot"]["refresh_interval"] = 0
        settings["plot"]["spectrogram"] = True
        settings["plot"]["fullscreen"] = False
        settings["plot"]["kiosk"] = False
        settings["plot"]["eq_screenshots"] = False
        settings["plot"]["channels"] = ["all"]
        settings["plot"]["filter_waveform"] = False
        settings["plot"]["filter_spectrogram"] = False
        settings["plot"]["filter_highpass"] = 0.7
        settings["plot"]["filter_lowpass"] = 2.0
        settings["plot"]["filter_corners"] = 4
        settings["plot"]["spectrogram_freq_range"] = False
        settings["plot"]["upper_limit"] = 15.0
        settings["plot"]["lower_limit"] = 0.0
        settings["plot"]["logarithmic_y_axis"] = False
        settings["plot"]["deconvolve"] = True
        settings["plot"]["units"] = "CHAN"

        # forward section
        settings["forward"] = {}
        settings["forward"]["enabled"] = False
        settings["forward"]["address"] = ["192.168.1.254"]
        settings["forward"]["port"] = [8888]
        settings["forward"]["channels"] = ["all"]
        settings["forward"]["fwd_data"] = True
        settings["forward"]["fwd_alarms"] = False

        # alert section
        settings["alert"] = {}
        settings["alert"]["enabled"] = True
        settings["alert"]["channel"] = "HZ"
        settings["alert"]["sta"] = 6
        settings["alert"]["lta"] = 30
        settings["alert"]["duration"] = 0.0
        settings["alert"]["threshold"] = 3.95
        settings["alert"]["reset"] = 0.9
        settings["alert"]["highpass"] = 0.8
        settings["alert"]["lowpass"] = 9
        settings["alert"]["deconvolve"] = False
        settings["alert"]["units"] = "VEL"
        settings["alert"]["on_plot"] = False # "separate" or "on-main"
        settings["alert"]["on_plot_end_line_color"] = "#D72638"
        settings["alert"]["on_plot_start_line_color"] = "#4C8BF5"

        # alertsound section
        settings["alertsound"] = {}
        settings["alertsound"]["enabled"] = False
        settings["alertsound"]["mp3file"] = "doorbell"

        # custom section
        settings["custom"] = {}
        settings["custom"]["enabled"] = False
        settings["custom"]["codefile"] = "n/a"
        settings["custom"]["win_override"] = False

        # tweets section
        settings["tweets"] = {}
        settings["tweets"]["enabled"] = False
        settings["tweets"]["tweet_images"] = True
        settings["tweets"]["api_key"] = "n/a"
        settings["tweets"]["api_secret"] = "n/a"
        settings["tweets"]["access_token"] = "n/a"
        settings["tweets"]["access_secret"] = "n/a"
        settings["tweets"]["extra_text"] = ""

        # telegram section
        settings["telegram"] = {}
        settings["telegram"]["enabled"] = False
        settings["telegram"]["send_images"] = True
        settings["telegram"]["token"] = "n/a"
        settings["telegram"]["chat_id"] = "n/a"
        settings["telegram"]["extra_text"] = ""
        settings["telegram"]["upload_timeout"] = 10

        # rsam section
        settings["rsam"] = {}
        settings["rsam"]["enabled"] = False
        settings["rsam"]["quiet"] = True
        settings["rsam"]["fwaddr"] = "192.168.1.254"
        settings["rsam"]["fwport"] = 8887
        settings["rsam"]["fwformat"] = "LITE"
        settings["rsam"]["channel"] = "HZ"
        settings["rsam"]["interval"] = 10
        settings["rsam"]["deconvolve"] = False
        settings["rsam"]["units"] = "VEL"

        if verbose:
            print('By default output_dir is set to %s' % output_dir)
        return settings
