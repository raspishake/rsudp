import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="rsudp",
    version="0.4.2",
    author="Ian Nesbitt",
    author_email="ian.nesbitt@raspberryshake.org",
    license='GPLv3',
    description="Tools for receiving and interacting with Raspberry Shake UDP data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/raspishake/rsudp",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=['obspy', 'numpy', 'matplotlib==3.1.1', 'pydub', 'twython',
                      'telepot', 'urllib3==1.24.2'],
    entry_points = {
        'console_scripts': [
            'rs-local=rsudp.shake_udp_local:main',
            'rs-remote=rsudp.shake_udp_remote:main',
            'rs-packetloss=rsudp.shake_udp_packetloss:main',
            'rs-client=rsudp.client:main',
            ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Physics",
        "Natural Language :: English",
        "Development Status :: 5 - Production/Stable",
    ],
)
