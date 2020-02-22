About rsudp
#####################################

rsudp is a program built to actively monitor and
plot UDP data output from Raspberry Shake seismographs.

Broad overview
*************************************

rsudp is a collection of monitoring and notification tools to accompany the Raspberry Shake.
It contains code for continuous plotting, continuous monitoring of sudden motion,
and distribution of alert notifications via multiple media including audible sound
and the Telegram and Twitter social media platforms.

rsudp is able to run as a stable headless daemon or GUI application continuously
on most systems with sufficent RAM, and can be used to power both a display kiosk
and notification system simultaneously.

Why it's special
*************************************

rsudp's uses as an educational tool in both seismology and computer science are broad.

The demands of real-time seismic processing
require that calculations must be made quickly and
remain stable for weeks or months without user intervention.
rsudp aims to achieve both of these things,
while maintaining a codebase lean enough to run on Raspberry Pi
but intuitive enough that users can learn the theory of
real time continuous data processing and contribute code of their own.
The project's source repository is `here <https://github.com/raspishake/rsudp>`_.

Programs that do similar tasks are usually not as fully-featured, cost money,
are unmaintained, or are complex to set up and run.
We have tried to keep dependencies to a minimum and installation simple
across multiple platforms.

In addition, we spent many hours making rsudp's plotting routines a beautiful
and informative way to explore the vibrations that move through Earth's crust.
Whether looking at an earthquake trace from far away or a car going by on a street,
the plots are designed to show the user the character of the vibration in an easy
to grasp yet informative format.

While the plotting may be the centerpiece of the program,
perhaps the most useful aspect of rsudp is its ability to monitor sudden motion
and trigger multiple outcomes and actions when events are detected.
Additionally, the way it was designed leaves room for developers
to add their own code to be run when events are detected.

rsudp is a special and unique piece of software in the seismological community
which brings easy-to-use open-source monitoring to low cost instrumentation.

What can't rsudp do?
*************************************

As noted in the `license <https://github.com/raspishake/rsudp/blob/master/LICENSE>`_
Raspberry Shake S.A. does not assume any liability or make any guarantee regarding
the performance of this software in detecting earthquakes.
Due to the unpredictable nature of earthquakes and the fact that this is not professional
monitoring software, this software should not be used to protect life or property.

Due to the limitations of the Raspberry Pi 3B's RAM modules, rsudp will run but occasionally
suffer from memory errors if the plotting module is enabled.
It can be programmed as a daemon in order to restart in the event of one of these errors,
which means that its monitoring capability may have brief periods of non-availability
on these devices (after :ref:`installing`, see :ref:`daemon`).
The Raspberry Pi 4B does not seem to suffer nearly as much from this issue,
but this has not been tested extensively.

`Back to top ↑ <#top>`_
