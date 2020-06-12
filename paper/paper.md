---
title: 'rsudp: A Python package for real-time seismic monitoring with Raspberry Shake instruments'
tags:
  - Python
  - seismology
  - monitoring
  - earthquake alerts
  - Raspberry Shake
authors:
  - name: Ian M. Nesbitt^[Corresponding author]
    orcid: 0000-0001-5828-6070
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Richard I. Boaz
    affiliation: 1
  - name: Justin Long
    affiliation: 3
affiliations:
  - name: Raspberry Shake, S.A.
    index: 1
  - name: School of Earth and Climate Sciences, University of Maine
    index: 2
  - name: Waterbear Energy
    index: 3
date: 11 June 2020
bibliography: paper.bib

---

# Statement of Need

The uses of low-cost seismographs in science and education are becoming more
widely known as these devices become more popular
[@Anthony:2018; @Walter:2019; @Diaz:2020; @Subedi:2020]. Raspberry Shake
seismographs are commonly used in schools, by Shake community members, and
other individuals having no formal training in seismology. The existence of
this class of instruments highlighted the need for easy-to-use visualization
and notification software to complement these devices. Because all Raspberry
Shake instruments are able to forward data as user datagram protocol (UDP)
packets, taking the opportunity to exploit the existence of this streaming data
was obvious.

![Chart of producer and consumer threads and the organization of data flow in `rsudp`. In order to maximize computational efficiency, features are broken into modules—each module constituting a thread—and data is passed to each module through an asynchronous queue. Inset: thread hierarchy and ownership chart, color-coded by function. Note that the Plot module is owned by the main thread, since `matplotlib` objects can only be created and destroyed by the main thread.\label{fig:flow}](flow.png)

# Summary

`rsudp` is a multi-featured, continuous monitoring tool for both Raspberry
Shake seismographs⁠, used to record both weak and strong ground motion⁠—and
Raspberry Boom pressure transducer instruments, used to record infrasound
waves. To encourage hands-on community involvement, `rsudp` is open-source,
written in Python, and utilizes easy-to-use tools common to the seismology
community, including `matplotlib` visualizations [@Hunter:2007] and the `obspy`
seismic framework for Python [@Beyreuther:2007; @Megies:2011; @Krischer:2015].
`rsudp` is multi-threaded and architected according to a modular
producer-consumer data-flow paradigm (\autoref{fig:flow}). The detection
algorithm employs a recursive short-term/long-term average ratio (STA/LTA)
computation threshold function from `obspy`, executed repeatedly within a loop
over the incoming data.

![An earthquake trace plotted with a spectrogram on multiple data channels in `rsudp`. The spectrograms are a representation of the fraction of maximum frequency power of the signal on each channel over the duration of the plot. Note that the first channel is data recorded with a geophone (EHZ), and the next three are accelerometers (ENE, ENN, ENZ).\label{fig:event}](event.png)

`rsudp` can be used by seismologists as a data analysis tool operating in real
time, and as a way for students, citizen scientists, and other end-users to
easily visualize and conceptualize live-streaming seismic data
(\autoref{fig:event}). Using the application’s simple and straightforward
framework, power-users can run their own custom code in the case of detected
strong motion. The distribution already contains many useful data-processing
modules, including: sound alerts, automated and instantaneous social media
notifications, data-forwarding, real-time seismic amplitude (RSAM) forwarding,
integrated logging, a miniSEED data archiver, and external script execution
(for example, to control input/output pins or some other programmable action).
The combination of speed, easy-to-interpret visualization, and ease of
customization makes `rsudp` a valuable and instructive companion to the
Raspberry Shake family of instruments for researchers, students, and amateur
seismologists alike.


# Acknowledgements

Financial support for this project comes from Raspberry Shake S.A. We are
grateful to Trinh Tuan Vu for his help authoring Windows setup scripts, Branden
Christensen for helpful reviews and guidance, and to Leif Lobinsky for design
input.


# References