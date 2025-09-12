import time

import qcodes as qc
from qcodes.instrument_drivers.yokogawa.GS200 import GS200

from qcodes_drivers.E82x7 import E82x7
from qcodes_drivers.N5222A import N5222A
from N51xx import N51xx

#Logging
setup_file = __file__
tags = ["CW", "CDK181", "ShelvingFluxonium"]
data_path = "D:\Redza\Logs"
wiring = "\n".join([
    """
    readout
    N5222A port 1 - 2000mm - 20 dBm - 10 dBm - in2A
    out2A - 2000mm - N5222A port 2

    drive 
    E8257D - 10 dBm - 10 dBm - 10 dBm  - 10 dBm - 10 dBm  - in2B

    """,
    ])


#Device list
#Input IP addresses of devices used here
station = qc.Station()

#Visual network analyzer
vna = N5222A("vna", "TCPIP0::192.168.100.73::inst0::INSTR")
vna.electrical_delay(49.677512e-9)  # s
vna.meas_trigger_input_type("level")
vna.meas_trigger_input_polarity("positive")
vna.aux1.output_polarity("negative")
vna.aux1.output_position("after")
vna.aux1.aux_trigger_mode("point")
station.add_component(vna)

#qubit drive source
drive_source:E82x7 = E82x7("drive_source", 'TCPIP0::192.168.100.7::inst0::INSTR')
drive_source.trigger_input_slope("positive")

#JPA pump source
pump_source = N51xx("pump_source", 'TCPIP0::192.168.100.9::inst0::INSTR')
pump_source.trigger_input_slope("positive")

#drive current source
current_source = GS200("current_source", "TCPIP0::192.168.100.99::inst0::INSTR")
station.add_component(current_source)

# #JPA current source
current_source2 = GS200("current_source2", "TCPIP0::192.168.100.95::inst0::INSTR")
station.add_component(current_source2)



#CW measurement related functions
def configure_drive_sweep(vna_freq: float, points: int):
    vna.sweep_type("linear frequency")
    vna.start(vna_freq)
    vna.stop(vna_freq)
    vna.points(points)
    vna.sweep_mode("hold")
    vna.trigger_source("external")
    vna.trigger_scope("current")
    vna.trigger_mode("point")
    vna.aux1.output(True)
    drive_source.frequency_mode("list")
    drive_source.point_trigger_source("external")
    drive_source.sweep_points(points)
    vna.meas_trigger_input_delay(0.02)
    # print(vna.meas_trigger_input_delay())

def run_drive_sweep():
    vna.output(True)
    drive_source.output(True)
    drive_source.start_sweep()
    vna.sweep_mode("single")
    try:
        while not (vna.done() and drive_source.sweep_done()):
            time.sleep(0.1)
    finally:
        vna.output(False)
        drive_source.output(False)
