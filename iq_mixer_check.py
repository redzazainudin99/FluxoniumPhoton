import matplotlib.pyplot as plt

from qcodes_drivers.E4407B import E4407B
from qcodes_drivers.iq_corrector import IQCorrector
from setup_td import *

spectrum_analyzer = E4407B("spectrum_analyzer", "GPIB0::18::INSTR")

iq_corrector = IQCorrector(
    awg_2photon_I,
    awg_2photon_Q,
    "D:\Redza\Logs\IQ_calibration",
    lo_leakage_datetime="2025-09-11T122304",
    rf_power_datetime="2025-09-11T122555",
    len_kernel=41,
    fit_weight=10,
    plot=True,
)
plt.show()

lo_2pho.output(True)
iq_corrector.check(
    [__file__, setup_file],
    "D:\Redza\Logs\IQ_calibration",
    wiring,
    station,
    awg_2,
    spectrum_analyzer,
    lo_2pho.frequency(),
    if_step=10,
    amps=np.linspace(0., 1, 14),
)
