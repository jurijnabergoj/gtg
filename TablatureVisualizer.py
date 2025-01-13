import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os

# Guitar constants
guitar_tuning = [82.41, 110.00, 146.83, 196.00, 246.94, 329.63]  # E2, A2, D3, G3, B3, E4
string_names = ["E", "A", "D", "G", "B", "e"]
MAX_MOVEMENT_COST = 8


class TablatureVisualizer:
    def __init__(self):
        plt.rcParams['font.family'] = 'monospace'
        self.strings = string_names
        self.string_map = {s: i for i, s in enumerate(self.strings)}
        self.max_notes = 22
        self.note_spacing = "  "
        self.max_visible_rows = 3
        self.full_tablature = []
        self.complete_tablature = []
        self.last_position = 0
        self.active_note = None
        self.running = True

        self.setup_plot()

    def setup_plot(self):
        self.fig, (self.ax_fretboard, self.ax_tab1, self.ax_tab2, self.ax_tab3) = plt.subplots(
            4, 1, figsize=(15, 7), gridspec_kw={'height_ratios': [1, 1, 1, 1]}
        )

        # Fretboard setup
        self.setup_fretboard()

        # Tablature setup
        self.ax_tabs = [self.ax_tab1, self.ax_tab2, self.ax_tab3]
        self.setup_tablature()

        # Create text elements for tablature
        self.tab_lines = [
            [ax.text(1.5, i, "", fontsize=12, va="center", ha="left")
             for i in range(6)] for ax in self.ax_tabs
        ]

        plt.tight_layout()

    def setup_fretboard(self):
        self.ax_fretboard.set_xlim(0, 20)
        self.ax_fretboard.set_ylim(-1, 6)
        self.ax_fretboard.set_xticks(range(21))
        self.ax_fretboard.set_yticks(range(6))
        self.ax_fretboard.set_yticklabels(self.strings)
        self.ax_fretboard.set_title("Guitar Fretboard")
        self.ax_fretboard.set_xlabel("Fret")
        self.ax_fretboard.set_ylabel("String")

        for i in range(6):
            self.ax_fretboard.plot(range(21), [i] * 21, color="black", linewidth=1.5)
        for fret in range(21):
            self.ax_fretboard.axvline(x=fret, color="gray", linestyle="--", linewidth=1.5)

        self.marker, = self.ax_fretboard.plot([], [], "ro", markersize=10)

    def setup_tablature(self):
        for ax_tab in self.ax_tabs:
            ax_tab.set_xlim(0, self.max_notes)
            ax_tab.set_ylim(-1, 6)
            ax_tab.set_yticks(range(6))
            ax_tab.set_yticklabels(self.strings)
            ax_tab.set_xticks([])
            ax_tab.grid(False)

        for j in range(self.max_visible_rows):
            for i in range(6):
                self.ax_tabs[j].plot(range(28), [i] * 28, color="black", linewidth=1.0)

    def format_note(self, note):
        return f"{note:^3}"

    def append_note_to_full_tablature(self, string, fret):
        if len(self.full_tablature) == 0 or len(self.full_tablature[-1][string]) >= self.max_notes:
            new_row = {s: [] for s in self.strings}
            self.full_tablature.append(new_row)
            self.complete_tablature.append({s: [] for s in self.strings})

        self.full_tablature[-1][string].append(fret)
        self.complete_tablature[-1][string].append(fret)
        for s in self.strings:
            if s != string:
                self.full_tablature[-1][s].append(" ")
                self.complete_tablature[-1][s].append(" ")

        if len(self.full_tablature) > self.max_visible_rows:
            self.full_tablature.pop(0)

    def read_new_notes(self):
        try:
            current_size = os.stat("output_tab.txt").st_size
            notes = []

            if current_size > self.last_position:
                with open("output_tab.txt", "r") as file:
                    file.seek(self.last_position)
                    lines = file.readlines()
                    self.last_position = file.tell()
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
        except FileNotFoundError:
            return []

    def update_plot(self, frame):
        if not self.running:
            plt.close()
            return self.marker, *[line for tab in self.tab_lines for line in tab]

        new_notes = self.read_new_notes()

        if new_notes:
            self.active_note = new_notes[-1]
            fret = self.active_note["fret"]
            string = self.active_note["string"]
            string_mapped = self.string_map[string]

            # Update fretboard marker
            self.marker.set_data([fret], [string_mapped])

            # Add note to tablature
            self.append_note_to_full_tablature(string, str(fret))

            # Update visible tablature
            visible_tablature = self.full_tablature[-self.max_visible_rows:]
            for row_idx, row in enumerate(visible_tablature):
                for i, string_name in enumerate(self.strings):
                    notes = row[string_name]
                    formatted_notes = [self.format_note(note) for note in notes]
                    self.tab_lines[row_idx][i].set_text(self.note_spacing.join(formatted_notes))

        return self.marker, *[line for tab in self.tab_lines for line in tab]

    def save_tablature_pdf(self, filename="final_tablature.pdf"):
        if not self.complete_tablature:
            return

        num_rows = len(self.complete_tablature)
        row_spacing = 0.5
        new_row_spacing = 1.0

        fig_full, ax_full = plt.subplots(figsize=(15, max(1, num_rows) * row_spacing + num_rows * new_row_spacing))
        ax_full.set_xlim(0, self.max_notes)
        ax_full.set_ylim(-1, num_rows * 6 * row_spacing + num_rows * new_row_spacing)
        ax_full.set_yticks([])
        ax_full.set_title("Guitar Tablature", fontsize=16)
        ax_full.set_xlabel("Notes")
        ax_full.set_xticks([])

        y_offset = 0
        for row in self.complete_tablature:
            y_offset += new_row_spacing
            for string_idx, string_name in enumerate(reversed(self.strings)):
                notes = row[string_name]
                formatted_notes = [self.format_note(note) for note in notes]
                ax_full.text(0, y_offset + string_idx * row_spacing,
                             self.note_spacing.join(formatted_notes),
                             fontsize=12, va="center", ha="left", family="monospace")
                ax_full.plot(range(self.max_notes),
                             [y_offset + string_idx * row_spacing] * self.max_notes,
                             color="black", linewidth=1.0)
            y_offset += 6 * row_spacing

        ax_full.invert_yaxis()

        with PdfPages(filename) as pdf:
            pdf.savefig(fig_full, bbox_inches="tight")
        plt.close(fig_full)

    def stop(self):
        self.running = False
