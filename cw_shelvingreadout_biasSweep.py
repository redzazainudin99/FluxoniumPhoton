import os

import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from tqdm import tqdm

from setup_cw import *

measurement_name = os.path.basename(__file__)[:-3]

vna.sweep_type("linear frequency")
vna.s_parameter("S21")
vna.start(5e9)  # Hz
vna.stop(5.5e9)  # Hz
vna.power(-20)  #dBm
vna.points(1001)
vna.if_bandwidth(100)  # Hz

bias_vals = np.linspace(95,105,101)*1e-6

data = DataDict(
    frequency=dict(unit="Hz"),
    current=dict(unit="A"),
    s11=dict(axes=["frequency","current"])
)
data.validate()

current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.add_tag(measurement_name)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        current_source.on()
        for current in tqdm(bias_vals):
            current_source.ramp_current(current, step=5e-8, delay=0)
            vna.run_sweep()
            writer.add_data(
                frequency=vna.frequencies(),
                current=current,
                s11=vna.trace(),
            )
finally:
    current_source.ramp_current(0,5e-7,0.1)
    current_source.off()
    print("finished")