import os

import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from tqdm import tqdm

from setup_cw import *

measurement_name = os.path.basename(__file__)[:-3]

vna.sweep_type("linear frequency")
vna.s_parameter("S21")
vna.start(5.25e9)  # Hz
vna.stop(5.45e9)  # Hz

vna.points(401)
vna.if_bandwidth(1000)  # Hz
vna.power(-0)  #dBm


#gain peak here
amp_frequency = 5.352e9
#set the current bias value
# current_bias =95.8e-6
current_bias = 90.7e-6

pump_source.frequency(2*amp_frequency + 0.00e9)

#power values for pump signal
power_vals = np.linspace(-20, 19, 101)

data = DataDict(
    frequency=dict(unit="Hz"),
    power=dict(unit="dBm"),
    s11=dict(axes=["frequency","power"])
)
data.validate()

current_source2.ramp_current(0, step=5e-7, delay=0)
current_source2.off()

try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.add_tag(measurement_name)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        pump_source.output(True)
        current_source2.on()
        assert current_source2.state()
        current_source2.ramp_current(current_bias, step=5e-8, delay=0)
        for power in tqdm(power_vals):
            pump_source.power(power)
            vna.run_sweep()
            writer.add_data(
                frequency=vna.frequencies(),
                power=power,
                s11=vna.trace(),
            )
finally:
    current_source2.ramp_current(0, 5e-8, 0)
    current_source2.off()
    pump_source.output(False)
    print("finished")