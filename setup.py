import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="rsudp",
    version="0.1.1",
    author="Ian Nesbitt",
    author_email="ian.nesbitt@raspberryshake.org",
    license='GPL',
    description="Tools for receiving and interacting with Raspberry Shake UDP data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/iannesbitt/readgssi",
    packages=setuptools.find_packages(),
    install_requires=['obspy', 'numpy', 'matplotlib'],
    entry_points = {
        'console_scripts': [
            'shake_local=rsudp.shake_udp_local:main',
            'shake_remote=rsudp.shake_udp_remote:main',
            'shake_packetloss=rsudp.shake_udp_packetloss:main',
            'shake_obspy_plot=rsudp.obspy_example:main',
            'shake_liveplot=rsudp.live_example:main',
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
