import os

import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from tqdm import tqdm

from setup_cw import *

measurement_name = os.path.basename(__file__)[:-3]

vna.s_parameter("S21")
powers = np.linspace(-9, 20, 31)  # dBm
vna.power(-10)  # dBm
vna.if_bandwidth(300)  # Hz

# drive_source.frequency_start(0.15e9)
# drive_source.frequency_stop(0.3e9)
drive_source.frequency_start(0e9)
drive_source.frequency_stop(0.5e9)
# drive_source.power(30)
configure_drive_sweep(vna_freq=5.3528e9, points=201)
# configure_drive_sweep(vna_freq=7.827e9, points=101)

current=100.8e-6

data = DataDict(
    frequency=dict(unit="Hz"),
    power=dict(unit="dBm"),
    s11=dict(axes=["frequency", "power"])
)
data.validate()

current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.add_tag(measurement_name)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())
    current_source.current(0)
    assert current_source.current() == 0, "Current should be 0 initially."
    current_source.on()
    current_source.ramp_current(current,1e-6,0.1)
    for power in tqdm(powers):
        drive_source.power(power)
        run_drive_sweep()
        writer.add_data(
            frequency=drive_source.frequencies(),
            power=power,
            s11=vna.trace(),
        )

current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()
