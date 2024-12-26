import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from AudioProcessor import AudioProcessor
from TablatureVisualizer import TablatureVisualizer

# Standard tuning for a 6-string guitar (frequencies in Hz)
guitar_tuning = [82.41, 110.00, 146.83, 196.00, 246.94, 329.63]  # E2, A2, D3, G3, B3, E4
string_names = ["E", "A", "D", "G", "B", "e"]
MAX_MOVEMENT_COST = 8


def main():
    # Create the audio processor
    audio_processor = AudioProcessor()

    # Create the visualizer
    visualizer = TablatureVisualizer()

    # Start audio processing in a separate thread
    audio_thread = threading.Thread(target=audio_processor.start_recording, args=(20,))
    audio_thread.start()

    try:
        # Run visualization in the main thread
        ani = animation.FuncAnimation(
            visualizer.fig,
            visualizer.update_plot,
            interval=100,
            blit=True
        )
        plt.show()

    except KeyboardInterrupt:
        print("\nStopping recording and visualization...")
    finally:
        visualizer.stop()
        audio_processor.cleanup()
        visualizer.save_tablature_pdf()


if __name__ == "__main__":
    main()
