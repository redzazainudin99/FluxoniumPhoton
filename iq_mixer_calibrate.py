from qcodes_drivers.E4407B import E4407B
from qcodes_drivers.iq_calibrator import IQCalibrator

from setup_td import *

spectrum_analyzer = E4407B("spectrum_analyzer", "GPIB0::18::INSTR")

print(lo_2pho.frequency())

iq_calibrator = IQCalibrator(
    [__file__, setup_file],
    "D:\Redza\Logs\IQ_Calibration",
    wiring,
    station,
    awg_2,
    awg_2photon_I,
    awg_2photon_Q,
    spectrum_analyzer,
    lo_2pho.frequency(),
    if_lo=-290,  # MHz
    if_hi=290,  # MHz
    if_step=10,  # MHz
    i_amp=0.9,  # V
)

spectrum_analyzer.sweep_time(5e-3)
lo_2pho.output(True)
iq_calibrator.minimize_lo_leakage()
# print(spectrum_analyzer.sweep_time())
iq_calibrator.minimize_image_sideband()
iq_calibrator.measure_rf_power()
