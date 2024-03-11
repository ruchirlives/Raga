import mido
import random
import time
import threading


OUTPORT = mido.open_output("loopMIDI Port 3")


class Note:
    def __init__(self, increment=0, relative_duration=1, meendh=None):
        self.increment = increment  # increment (in scale steps) from the starting note
        self.relative_duration = relative_duration
        self.meendh = meendh


class Phrase:
    def __init__(self, notes):
        self.notes = notes

    def get_scale_type(self):
        net_movement = sum(note.increment for note in self.notes)
        return "arohana" if net_movement >= 0 else "avarohana"

    def get_midi_sequence(self, raga, start_scale_step=0, base_duration=1, velocity=64):
        scale_type = self.get_scale_type()
        scale = raga.arohana if scale_type == "arohana" else raga.avarohana

        midi_sequence = []
        current_position = start_scale_step
        total_length = 0

        for note in self.notes:
            current_position += note.increment
            octave_shift = current_position // len(scale)
            note_index = current_position % len(scale)
            midi_note = scale[note_index] + (12 * octave_shift)
            actual_duration = note.relative_duration * base_duration

            meendth = note.meendh
            keysw = (
                raga.meendhMap[meendth] if meendth in raga.meendhMap else None
            )  # need to check this

            wobble_sequence = add_wobble(0, actual_duration, raga.step_frequencies)
            wobble = random.random() > 0.5

            if wobble:
                midi_sequence.append(mido.Message("note_on", note=midi_note))
                midi_sequence += wobble_sequence
            elif keysw:
                midi_sequence.append(mido.Message("note_on", note=keysw))
                midi_sequence.append(
                    mido.Message(
                        "note_on",
                        note=midi_note,
                        velocity=velocity,
                        time=actual_duration,
                    )
                )
                midi_sequence.append(
                    mido.Message("note_off", note=keysw)
                )  # move this up to other function
            else:
                midi_sequence.append(
                    mido.Message(
                        "note_on",
                        note=midi_note,
                        velocity=velocity,
                        time=actual_duration,
                    )
                )
            midi_sequence.append(mido.Message("note_off", note=midi_note))
            total_length += actual_duration

        return midi_sequence, total_length


class Raga:
    def __init__(
        self,
        name,
        arohana,
        avarohana,
        tal=4,
        bpm=120,
        rules=None,
        meendhMap=[],
        step_frequencies={},
    ):
        self.name = name
        self.arohana = arohana
        self.avarohana = avarohana
        self.phrases = []
        self.tal = tal
        self.bpm = bpm
        self.rules = rules if rules is not None else {}
        self.meendhMap = meendhMap
        self.step_frequencies = step_frequencies

    def __setitem__(self, key, value):
        self.rules[key] = value

    def add_phrase(self, phrase):
        self.phrases.append(phrase)

    def play(self, start_scale_step=None):
        if not self.phrases:
            raise ValueError("No phrases added to the Raga")

        played_sequences = []

        # Apply raga-specific rules
        base_velocity, base_duration, phrase_velocity, sequence = self.get_rules()

        start_scale_step = self.set_scale_step(start_scale_step)

        # Generate MIDI sequence
        midi_sequence, playing_time = self.get_midi_sequence(
            start_scale_step, base_duration, phrase_velocity, sequence
        )

        # Apply velocity rule to each note in the sequence
        midi_sequence = self.getvelocities(
            base_velocity, phrase_velocity, midi_sequence
        )

        # Play the sequences
        thread_notes = threading.Thread(target=self.playmidi, args=(midi_sequence,))
        thread_notes.start()

        # if random.random()>0.5:
        # wobble=threading.Thread(target=add_wobble, args = (0, 0.5,  self.step_frequencies))
        # wobble.start()

        # return the length in bars or beats

        return playing_time

    def set_scale_step(self, start_scale_step):
        start_scale_step = (
            start_scale_step if start_scale_step is not None else random.choice([0, 7])
        )

        return start_scale_step

    def get_rules(self):
        base_velocity = self.rules.get("base_velocity_rule", lambda x: 64)
        phrases = self.phrases

        params = {"raga": self}
        base_duration = self.rules.get("base_duration_rule", lambda x: 0.5)(params)
        phrase_velocity = self.rules.get("phrase_velocity_rule", lambda x: 64)(params)

        params = {"raga": self, "base_duration": base_duration}
        sequence = self.rules.get(
            "phrase_selection_rule", lambda x: random.choice(phrases)
        )(params)
        return base_velocity, base_duration, phrase_velocity, sequence

    def get_midi_sequence(
        self, start_scale_step, base_duration, phrase_velocity, sequence
    ):
        midi_sequence = []
        playing_time = 0
        for phrase in sequence:
            midi_sub_sequence, this_playing_time = phrase.get_midi_sequence(
                self, start_scale_step, base_duration, phrase_velocity
            )
            midi_sequence += midi_sub_sequence
            playing_time += this_playing_time
        return midi_sequence, playing_time

    def getvelocities(self, base_velocity, phrase_velocity, midi_sequence):
        for i, msg in enumerate(midi_sequence):
            if msg.type == "note_on":
                params = {
                    "note_index": i,
                    "total_notes": len(midi_sequence),
                    "raga": self,
                }
                msg.velocity = base_velocity(params)
                msg.velocity = int((msg.velocity + phrase_velocity) / 2)
        return midi_sequence

    def playmidi(self, midi_sequence):
        outport = OUTPORT

        for msg in midi_sequence:
            if msg.type == "note_off":
                # For real-time playing, time attribute is not used in 'note_off'
                outport.send(msg)
            else:
                outport.send(msg)
                # Delay for the duration of the note
                time.sleep(msg.time)

    def mmcmidi(self):
        mmc_play = mido.Message("sysex", data=[0x7F, 0x7F, 0x06, 0x02])

        # To send it, open a port and send the message
        print("sending mmc play")
        outport = OUTPORT
        outport.send(mmc_play)


# PITCH BENDING____________________________________________________
import math

# need to change all of this to create a midi sequence rather than actually output the midi.


def send_pitch_bend_ramp(
    current_step, step_delta, duration, step_frequencies, max_bend=8191, outport=OUTPORT
):
    # Calculate the current and target frequency ratios
    current_ratio = step_frequencies.get(current_step)
    target_ratio = step_frequencies.get(current_step + step_delta)

    if current_ratio is None or target_ratio is None:
        raise ValueError("Invalid scale step")

    # Convert ratios to semitones
    current_semitones = 12 * math.log2(current_ratio)
    target_semitones = 12 * math.log2(target_ratio)

    # Calculate the current and target pitch bend values
    current_bend = calculate_pitch_bend_for_semitones(current_semitones, max_bend)
    target_bend = calculate_pitch_bend_for_semitones(target_semitones, max_bend)

    # Wait for half the duration before starting the pitch bend
    time.sleep(duration / 2)

    # Number of steps for the ramp
    ramp_steps = 10  # Adjust for smoother transitions

    # Linearly interpolate between current and target pitch bend
    for i in range(ramp_steps + 1):
        fraction = i / ramp_steps
        bend_value = int(current_bend + (target_bend - current_bend) * fraction)
        bend_message = mido.Message("pitchwheel", pitch=bend_value)
        outport.send(bend_message)
        time.sleep(duration / 2 / ramp_steps)

    # reset
    # bend_message = mido.Message('pitchwheel', pitch=0)


def add_wobble(
    target_step,
    actual_duration,
    step_frequencies,
    max_bend=8191,
    wobble_intensity=500,
    wobble_rate=6,
    outport=OUTPORT,
):
    target_ratio = step_frequencies.get(target_step)
    target_semitones = 12 * math.log2(target_ratio)
    target_bend = calculate_pitch_bend_for_semitones(target_semitones, max_bend)

    wobble_step = wobble_intensity  # Adjust for desired wobble intensity
    wobble_frequency = wobble_rate  # Adjust for desired wobble rate
    num_of_wobbles = int(actual_duration * wobble_frequency)

    seq = []
    for i in range(num_of_wobbles):
        # Alternate pitch bend for wobble
        seq.append(
            mido.Message(
                "pitchwheel",
                pitch=target_bend + wobble_step,
                time=(1 / (2 * wobble_frequency)),
            )
        )
        seq.append(
            mido.Message(
                "pitchwheel",
                pitch=target_bend - wobble_step,
                time=(1 / (2 * wobble_frequency)),
            )
        )
        seq.append(mido.Message("pitchwheel", pitch=0))

    return seq


def calculate_pitch_bend_for_step(step, step_frequencies, max_bend=8191):
    frequency_ratio = step_frequencies.get(step)
    if frequency_ratio is None:
        raise ValueError("Step not defined in Raga Bhairav")

    # Calculate the number of semitones the step represents
    semitones = 12 * math.log2(frequency_ratio)

    # Calculate and return the pitch bend value
    return calculate_pitch_bend_for_semitones(semitones, max_bend)


def calculate_pitch_bend_for_semitones(semitones, max_bend=8191, octave=12):
    # Calculate the fraction of an octave
    fraction_of_octave = semitones / octave

    # Calculate the MIDI pitch bend value
    pitch_bend_value = int(fraction_of_octave * max_bend)
    return pitch_bend_value
