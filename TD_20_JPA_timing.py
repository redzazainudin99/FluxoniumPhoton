from setup_td import *

measurement_name = os.path.basename(__file__)[:-3]

cycles = 10000
hvi_trigger.digitizer_delay(0)
hvi_trigger.trigger_period(10000)

seq = Sequence(port_list=[readout_port, digi_port, JPA_port])
# seq.call(seq_JPA)
seq.add(Square(amplitude=1.3, duration=1000), JPA_port)
seq.add(Acquire(2000), digi_port)

# seq.draw()
# raise SystemError
data = DataDict(
    time=dict(unit="ns"), 
    mean=dict(axes=["time"]),
    std=dict(axes=["time"]),
)
data.validate()

current_source.ramp_current(0, step=5e-7, delay=0)
current_source.off()

current=100.8e-6

current_source.on()
current_source.ramp_current(current,5e-7,0.1)


#Continuous JPA amplification setup here!
JPA_current_source.ramp_current(0, step=5e-7, delay=0)
JPA_current_source.off()

current_JPA=90.7e-6

JPA_current_source.on()
JPA_current_source.ramp_current(current_JPA,5e-7,0.1)

digi_ch.cycles(cycles)
try:
    with DDH5Writer(data, data_path, name=measurement_name) as writer:
        writer.add_tag(tags)
        writer.backup_file([__file__, setup_file])
        writer.save_text("wiring.md", wiring)
        writer.save_dict("station_snapshot.json", station.snapshot())
        load_sequence2(seq, cycles=cycles)
        data = run2(seq,JPA_TD = True) * voltage_step
        mean = data.mean(axis=0)
        stderr = data.std(axis=0)
        writer.add_data(
            time=digi_ch.sampling_interval()*np.arange(len(mean)),
            mean=mean,
            std=stderr,
        )
        # awg1.flush_waveform()
        digi_ch.stop()
# except:print('An error occurred')
finally:
    print('finished')
