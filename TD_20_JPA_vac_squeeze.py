from setup_td import *
from tqdm import tqdm
measurement_name = os.path.basename(__file__)[:-3]

shot_count = 50000
repetition = 1
hvi_trigger.digitizer_delay(400)
hvi_trigger.trigger_period(10000)

# target_frequency = 10.32
target_frequency = readout_freq
JPA_port.if_freq = (target_frequency * 2 - readout_lo_freq * 2)
demodulation_if = readout_lo_freq - target_frequency

var = Variables()
amplitude = Variable("amplitude", np.linspace(0.1, 1.3, 6), "V")

var.add(amplitude)
var.compile()
seq_JPA = Sequence(port_list=[JPA_port])
seq_JPA.add(Square(amplitude=amplitude, duration=2000), JPA_port, copy=False)
seq = Sequence(port_list=[digi_port, JPA_port])
seq.call(seq_JPA)
seq.add(Acquire(80), digi_port)

data = DataDict(
    pump_amplitude=dict(unit="V"),
    s11=dict(axes=["pump_amplitude"]),
)
data.validate()

digi_ch.cycles(shot_count)
try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        for update_command in tqdm(var.update_command_list):
            result = []
            for _ in range(repetition):
                seq.update_variables(update_command)
                load_sequence(seq, cycles=shot_count)
                s11 = demodulate(run(seq), demodulation_if=-demodulation_if) * voltage_step
                result = np.append(result, s11)
            writer.add_data(
                pump_amplitude=seq.variable_dict["amplitude"][0].value,
                # shot_count=np.arange(shot_count),
                s11=result,
            )
            # awg_2.flush_waveform()
            digi_ch.stop()
except:print('An error occurred')
finally:
    print('finished')