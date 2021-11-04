import setuptools
from rsudp import _version

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="rsudp",
    version=_version.version,
    author="Ian Nesbitt",
    author_email="ian.nesbitt@raspberryshake.org",
    license='GPLv3',
    description="Tools for receiving and interacting with Raspberry Shake UDP data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/raspishake/rsudp",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=['obspy', 'numpy', 'matplotlib<3.2', 'pydub', 'twython',
                      'python-telegram-bot'],
    entry_points = {
        'console_scripts': [
            'rs-packetloss=rsudp.packetloss:main',
            'rs-client=rsudp.client:main',
            'rs-test=rsudp.client:test',
            'packetize=rsudp.packetize:main',
            'rs-settings=rsudp.entry_points:ep_edit_settings',
            'rs-log=rsudp.entry_points:ep_cat_log',
            'rs-tailf=rsudp.entry_points:ep_tailf_log',
            ],
    },
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "Framework :: Matplotlib",
        "Topic :: Scientific/Engineering :: Physics",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Development Status :: 5 - Production/Stable",
    ],
)
