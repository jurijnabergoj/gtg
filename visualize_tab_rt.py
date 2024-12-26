import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_pdf import PdfPages
import time
import os

plt.rcParams['font.family'] = 'monospace'

# File path
file_path = "output_tab.txt"

strings = ["E", "A", "D", "G", "B", "e"]
string_map = {s: i for i, s in enumerate(strings)}

tablature = {string: [] for string in strings}

max_notes = 25  # Maximum notes per string
curr_tab_length = 0  # Current length of tablature
note_spacing = "  "  # Space between notes
previous_note = None
max_visible_rows = 3

full_tablature = []
complete_tablature = []
fig, (ax_fretboard, ax_tab1, ax_tab2, ax_tab3) = plt.subplots(4, 1, figsize=(15, 7),
                                                              gridspec_kw={'height_ratios': [1, 1, 1, 1]})

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

ax_tabs = [ax_tab1, ax_tab2, ax_tab3]

# Tablature setup
for ax_tab in ax_tabs:
    ax_tab.set_xlim(0, max_notes)
    ax_tab.set_ylim(-1, 6)

    ax_tab.set_yticks(range(6))
    ax_tab.set_yticklabels(strings)
    ax_tab.set_xticks([])
    ax_tab.grid(False)

for j in range(max_visible_rows):
    for i in range(6):  # Draw strings
        ax_tabs[j].plot(range(28), [i] * 28, color="black", linewidth=1.0)

# Text elements for tablature (one per string)
tab_lines1 = [ax_tab1.text(1.5, i, "", fontsize=12, va="center", ha="left") for i in range(6)]
tab_lines2 = [ax_tab2.text(1.5, i, "", fontsize=12, va="center", ha="left") for i in range(6)]
tab_lines3 = [ax_tab3.text(1.5, i, "", fontsize=12, va="center", ha="left") for i in range(6)]

tab_lines = [tab_lines1, tab_lines2, tab_lines3]


def format_note(note):
    return f"{note:^3}"  # Center-align within 3 spaces


def append_note_to_full_tablature(string, fret):
    global full_tablature, complete_tablature

    # Ensure each string has a row in full tablature
    if len(full_tablature) == 0 or len(full_tablature[-1][string]) >= max_notes:
        full_tablature.append({s: [] for s in strings})  # Create a new row
        complete_tablature.append({s: [] for s in strings})  # Create a new row

    # Add the note to the latest row
    full_tablature[-1][string].append(fret)
    complete_tablature[-1][string].append(fret)
    for s in strings:
        if s != string:
            full_tablature[-1][s].append(" ")
            complete_tablature[-1][s].append(" ")

    # If rows exceed max visible rows, simulate scrolling by removing the oldest visible row
    if len(full_tablature) > max_visible_rows:
        full_tablature.pop(0)


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


# Save the full tablature periodically
def save_full_tablature(filename="full_tablature.txt"):
    with open(filename, "w") as f:
        for row in full_tablature:
            for string_name in strings:
                f.write(f"{string_name}: {''.join(row[string_name])}\n")
            f.write("\n")


def save_full_tablature_pdf(filename="full_tablature.pdf"):
    """
    Save the full tablature as a PDF.
    """
    num_rows = len(complete_tablature)
    row_spacing = 0.5  # Vertical spacing between strings within a row
    new_row_spacing = 1.0  # Extra vertical space between new tablature rows

    fig_full, ax_full = plt.subplots(
        figsize=(15, num_rows * row_spacing + num_rows * new_row_spacing))

    # Set up the full tablature axis
    ax_full.set_xlim(0, max_notes)
    ax_full.set_ylim(-1, num_rows * 6 * row_spacing + num_rows * new_row_spacing)
    ax_full.set_yticks([])
    # ax_full.set_yticklabels(strings)
    ax_full.set_title("Guitar Tablature", fontsize=16)
    ax_full.set_xlabel("Notes")
    ax_full.set_xticks([])

    # Draw the full tablature
    y_offset = 0
    for row_idx, row in enumerate(complete_tablature):
        y_offset += new_row_spacing
        for string_idx, string_name in enumerate(reversed(strings)):
            notes = row[string_name]
            formatted_notes = [format_note(note) for note in notes]
            ax_full.text(0, y_offset + string_idx * row_spacing, note_spacing.join(formatted_notes),
                         fontsize=12, va="center", ha="left", family="monospace")
            ax_full.plot(range(max_notes), [y_offset + string_idx * row_spacing] * max_notes,
                         color="black", linewidth=1.0)
        y_offset += 6 * row_spacing  # Move to the next tablature row

    ax_full.invert_yaxis()  # Match tablature style (high e-string at the top)
    plt.tight_layout()

    # Save the full tablature to a PDF
    with PdfPages(filename) as pdf:
        pdf.savefig(fig_full, bbox_inches="tight")
    plt.close(fig_full)  # Close the figure to free memory


# Function to update the plot
def update(frame):
    global last_position, active_note, curr_tab_length, previous_note
    new_notes = read_new_notes(file)

    if new_notes:
        active_note = new_notes[-1]

    if new_notes and active_note:
        previous_note = active_note
        fret = active_note["fret"]
        string = active_note["string"]
        string_mapped = string_map[string]

        # Update fretboard marker
        marker.set_data([fret], [string_mapped])
        curr_tab_length = max(len(tablature[string]), curr_tab_length)

        # Add note to full tablature
        append_note_to_full_tablature(string, str(fret))

        visible_tablature = full_tablature[-max_visible_rows:]
        for row_idx, row in enumerate(visible_tablature):
            for i, string_name in enumerate(strings):
                notes = row[string_name]
                formatted_notes = [format_note(note) for note in notes]
                tab_lines[row_idx][i].set_text(note_spacing.join(formatted_notes))

    return marker, *[line for tab in tab_lines for line in tab]


# Open the file and initialize the read position
with open(file_path, "r") as file:
    last_position = os.stat(file_path).st_size  # Start at the end of the file
    active_note = None  # Currently displayed note
    start_time = time.time()  # Record the start time

    # Animation
    ani = animation.FuncAnimation(fig, update, interval=100, blit=True)
    # Periodically save the full tablature
    plt.tight_layout()
    try:
        plt.show()
    finally:
        save_full_tablature()  # Save when closing
        save_full_tablature_pdf("final_full_tablature.pdf")
