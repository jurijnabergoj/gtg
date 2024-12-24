import pyaudio
import numpy as np
import aubio
import time

# Standard tuning for a 6-string guitar (frequencies in Hz)
guitar_tuning = [82.41, 110.00, 146.83, 196.00, 246.94, 329.63]  # E2, A2, D3, G3, B3, E4
string_names = ["E", "A", "D", "G", "B", "e"]
MAX_MOVEMENT_COST = 8
# Data structure to store detected notes
detected_notes = []


def find_tab_positions(frequency):
    """Map detected frequency to guitar tablature positions."""
    if frequency == 0:
        return None  # Silence or unrecognized
    positions = []
    for i, base_freq in enumerate(guitar_tuning):
        for fret in range(0, 21):  # Standard guitars have 20 frets
            note_freq = base_freq * (2 ** (fret / 12))
            if abs(note_freq - frequency) < 3:  # Allow slight deviation
                positions.append((string_names[i], fret))
                break  # Stop after the first match for this string
    return positions


def update_last_three_notes(new_note):
    """Update the list of last three notes with the latest note."""
    global last_three_notes
    last_three_notes.append(new_note)
    if len(last_three_notes) > 3:  # Keep only the last three notes
        last_three_notes.pop(0)


def select_appropriate_string_min(positions, previous_position=None):
    """Select the easiest string and fret combination."""
    if not positions:
        return None
    # Prioritize lower frets and choose the lowest string when possible
    # return min(positions, key=lambda x: (x[1], string_names.index(x[0])))
    return min(positions, key=lambda x: (x[1], -string_names.index(x[0])))


def select_appropriate_string2(positions, recent_notes=None):
    """
    Select the string and fret combination that minimizes movement considering recent notes.
    Recent notes are weighted to prioritize smoother transitions and lower fret positions.

    Args:
        positions (list): Possible positions [(string, fret), ...].
        recent_notes (list): Last n notes played as [(string, fret), ...].

    Returns:
        tuple: Selected (string, fret) position.
    """
    if not positions:
        return None

    def movement_cost(position):
        string, fret = position
        cost = 0

        # Weighted cost based on recent notes
        for i, recent_note in enumerate(reversed(recent_notes)):
            prev_string, prev_fret = recent_note
            weight = 1 / (i + 1)  # More recent notes have higher weight
            string_change = abs(string_names.index(string) - string_names.index(prev_string))
            fret_change = abs(fret - prev_fret)
            cost += weight * np.sqrt(string_change ** 2 + fret_change ** 2)

        # Default to lower fret positions
        cost += 0.1 * fret  # Small penalty for higher frets
        return cost

    # Calculate costs for all positions
    costs = [(position, movement_cost(position)) for position in positions]

    # Filter out positions that exceed the threshold
    if current_time - note_last_time > NOTE_PAUSE_THRESHOLD:
        valid_positions = [pos for pos, cost in costs]
        recent_notes = []
    else:
        valid_positions = [pos for pos, cost in costs if cost <= MAX_MOVEMENT_COST]

    # Return the position with the minimum cost if valid positions exist
    if valid_positions and recent_notes:
        result = min(valid_positions, key=movement_cost)
        # print(abs(string_names.index(result[0]) - string_names.index(recent_notes[-1][0])))
        if abs(string_names.index(result[0]) - string_names.index(recent_notes[-1][0])) >= 2:
            return None
        else:
            return result
    elif valid_positions:
        return min(valid_positions, key=movement_cost)
    # If no valid positions, return None
    return None


def select_appropriate_string(positions, previous_position=None):
    """
    Select the string and fret combination that minimizes movement from the previous note.
    Prioritize lower frets and same strings when possible.
    """

    if not positions:
        return None

    def movement_cost(position):
        string, fret = position
        if previous_position:
            prev_string, prev_fret = previous_position
            string_change = abs(string_names.index(string) - string_names.index(prev_string))
            fret_change = abs(fret - prev_fret)
            return np.sqrt(string_change ** 2 + fret_change ** 2)
        return fret  # Default to lower frets if no previous position

    return min(positions, key=movement_cost)


def matches_previous_note(prev_position, position):
    if prev_position == position:
        return True

    return False


# PyAudio setup
buffer_size = 1024
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=samplerate,
                input=True,
                frames_per_buffer=buffer_size)

# Aubio setup
tolerance = 0.2
win_s = 4096  # FFT size
hop_s = buffer_size  # Hop size
pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("Hz")
pitch_o.set_tolerance(tolerance)


def save_note_to_file(note, filename="output_tab.txt"):
    """Append a single note to the file."""
    with open(filename, "a") as f:
        string, fret = note["position"]
        rel_start = note["start_time"] - start_offset
        f.write(f"{rel_start:.2f},{string},{fret}\n")


print("*** Starting real-time pitch detection. Press Ctrl+C to exit. ***")

note_active = None
start_offset = time.time()
last_three_notes = []

# Add a time threshold to detect repeated notes
NOTE_REPEAT_THRESHOLD = 0.7  # Time in seconds to consider a note as repeated
NOTE_PAUSE_THRESHOLD = 3  # Time in seconds to consider a note as
note_last_time = 0  # Last detected time for a note
note_signal_max = 0  # Last detected signal max for a note

try:
    with open("output_tab.txt", "w") as f:  # Clear the file at the start
        pass
    start_offset = time.time()  # Initialize start time
    while True:
        audiobuffer = stream.read(buffer_size, exception_on_overflow=False)
        signal = np.frombuffer(audiobuffer, dtype=np.float32)
        pitch = pitch_o(signal)[0]
        confidence = pitch_o.get_confidence()
        current_time = time.time()

        if confidence > -0.7:  # Only process if confidence is high
            positions = find_tab_positions(pitch)
            if positions:
                # selected_position = select_appropriate_string(
                #     positions,
                #     note_active["position"] if note_active else None
                # )
                selected_position = select_appropriate_string2(
                    positions,
                    recent_notes=last_three_notes
                )
                if not selected_position:
                    continue

                b = ((not note_active) or
                     (note_active["position"] != selected_position)
                     or
                     ((note_active["position"] == selected_position)
                      and (current_time - note_last_time > NOTE_REPEAT_THRESHOLD)
                      and (abs(note_signal_max - signal.max()) <= 0.01)))

                if ((not note_active) or
                        (note_active["position"] != selected_position)
                        or
                        ((note_active["position"] == selected_position)
                         and (current_time - note_last_time > NOTE_REPEAT_THRESHOLD)
                         and (abs(note_signal_max - signal.max()) <= 0.01))):
                    note_active = {
                        "position": selected_position,
                        "start_time": current_time,
                    }
                    note_last_time = current_time
                    note_signal_max = signal.max()
                    save_note_to_file(note_active)
                    update_last_three_notes(selected_position)
                    print(f"Pitch: {pitch:.2f} Hz, Tablature: {selected_position}, Signal Max: {signal.max()}")

except KeyboardInterrupt:
    print("\n*** Stopping recording ***")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
