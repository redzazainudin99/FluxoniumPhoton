import os

import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from tqdm import tqdm

from setup_cw import *

measurement_name = os.path.basename(__file__)[:-3]

vna.sweep_type("linear frequency")
vna.s_parameter("S21")
vna.start(5.3e9)  # Hz
vna.stop(5.4e9)  # Hz
vna.points(1001)
vna.if_bandwidth(80)  # Hz

data = DataDict(
    frequency=dict(unit="Hz"),
    power=dict(unit="dBm"),
    s11=dict(axes=["frequency", "power"])
)
data.validate()

current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=100.8e-6
# current=104.5e-6
# current = 29e-6
assert current_source.current() == 0, "Current should be 0 initially."
current_source.on()
current_source.ramp_current(current,1e-6,0.1)

with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())
    for power in tqdm(np.linspace(-25, 0, 50)):
        vna.power(power)
        vna.run_sweep()
        writer.add_data(
            frequency=vna.frequencies(),
            power=power,
            s11=vna.trace(),
        )


current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()