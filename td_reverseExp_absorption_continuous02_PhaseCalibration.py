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


phase = Variable("phase",np.linspace(0, 2*np.pi, 51), "ns")
# delay = Variable("delay",[10,20], "ns")
# duration = Variable("duration",100*np.arange(50) + 4000, "ns")
variables = Variables([phase])


# gf_pi_flat.params['top_duration'] = duration
# gf_pi.params['amplitude'] = amplitude




JPA_phase.params['phase'] = phase


revExp_sequence = Sequence([readout_port, ge_drive_port, gf_drive_port, digi_port])


revExp_sequence.trigger([readout_port,ge_drive_port, gf_drive_port,   digi_port])
revExp_sequence.call(ge_flat_seq)
revExp_sequence.trigger([readout_port,ge_drive_port, gf_drive_port,   digi_port])

# revExp_sequence.call(gf_pi_seq)
# revExp_sequence.add(Square(amplitude=0.01, duration=7000),readout_port, copy=False )

revExp_sequence.add(Delay(7100), digi_port)

# revExp_sequence.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
revExp_sequence.trigger([readout_port,  ge_drive_port, gf_drive_port, digi_port])
revExp_sequence.call(readout_seq_JPA)

# readout_pulse.params["amplitude"] = 1
sequence = Sequence(all_ports)
sequence.call(revExp_sequence)



revExp_sequence_ground = Sequence([readout_port, ge_drive_port, gf_drive_port, digi_port])


revExp_sequence_ground.trigger([readout_port,ge_drive_port, gf_drive_port,   digi_port])
revExp_sequence_ground.add(Delay(ge_flat_pi.params['top_duration'] + ge_pi.params['duration']), ge_drive_port)
revExp_sequence_ground.trigger([readout_port,ge_drive_port, gf_drive_port,   digi_port])

# revExp_sequence.call(gf_pi_seq)
# revExp_sequence.add(Square(amplitude=0.01, duration=7000),readout_port, copy=False )

revExp_sequence_ground.add(Delay(7100), digi_port)

# revExp_sequence.add(digi_acquire, digi_port, copy=False)                             #this is the digiitizer input, which is the reflected readout pulse
revExp_sequence_ground.trigger([readout_port,  ge_drive_port, gf_drive_port, digi_port])
revExp_sequence_ground.call(readout_seq_JPA)

sequence_ground = Sequence(all_ports)
sequence_ground.call(revExp_sequence_ground)


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
    phase = dict(unit = 'rad'),
    s11_g=dict( axes=["phase"]),
    s11_e=dict( axes=["phase"]),
    separation=dict( axes=["phase"]),
    separation_ratio = dict( axes=["phase"]),
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
            s11_e = demodulate(run2(sequence,JPA_TD = True, plot= False).mean(axis=0))

            sequence_ground.update_variables(update_command)
            load_sequence2(sequence_ground, cycles=40000)
            s11_g = demodulate(run2(sequence_ground,JPA_TD = True, plot= False).mean(axis=0))


            digi_ch.delay(0)
            digi_ch.points_per_cycle(points_per_cycle)
            writer.add_data(
                phase=sequence.variable_dict["phase"][0].value/np.pi,
                s11_g = s11_g,
                s11_e = s11_e,
                separation = s11_e - s11_g,
                separation_ratio = (s11_e - s11_g)/s11_e,
            )
