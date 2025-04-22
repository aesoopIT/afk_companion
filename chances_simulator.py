import random
import time
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from scipy.signal import find_peaks

GUARANTEED_PULLS = sorted({60, 120, 180, 240, 300, 500, 580, 660, 740, 820, 1100, 1200, 1300, 1400, 1500})
MAX_GUARANTEED_CARDS = len(GUARANTEED_PULLS)
NUM_SIMULATIONS = 100000      # Number of simulations, change as needed
PULL_COST = 300

def simulate_single_hero(souls_needed):
    pulls = 0
    hero_souls = 0
    pity_counter = 0
    used_milestones = set()
    milestones = GUARANTEED_PULLS.copy()

    while hero_souls < souls_needed:
        pulls += 1
        pity_counter += 1

        got_hero = False

        # 2% Drop chance
        if random.random() < 0.02:
            got_hero = True

        # Pity-Hit 60 pull
        elif pity_counter >= 60:
            got_hero = True

        # Got a Hero: Pity reset
        if got_hero:
            hero_souls += 1
            pity_counter = 0

        # Bonus-Milestone check
        if pulls in milestones and pulls not in used_milestones:
            hero_souls += 1
            used_milestones.add(pulls)

    return pulls

def simulate_two_heroes(souls_hero1, souls_hero2):
    pulls = 0
    h1, h2 = 0, 0
    pity_counter = 0
    used_milestones = set()
    milestones = GUARANTEED_PULLS.copy()

    while h1 < souls_hero1 or h2 < souls_hero2:
        pulls += 1
        pity_counter += 1
        got_hero = False

        # 2% Drop chance
        if random.random() < 0.02:
            got_hero = True

        # Pity-Hit 60 pull
        elif pity_counter >= 60:
            got_hero = True

        # Got a Hero: Pity reset
        if got_hero:
            if h1 < souls_hero1:
                h1 += 1
            elif h2 < souls_hero2:
                h2 += 1
            pity_counter = 0

        # Bonus-Milestone check
        if pulls in milestones and pulls not in used_milestones:
            if h1 < souls_hero1:
                h1 += 1
            elif h2 < souls_hero2:
                h2 += 1
            used_milestones.add(pulls)

    return pulls

def get_top_spikes(pulls_results, num_spikes=3):
    counts, bins = np.histogram(pulls_results, bins=50)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    peaks, _ = find_peaks(counts, prominence=500)
    top_peaks = sorted(peaks, key=lambda p: counts[p], reverse=True)[:num_spikes]
    return [(int(bin_centers[p]), counts[p]) for p in top_peaks]

def print_top_spikes(spike_data, souls_needed):
    labels = ["Most likely", "Second most likely", "Third most likely"]
    data = [
        (labels[i], pulls, pulls * PULL_COST, souls_needed)
        for i, (pulls, _) in enumerate(spike_data)
    ]
    headers = ["Spike", "Pulls", "Diamond Cost", "Souls"]
    print(tabulate(data, headers=headers, tablefmt="grid", colalign=("left", "center", "center", "center")))

def plot_histogram_with_top3_spikes(pulls_results, spike_data):
    counts, bins = np.histogram(pulls_results, bins=50)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    max_height = max(counts)

    plt.figure(figsize=(10, 6))
    plt.bar(bin_centers, counts, width=(bins[1] - bins[0]), edgecolor='black', alpha=0.7)

    plt.ylim(top=max_height * 1.5)

    for i, (x, _) in enumerate(spike_data):
        label = f"Spike {i+1}: {x} Pulls"
        plt.axvline(x, linestyle='--', color='purple', linewidth=1, label=label)
        plt.text(x, max_height * 1.05, label, rotation=90, color='purple', ha='center')

    plt.title("Simulation Result Histogram (Top 3 Spikes)")
    plt.xlabel("Number of Pulls")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

def print_best_worst_case(pulls):
    best_case = min(pulls)
    worst_case = max(pulls)
    print(f"\nBest Case:\t {best_case} pulls → {best_case * PULL_COST} Diamonds")
    print(f"Worst Case:\t {worst_case} pulls → {worst_case * PULL_COST} Diamonds")


if __name__ == "__main__":
    mode = input("Simulate for 1 or 2 heroes? Enter 1 or 2: ").strip()

    if mode == "1":
        souls = int(input("Souls needed for the hero: "))
        print(f"\nRunning simulation for 1 hero ({souls} souls)...")
        start = time.time()
        pulls = [simulate_single_hero(souls) for _ in range(NUM_SIMULATIONS)]
        print(f"Done after {time.time() - start:.2f} seconds.\n")

        spike_data = get_top_spikes(pulls)
        print_top_spikes(spike_data, souls)
        plot_histogram_with_top3_spikes(pulls, spike_data)
        print_best_worst_case(pulls)

    elif mode == "2":
        s1 = int(input("Souls needed for Hero 1: "))
        s2 = int(input("Souls needed for Hero 2: "))
        total = s1 + s2
        print(f"\nRunning simulation for 2 heroes ({total} souls total)...")
        start = time.time()
        pulls = [simulate_two_heroes(s1, s2) for _ in range(NUM_SIMULATIONS)]
        print(f"Done after {time.time() - start:.2f} sec.\n")

        spike_data = get_top_spikes(pulls)
        print_top_spikes(spike_data, total)
        plot_histogram_with_top3_spikes(pulls, spike_data)
        print_best_worst_case(pulls)

    else:
        print("Invalid input. Please enter '1' or '2'.")