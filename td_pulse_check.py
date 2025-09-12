#this is to check the time delay between the readout pulse and digitizer pulse

import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer

from sequence_parser import Sequence
from setup_td import *
# from ReverseExpPulse import * 
# from setup_td_pulses import *

measurement_name = os.path.basename(__file__)[:-3]
readout_phase = ResetPhase(phase=0)
# readout_pulse = ReverseExp(amplitude=1, duration=15000)      
readout_pulse = Square(amplitude=0.3, duration=15000)
digi_acquire = Acquire(duration = readout_pulse.params["duration"]+ 6000)         #pulse input into digiitizer
# readout_acquire = Acquire(duration=15000)

# readout_seq = Sequence([readout_port, JPA_port, digi_port])

# readout_seq.trigger([readout_port,  JPA_port,digi_port])

readout_seq = Sequence([readout_port, digi_port])

readout_seq.trigger([readout_port, digi_port])

# readout_seq.add(ReverseExp(amplitude=0.4, duration=1200),readout_port, copy=False )
# readout_seq.add(Delay(1000), readout_port)
# readout_seq.add(readout_pulse, readout_port, copy=False)
# readout_seq.add(JPA_pulse, JPA_port, copy=False)     
# readout_seq.add(readout_phase, readout_port, copy=False)
# readout_seq.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
# readout_seq.trigger([readout_port,  JPA_port, digi_port])
# readout_seq.add(Delay(10), readout_port)


# readout_seq.add(Square(amplitude=0.4, duration=1200),readout_port, copy=False )
# readout_seq.add(Delay(1000), readout_port)
# readout_seq.add(readout_pulse, readout_port, copy=False)
# readout_seq.add(readout_phase, readout_port, copy=False)
# readout_seq.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
# readout_seq.trigger([readout_port,  digi_port])
# readout_seq.add(Delay(10), readout_port)


# readout_seq.add(Gaussian(amplitude=0.4, fwhm = 500, duration=1200),readout_port, copy=False )
readout_seq.add(Delay(1000), readout_port)
readout_seq.add(readout_pulse, readout_port, copy=False)
readout_seq.add(readout_phase, readout_port, copy=False)
readout_seq.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
readout_seq.trigger([readout_port,  digi_port])
readout_seq.add(Delay(10), readout_port)

# readout_pulse.params["amplitude"] = 1
sequence = Sequence(all_ports)
sequence.call(readout_seq)

# sequence.draw()
# plt.plot(readout_port.waveform.real)
# plt.show()
# raise SyntaxError
lo_readout.power(20)
hvi_trigger.digitizer_delay(0)

points_per_cycle = 10000
time = np.arange(points_per_cycle) * digi_ch.sampling_interval()

data = DataDict(
    time=dict(unit="ns"),
    voltage=dict(unit="V", axes=["time"]),
    )

data.validate()
# sequence.draw()
with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())
    load_sequence2(sequence, cycles=40000)
    digi_ch.delay(0)
    digi_ch.points_per_cycle(points_per_cycle)
    writer.add_data(
        time=time,
        voltage=run2(sequence, plot=True).mean(axis=0) * digi_ch.voltage_step(),
    )
