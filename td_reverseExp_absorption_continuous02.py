#this is to check the time delay between the readout pulse and digitizer pulse

import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer

from sequence_parser import Sequence
from setup_td import *
from ReverseExpPulse import * 
# from setup_td_pulses import *

measurement_name = os.path.basename(__file__)[:-3]


duration = Variable("duration",10 + 40*np.arange(150), "ns")
amplitude = Variable("amplitude",np.linspace(0,1, 10), "V")
# delay = Variable("delay",[10,20], "ns")
# duration = Variable("duration",100*np.arange(50) + 4000, "ns")
variables = Variables([duration,amplitude])


gf_pi_flat.params['top_duration'] = duration
gf_pi.params['amplitude'] = amplitude




JPA_phase.params['phase'] = 0.2 * np.pi
revExp_sequence = Sequence([readout_port, ge_drive_port, gf_drive_port, digi_port])


revExp_sequence.trigger([readout_port,ge_drive_port, gf_drive_port,   digi_port])
revExp_sequence.call(ge_flat_seq)
revExp_sequence.trigger([readout_port,ge_drive_port, gf_drive_port,   digi_port])

revExp_sequence.call(gf_pi_seq)
revExp_sequence.add(Square(amplitude=0.01, duration=7000),readout_port, copy=False )

revExp_sequence.add(Delay(7100), digi_port)

# revExp_sequence.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
revExp_sequence.trigger([readout_port,  ge_drive_port, gf_drive_port, digi_port])
revExp_sequence.call(readout_seq_JPA)

# readout_pulse.params["amplitude"] = 1
sequence = Sequence(all_ports)
sequence.call(revExp_sequence)


# check_sequence(sequence, variables, idxlist=[1,-1])
# raise SystemError
# plt.plot(readout_port.waveform.real)
# plt.show()
# raise SyntaxError
# lo_readout.power(20)
hvi_trigger.digitizer_delay(0)

points_per_cycle = 5000
time = np.arange(points_per_cycle) * digi_ch.sampling_interval()

data = DataDict(
    duration=dict(unit="ns"),
    amplitude = dict(unit= 'V'),
    s11=dict( axes=["duration",'amplitude']),
    )

data.validate()



# #In cases where more than 60000 cycles are needed, repeat the measurements with this!
# extra_reps = 200


with DDH5Writer(data, data_path, name=measurement_name) as writer:
    writer.add_tag(tags)
    writer.backup_file([__file__, setup_file])
    writer.save_text("wiring.md", wiring)
    writer.save_dict("station_snapshot.json", station.snapshot())
    for update_command in tqdm(variables.update_command_list): 
            
            sequence.update_variables(update_command)
            load_sequence2(sequence, cycles=40000)
            data = run2(sequence,JPA_TD = True, plot= False).mean(axis=0)


            digi_ch.delay(0)
            digi_ch.points_per_cycle(points_per_cycle)
            writer.add_data(
                duration=sequence.variable_dict["duration"][0].value,
                amplitude = sequence.variable_dict["amplitude"][0].value,
                s11 = demodulate(data)
            )
