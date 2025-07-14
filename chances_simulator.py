import random
import time
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from scipy.signal import find_peaks
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

GUARANTEED_PULLS = sorted({60, 120, 180, 240, 300, 500, 580, 660, 740, 820, 1100, 1200, 1300, 1400, 1500})
PULL_COST = 300

# ================= Simulation Logic =================

def simulate_hero_pulls(souls_needed_list):
    pulls = 0
    pity_counter = 0
    used_milestones = set()
    souls = [0 for _ in souls_needed_list]

    def add_soul():
        for i in range(len(souls)):
            if souls[i] < souls_needed_list[i]:
                souls[i] += 1
                break

    # Continue pulling until all heroes have their required souls
    while any(s < needed for s, needed in zip(souls, souls_needed_list)):
        pulls += 1
        pity_counter += 1
        got_hero = False

        # 2% Drop Chance or 60 Pulls Pity
        if random.random() < 0.02 or pity_counter >= 60:
            got_hero = True

        # Got a hero: assign soul and reset pity
        if got_hero:
            add_soul()
            pity_counter = 0

        # Bonus-Milestone: extra soul at predefined pull intervals
        if pulls in GUARANTEED_PULLS and pulls not in used_milestones:
            add_soul()
            used_milestones.add(pulls)

    return pulls

def simulate_fixed_pulls(num_pulls):
    pity_counter = 0
    used_milestones = set()
    souls = 0

    for pull in range(1, num_pulls + 1):
        pity_counter += 1
        got_hero = False

        if random.random() < 0.02 or pity_counter >= 60:
            got_hero = True

        if got_hero:
            souls += 1
            pity_counter = 0

        if pull in GUARANTEED_PULLS and pull not in used_milestones:
            souls += 1
            used_milestones.add(pull)

    return souls

# ================= Utility Wrappers =================

def simulate_fixed_pulls_wrapper(pulls_possible):
    return simulate_fixed_pulls(pulls_possible)

def simulate_single_run(args):
    return simulate_hero_pulls(args)

# ================= Statistics & Plotting =================

def get_top_spikes(pulls_results, num_spikes=3):
    counts, bins = np.histogram(pulls_results, bins=50)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    peaks, _ = find_peaks(counts, prominence=250)
    top_peaks = sorted(peaks, key=lambda p: counts[p], reverse=True)[:num_spikes]
    return [(int(bin_centers[p]), counts[p]) for p in top_peaks] if top_peaks else []

def print_top_spikes(spike_data, souls_needed):
    labels = ["Most likely", "Second most likely", "Third most likely"]
    data = [
        (labels[i], pulls, pulls * PULL_COST, souls_needed)
        for i, (pulls, _) in enumerate(spike_data[:len(labels)])
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

# ================= Input Handling =================

def get_valid_input(prompt, default, min_value=1):
    try:
        value = int(input(prompt).strip())
        if value < min_value:
            print(f"Value too small. Using minimum value of {min_value}.")
            return min_value
        return value
    except ValueError:
        print(f"Invalid input. Using default value of {default}.")
        return default

# ================= Simulation Modes =================

def run_target_souls_simulation():
    NUM_SIMULATIONS = get_valid_input(
        "\nPlease type the Number of Simulations (Default: 10000): ",10000, 10000)

    hero_mode = input("\nSimulation for 1 or 2 Heroes?\nEnter 1 or 2: ").strip()
    if hero_mode == "1":
        souls = get_valid_input("Souls needed for Hero (14 = Ascended, 24 = Ascended 5*): ", 14)
        args = [[souls]] * NUM_SIMULATIONS
        title = f"Simulation for 1 Hero ({souls} Souls)"
    elif hero_mode == "2":
        s1 = get_valid_input("Souls needed for Hero 1 (14 = Ascended, 24 = Ascended 5*): ", 14)
        s2 = get_valid_input("Souls needed for Hero 2 (14 = Ascended, 24 = Ascended 5*): ", 14)
        souls = s1 + s2
        args = [[s1, s2]] * NUM_SIMULATIONS
        title = f"Simulation for 2 Heroes ({souls} Souls total)"
    else:
        print("Invalid input. Please enter '1' or '2'.")
        return

    print(f"\n{title} is executed...")
    start = time.time()
    with Pool(cpu_count()) as pool:
        pulls = list(tqdm(pool.imap_unordered(simulate_single_run, args), total=NUM_SIMULATIONS, desc="Simulating"))
    print(f"Done in {time.time() - start:.2f} Seconds.\n")

    spike_data = get_top_spikes(pulls)
    print_top_spikes(spike_data, souls)
    plot_histogram_with_top3_spikes(pulls, spike_data)
    print_best_worst_case(pulls)

def run_fixed_pulls_simulation():
    divine_scrolls = get_valid_input("How many Destiny Scrolls do you have: ", 0, 0)
    diamonds = get_valid_input("How many diamonds do you have: ", 0, 0)
    pulls_possible = divine_scrolls + diamonds // PULL_COST
    print(f"\nYou can do {pulls_possible} pulls (Scrolls: {divine_scrolls}, Diamonds: {diamonds})")

    NUM_SIMULATIONS = get_valid_input(
        "\nPlease type the Number of Simulations (Default: 10000): ",10000, 1000)

    print(f"\nSimulating {NUM_SIMULATIONS} runs with {pulls_possible} pulls each...")
    start = time.time()
    with Pool(cpu_count()) as pool:
        results = list(tqdm(pool.imap_unordered(simulate_fixed_pulls_wrapper, [pulls_possible] * NUM_SIMULATIONS),
                            total=NUM_SIMULATIONS, desc="Simulating"))

    mean_souls = np.mean(results)
    min_souls = min(results)
    max_souls = max(results)
    print(f"\nResults for Souls obtained in {pulls_possible} pulls:")
    print(f"  Avg Souls: {mean_souls:.2f}")
    print(f"  Min Souls: {min_souls}")
    print(f"  Max Souls: {max_souls}")

    plt.hist(results, bins=range(0, max_souls+2), alpha=0.7, edgecolor='black')
    plt.title("Distribution of Dimensional Souls")
    plt.xlabel("Souls Obtained")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.savefig("example_pulls.png")
    plt.show()

    print(f"\nSimulation completed in {time.time() - start:.2f} Seconds.\n")

# ================= Entry Point =================

if __name__ == "__main__":
    print("Choose Simulation Mode:")
    print("1 - Simulate pulls needed for specific souls (Target Souls Mode)")
    print("2 - Simulate souls gained from fixed pulls (Fixed Pull Mode)")
    mode = input("Enter 1 or 2: ").strip()

    if mode == "1":
        run_target_souls_simulation()
    elif mode == "2":
        run_fixed_pulls_simulation()
    else:
        print("Invalid input. Please enter '1' or '2'.")
