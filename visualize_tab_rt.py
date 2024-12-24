import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import os

plt.rcParams['font.family'] = 'monospace'

# File path
file_path = "output_tab.txt"

strings = ["E", "A", "D", "G", "B", "e"]
string_map = {s: i for i, s in enumerate(strings)}
tablature = {string: "" for string in strings}  # Store tablature as strings
max_notes = 25  # Maximum notes per string
curr_tab_length = 0  # Current length of tablature
note_spacing = "  "  # Space between notes
previous_note = None

# Initialize the plot
fig, (ax_fretboard, ax_tab) = plt.subplots(2, 1, figsize=(15, 7), gridspec_kw={'height_ratios': [2, 1]})

# Fretboard setup
ax_fretboard.set_xlim(0, 20)  # Frets
ax_fretboard.set_ylim(-1, 6)  # Strings (0 to 5)
ax_fretboard.set_xticks(range(21))
ax_fretboard.set_yticks(range(6))
ax_fretboard.set_yticklabels(strings)
ax_fretboard.set_title("Guitar Fretboard")
ax_fretboard.set_xlabel("Fret")
ax_fretboard.set_ylabel("String")

for i in range(6):  # Draw strings
    ax_fretboard.plot(range(21), [i] * 21, color="black", linewidth=1.5)

for fret in range(21):  # Draw frets
    ax_fretboard.axvline(x=fret, color="gray", linestyle="--", linewidth=1.5)

# Marker for current note
marker, = ax_fretboard.plot([], [], "ro", markersize=10)

# Tablature setup
ax_tab.set_xlim(0, max_notes)  # Number of notes visible
ax_tab.set_ylim(-1, 6)  # Strings
ax_tab.set_yticks(range(6))
ax_tab.set_yticklabels(strings)
ax_tab.set_title("Guitar Tablature")
ax_tab.set_xlabel("Notes")
ax_tab.set_xticks([])  # Remove x-ticks for cleaner display
ax_tab.grid(True)

# Text elements for tablature (one per string)
tab_lines = [ax_tab.text(1.5, i, "", fontsize=12, va="center", ha="left") for i in range(6)]


def format_note(note):
    return f"{note:^3}"  # Center-align within 3 spaces


# Function to read new notes from the file
def read_new_notes(file):
    global last_position
    current_size = os.stat(file_path).st_size
    notes = []

    if current_size > last_position:
        file.seek(last_position)
        lines = file.readlines()
        last_position = file.tell()
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) == 3:
                time_start, string, fret = parts
                notes.append({
                    "time_start": float(time_start),
                    "string": string,
                    "fret": int(fret)
                })
    return notes


tablature = {string: [] for string in strings}


# Function to update the plot
def update(frame):
    global last_position, active_note, curr_tab_length, previous_note
    new_notes = read_new_notes(file)

    # Update active note if there's a new one
    if new_notes:
        active_note = new_notes[-1]
    # Display the active note

    # if ((active_note and not previous_note) or
    #         (active_note and (active_note["fret"] != previous_note["fret"] or
    #                           active_note["string"] != previous_note["string"]))):
    if new_notes and active_note:
        previous_note = active_note
        fret = active_note["fret"]
        string = active_note["string"]
        string_mapped = string_map[string]

        # Update fretboard marker
        marker.set_data([fret], [string_mapped])
        curr_tab_length = max(len(tablature[string]), curr_tab_length)

        if curr_tab_length == max_notes:
            for s in strings:
                tablature[s].pop(0)  # Remove the oldest note
                curr_tab_length -= 1
        # Append note to the tablature
        if curr_tab_length < max_notes:
            tablature[string].append(str(fret))
            for s in strings:
                if s != string:
                    tablature[s].append(" ")

        # Update tablature visualization
        for i, string_name in enumerate(strings):
            notes = tablature[string_name]
            formatted_notes = [format_note(note) for note in notes]  # Apply formatting
            tab_lines[i].set_text(note_spacing.join(formatted_notes))
    return marker, *tab_lines


# Open the file and initialize the read position
with open(file_path, "r") as file:
    last_position = os.stat(file_path).st_size  # Start at the end of the file
    active_note = None  # Currently displayed note
    start_time = time.time()  # Record the start time

    # Animation
    ani = animation.FuncAnimation(fig, update, interval=100, blit=True)
    plt.tight_layout()
    plt.show()
