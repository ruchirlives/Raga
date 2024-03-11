from main import *
import random

# Define the scales for Raga Bhairav
scale_arohana = [60, 62, 64, 65, 67, 69, 71]
scale_avarohana = [60, 61, 63, 65, 67, 69, 71]
meendhMap = {
    "8ve": 37,
    "shortup": 38,
    "shortdown": 40,
    "up": 41,
    "down": 43,
    "updown": 47,
    "fifth": 42,
}

bhairav_step_frequencies = {
    # Ascending (Arohana)
    0: 1,  # Sa
    1: 16 / 15,  # Komal Re
    2: 32 / 27,  # Komal Ga
    3: 4 / 3,  # Ma
    4: 3 / 2,  # Pa
    5: 5 / 3,  # Dha
    6: 16 / 9,  # Komal Ni
    # Descending (Avarohana) - typically mirrors the ascending scale in Raga Bhairav
    -1: 16 / 9,  # Komal Ni
    -2: 5 / 3,  # Dha
    -3: 3 / 2,  # Pa
    -4: 4 / 3,  # Ma
    -5: 32 / 27,  # Komal Ga
    -6: 16 / 15,  # Komal Re
    -7: 1,  # Sa
}


def bhairav_base_duration_rule(params):
    # Calculate the base duration
    base_duration = 1.0

    # Snap to the nearest 0.5
    snapped_duration = round(base_duration / 0.5) * 0.5

    return snapped_duration


def bhairav_base_velocity_rule(params):
    note_index = params["note_index"]
    total_notes = params["total_notes"]
    """
    A simple rule for setting the velocity of notes in the Bhairav Raga.
    This example increases velocity towards the middle of the phrase and then decreases it.
    """
    midpoint = total_notes / 2
    if note_index < midpoint:
        # Increase velocity as we approach the middle
        velocity = int(60 + (note_index / midpoint) * (127 - 60))
    else:
        # Decrease velocity as we move away from the middle
        velocity = int(127 - ((note_index - midpoint) / midpoint) * (127 - 60))

    velocity = int(velocity / 2)  # scale down velocity
    return velocity


def bhairav_phrase_velocity_rule(params):

    base_velocity = 64

    # Snap to the nearest 0.5
    snapped_velocity = int(base_velocity)

    return snapped_velocity


def calculate_phrase_duration(phrase, base_duration):
    # Assuming each Note in a phrase has a 'duration' attribute
    return sum(note.relative_duration for note in phrase.notes) * base_duration


def bhairav_phrase_selection_rule(params):
    tal = params["raga"].tal
    bpm = params["raga"].bpm
    base_duration = params["base_duration"]
    phrases = params["raga"].phrases

    # Calculate the duration of each phrase
    phrase_durations = [
        calculate_phrase_duration(phrase, base_duration) for phrase in phrases
    ]

    # Attempt to find a combination of phrases that matches a low multiple of tal
    for attempt in range(100):  # Arbitrary number of attempts to avoid infinite loop
        selected_phrases = random.sample(phrases, 3) if len(phrases) > 3 else phrases
        total_duration = sum(
            phrase_durations[phrases.index(p)] for p in selected_phrases
        )
        beatduration = 60 / bpm
        talduration = tal * beatduration

        if (
            total_duration % talduration == 0
        ):  # Check if total duration is a multiple of tal
            return selected_phrases

    # Fallback if no combination is found
    return phrases  # Or some other default behaviour


# Usage
# params = {'raga': raga_object, 'base_duration': value, ...}
# selected_phrases = bhairav_phrase_selection_rule(params)


def bhairav_phrase_selection_rule_sentence_based(params):

    num_phrases_index = params["phrase_index"]
    num_phrases = params["total_phrases"]
    phrases = params["raga"].phrases

    sentence = "Hello darkness my old friend"
    # If the sentence is longer than the number of phrases, truncate or repeat it
    while len(sentence) < num_phrases:
        sentence += sentence

    # Map the current character to a phrase
    char_index = ord(sentence[num_phrases_index % len(sentence)]) % len(phrases)
    print(char_index)
    return phrases[char_index]


# Bhairav Raga rules
bhairav_rules = {
    "base_duration_rule": bhairav_base_duration_rule,
    "base_velocity_rule": bhairav_base_velocity_rule,
    "phrase_velocity_rule": bhairav_phrase_velocity_rule,
    "phrase_selection_rule": bhairav_phrase_selection_rule,
}

# Create Bhairav Raga object with specific rules
raga_bhairav = Raga(
    "Bhairav",
    scale_arohana,
    scale_avarohana,
    tal=6,
    bpm=60,
    rules=bhairav_rules,
    meendhMap=meendhMap,
    step_frequencies=bhairav_step_frequencies,
)


# Add phrases to Raga Bhairav
def mutate_phrase(phrase):
    mutated_notes = []

    for note in phrase.notes:
        # Randomly decide whether to mutate each aspect of the note
        mutate_step = random.choice([True, False])
        mutate_duration = random.choice([True, False])
        mutate_meendh = random.choice([True, False])

        new_step = note.increment
        new_duration = note.relative_duration
        new_meendh = note.meendh

        # Mutate step
        if mutate_step:
            new_step += random.choice([-1, 0, 1])
            new_step = max(-2, min(2, new_step))  # Keep within a range

        # Mutate duration
        if mutate_duration:
            duration_choices = [0.25, 0.5, 0.75, 1, 1.25, 1.5]
            new_duration = random.choice(duration_choices)

        # Mutate meendh
        if mutate_meendh:
            meendh_choices = [None] + list(meendhMap)
            new_meendh = random.choice(meendh_choices)

        mutated_notes.append(Note(new_step, new_duration, new_meendh))

    return Phrase(mutated_notes)


def generate_random_phrase(num_notes):
    notes = []

    # Ensure the first note's step is always 0
    step = 0
    first_duration = random.choice([0.5, 1, 1.5])
    notes.append(Note(step, first_duration))

    # Generate the rest of the notes
    for _ in range(1, num_notes):
        # Adjust the probability of the next step based on the previous step
        if step == 0:
            step = random.choice([-1, 1])
        else:
            step = random.choice([step, step, step, -1, 0, 1])

        duration = random.choice([0.25, 0.5, 0.75, 1, 1.25, 1.5]) * first_duration
        meendh = random.choice([None, None, None, "updown", "updown"])
        notes.append(Note(step, duration, meendh))

    return Phrase(notes)


phrase1 = Phrase([Note(0, 0.75, "updown"), Note(1, 0.75), Note(1, 1.5, "up")])
phrase2 = Phrase(
    [Note(-1, 0.25, "fifth"), Note(-1, 0.25), Note(-1, 0.25), Note(-1, 1, "updown")]
)
phrase3 = Phrase(
    [
        Note(0, 0.25, "fifth"),
        Note(1, 0.25, "updown"),
        Note(1, 0.25),
        Note(1, 0.25),
        Note(1, 0.25, "updown"),
    ]
)
phrase4 = Phrase(
    [
        Note(0, 0.25, "fifth"),
        Note(-1, 0.5, "updown"),
        Note(-1, 0.25),
        Note(-1, 0.5, "updown"),
        Note(1, 0.25),
    ]
)
phrase5 = Phrase(
    [
        Note(0, 1.5, "fifth"),
        Note(1, 1.5, "updown"),
        Note(1, 1.5),
        Note(1, 1.5, "updown"),
        Note(1, 2),
    ]
)


raga_bhairav.add_phrase(phrase2)
raga_bhairav.add_phrase(mutate_phrase(phrase2))
raga_bhairav.add_phrase(mutate_phrase(phrase2))
raga_bhairav.add_phrase(mutate_phrase(phrase2))
raga_bhairav.add_phrase(mutate_phrase(phrase2))
raga_bhairav.add_phrase(mutate_phrase(phrase2))

raga_bhairav.add_phrase(phrase3)
raga_bhairav.add_phrase(mutate_phrase(phrase3))
raga_bhairav.add_phrase(mutate_phrase(phrase3))
raga_bhairav.add_phrase(mutate_phrase(phrase3))
raga_bhairav.add_phrase(mutate_phrase(phrase3))
raga_bhairav.add_phrase(mutate_phrase(phrase3))

raga_bhairav.add_phrase(phrase5)

# for i in range(1,5):
#     numnotes = random.randint(3,5)
#     phrase = generate_random_phrase(numnotes)
#     print(phrase)
#     raga_bhairav.add_phrase(phrase)

# raga_bhairav.play()
