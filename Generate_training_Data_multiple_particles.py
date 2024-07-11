import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')


def generate_waveform(t):
    """
    Generates a waveform with two local minima and highest values at the edges, with random variation.
    """
    # Create a base waveform with two dips
    center1 = 2 + np.random.uniform(-0.5, 0.5)
    center2 = 4 + np.random.uniform(-0.5, 0.5)
    dip_width1 = 0.5 + np.random.uniform(-0.2, 0.2)
    dip_width2 = 0.5 + np.random.uniform(-0.2, 0.2)
    amplitude1 = 1.75e8 + np.random.uniform(-0.25e8, 0.25e8)
    amplitude2 = 1.75e8 + np.random.uniform(-0.25e8, 0.25e8)

    waveform = 2.75e8 - amplitude1 * np.exp(-((t - center1) ** 2) / (2 * dip_width1 ** 2)) - amplitude2 * np.exp(
        -((t - center2) ** 2) / (2 * dip_width2 ** 2))

    # Add some random noise
    noise = np.random.normal(0, 0.05e8, t.shape)
    waveform += noise

    return waveform


def plot_waveform(t, waveform, filename):
    """
    Plots the waveform and saves it to a file.
    """
    plt.figure()
    plt.plot(t, waveform, label="Weighted Uncovered Area")
    plt.xlabel("Time (s)")
    plt.ylabel("Weighted Uncovered Area")
    plt.title("Weighted Uncovered Area vs. Time")
    plt.legend()
    plt.savefig(filename)
    plt.close()


def main():
    # Time array
    t = np.linspace(0, 6, 1000)

    # Number of waveforms to generate
    num_waveforms = 3

    for i in range(num_waveforms):
        waveform = generate_waveform(t)
        filename = f"waveform_{i + 1}.png"
        plot_waveform(t, waveform, filename)
        print(f"Saved {filename}")


if __name__ == "__main__":
    main()