# horus-udp-to-basestation
This program will receive Horus UDP packets (such as those created by [radiosonde_auto_rx](https://github.com/projecthorus/radiosonde_auto_rx)), and output SBS BaseStation messages, allowing positions of radiosondes to be plotted with Virtual Radar Server.

This program assigns each radiosonde a Mode-S code (unique identifier within BaseStation messages) to allow programs receiving the BaseStation messages to be able to distinguish between radiosondes. This data is stored in the `icaos.json` file, allowing the program to be restarted without giving changing the matched Mode-S code of a radiosonde.

This code was based on the examples provided within [radiosonde_auto_rx](https://github.com/projecthorus/radiosonde_auto_rx/).

# Installation
Rename the `example_config.py` to `config.py` and change the values accordingly.

The BaseStation output socket listens for connections, so Virtual Radar Server must **not** have the receiver configured as a  push receiver.
