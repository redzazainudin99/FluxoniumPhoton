import os

import matplotlib.pyplot as plt
import numpy as np
import qcodes as qc
import qcodes.utils.validators as vals
from sequence_parser import Sequence, Variable, Variables
from tqdm import tqdm

from setup_td import *
from ReverseExpPulse import *

with open(__file__) as file:
    script = file.read()

measurement_name = os.path.basename(__file__)


freq_vals = np.linspace(gf_freq - 0.1, gf_freq + 0.1, 10)

amplitude = Variable("amplitude",np.linspace(0,1,21), "V")
variables = Variables([amplitude])


gf_pi.params['amplitude'] = 0.8
gf_pi_flat.params['top_duration'] = 7000



sequence = Sequence([readout_port, ge_drive_port, gf_drive_port, JPA_port, digi_port])


sequence.call(ge_flat_seq)
sequence.trigger([readout_port, ge_drive_port,gf_drive_port, JPA_port ,digi_port])

#single photon and absorption pulse here
sequence.add(Square(amplitude = 0.1, duration=9000), readout_port,copy=False)
# sequence.add(Delay(delay),gf_drive_port, copy = False)
sequence.call(gf_pi_seq)


sequence.trigger([readout_port, gf_drive_port, ge_drive_port, JPA_port ,digi_port])
sequence.add(Delay(100),readout_port, copy = False)
sequence.call(readout_seq_JPA)
# sequence.add(Delay(delay),gf_drive_port, copy = False)

# check_sequence(sequence, variables, idxlist=[1,-1])
# raise SystemError




#Current set!
current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=28.88e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)


#Continuous JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=-94.8e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)




data = DataDict(
    frequency = dict(unit = ['GHz']),
    amplitude=dict(unit="V"),
    s11=dict(axes=["amplitude", "frequency"])
)
data.validate() 



try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.add_tag(measurement_name)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        for f in tqdm(freq_vals):
            gf_if_freq = (f - gf_lo_freq)
            for update_command in tqdm(variables.update_command_list):         
                sequence.update_variables(update_command)
                load_sequence2(sequence, cycles=30000)
                # load_sequence_append(reversed_photon,readout_port,sequence, cycles=40000) 
                data = run2(sequence, JPA_TD=True).mean(axis=0)
                s11 = demodulate(data)
                writer.add_data(
                    frequency = f,
                    amplitude = sequence.variable_dict["amplitude"][0].value,
                    s11 = s11,
                )

finally:

    current_source.ramp_current(0, step=5e-7, delay=0)
    current_source.off()

    JPA_current_source.ramp_current(0, step=5e-7, delay=0)
    JPA_current_source.off()
    
    # lo_JPA.output(False)
    print("finished")