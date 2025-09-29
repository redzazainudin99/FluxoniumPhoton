
from sequence_parser.instruction.pulse import Pulse, PulseShape
import copy
import numpy as np


import os

import matplotlib.pyplot as plt
import numpy as np
from plottr.data.datadict_storage import DataDict, DDH5Writer
from sequence_parser import Port, Sequence, Variable, Variables
from tqdm import tqdm
import qcodes as qc
import qcodes.utils.validators as vals
from plottr.data.datadict_storage import search_datadict




class SechPulseShape(PulseShape):
    def __init__(self):
        super().__init__()
        
    def set_params(self, pulse):
        self.amplitude = pulse.tmp_params["amplitude"]
        self.duration = pulse.duration

    def model_func(self, time):
        waveform = self.amplitude * (np.cosh(time / self.duration))**(-2)
        return waveform

class SechPulse(Pulse):
    def __init__(
        self,
        amplitude = 1,
        duration = 100,
        zero_end = False,
    ):
        super().__init__()
        self.pulse_shape = SechPulseShape()
        self.params = {
            "amplitude" : amplitude,
            "duration" : duration,
            "zero_end" : zero_end
        }

    def _get_duration(self):
        self.duration = self.tmp_params["duration"]

readout_port = Port("readout_port", if_freq =1, max_amp=1.5)

# show_plots = False
seq = Sequence([readout_port])
seq.add(ReversePhoton(zero_end=False), readout_port)

seq.draw()