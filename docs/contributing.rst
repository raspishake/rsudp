Contributing to this project
#####################################

Code contributions
*********************************

Contributions to this project are always welcome.
If you have questions or comments about how this software works,
we want to hear from you.
Even if coding isn't your thing, we want to make it easier for you to get involved.
We monitor both our forums at https://community.raspberryshake.org, and our GitHub
issues page at https://github.com/raspishake/rsudp/issues.

Since the Producer function passes an ALARM queue message when it sees
:code:`Alert.alarm == True`,
other modules can be easily added and programmed to do something when they see this message.

The :py:class:`rsudp.c_custom.Custom` class makes running custom code easy.
If you have suggestions for feature addition of a new module, please open a
`new issue <https://github.com/raspishake/rsudp/issues/new>`_ with the "enhancement" tag.

If you're a developer or feeling adventurous, here are some fun potential projects:

- Windows batch scripts similar to the provided UNIX ones
- GPIO pin interaction module (lights, motor control, buzzers, etc.)
- IFTTT integration
- Integration into other social media apps beyond Telegram and Twitter
- plot `trigger on-off events <https://docs.obspy.org/tutorial/code_snippets/trigger_tutorial.html#advanced-example>`_ using :py:func:`obspy.signal.trigger.trigger_onset` and :py:func:`matplotlib.pyplot.axvline`::

    on_events = [UTCDateTime1, UTCDateTime3]
    for time in on_events:
        plt.axvline(x=time, color='r', linestyle=(0, (14,14)), linewidth=1, alpha=0.7)
    off_events = [UTCDateTime2, UTCDateTime4]
    for time in off_events:
        plt.axvline(x=time, color='g', linestyle=(0, (14,14)), linewidth=1, alpha=0.7)

- a more efficient plotting routine (I'm kidding, that's actually not a fun one)
- a way to run the plot module with the Agg backend in matplotlib, allowing for the creation of screenshots without the need for a plot window


Bugs
***********************

This software, like most, contains bugs and errors.
If you find a bug, please create a GitHub issue.
Be sure to describe the problem clearly, attach your logs
(:code:`/tmp/rsudp/rsudp.log`) and/or copy/paste command line output
in triple backticks \`\`\` like this \`\`\` to format it as code.

`Back to top ↑ <#top>`_