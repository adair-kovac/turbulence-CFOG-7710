import CFOG_Q1 as cq
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from data import data_loader
from calculations.scripts.calculations_from_intermediates import load_datasets, get_start_time
from calculations.scripts.plots import PlotVariables, plot_variable
from utils import path_util


def main(test=True):
    intermediate_dir = path_util.get_project_root() / "data" / "intermediate"
    output_dir = path_util.get_project_root() / "calculations" / "calc_from_intermediate" / "dissipation"
    if test:
        intermediate_dir = intermediate_dir / "test"
        output_dir = output_dir / "test"
    levels = [2, 5, 10]
    datasets = dict()
    for level in levels:
        input_dir = intermediate_dir / str(level)
        datasets[level] = load_datasets(input_dir)

    dissipation_rates = dict()
    for level in levels:
        dissipation_rates[level] = calculate_dissipation_rate(datasets, level)
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_dissipation_rate(dissipation_rates, output_dir)


def calculate_dissipation_rate(datasets, level):
    u_prime_2 = datasets[2]["u_prime"]["u_prime"]
    u_prime_5 = datasets[5]["u_prime"]["u_prime"]
    u_prime_10 = datasets[10]["u_prime"]["u_prime"]
    v_prime_2 = datasets[2]["v_prime"]["v_prime"]
    v_prime_5 = datasets[5]["v_prime"]["v_prime"]
    v_prime_10 = datasets[10]["v_prime"]["v_prime"]
    rate = cq.dissipation_rate(u_prime_2, u_prime_5, u_prime_10, v_prime_2, v_prime_5, v_prime_10, level)
    df = pd.DataFrame()
    df["time"] = datasets[2]["u_prime"]["time"] - datetime.timedelta(days=366)
    df["dissipation_rate"] = rate
    return df

def plot_dissipation_rate(dissipation_rates, output_dir):
    print("making plot")
    args = PlotVariables(
        column="dissipation_rate",
        plot_title="Dissipation Rate",
        y_label="Dissipation Rate (W/kg)",
        output_path=output_dir / "dissipation_rate.png"
    )
    plot_variable(dissipation_rates, args)
    args.output_path = output_dir / "dissipation_rate_fog_events.png"
    plot_variable_for_fog_events(dissipation_rates, args)


def plot_variable_for_fog_events(data_at_levels: dict, vars: PlotVariables):
    fig, ax = plt.subplots()
    for level, data in data_at_levels.items():
        data = data[(pd.Timestamp('2018-09-13 21:00:00') <= data.time) & (data.time <= pd.Timestamp('2018-09-14 06:30:00'))]
        plt.plot(data, data[vars.column], label=level)
    plt.legend()
    # ax.set_xlabel("Time Interval Start")
    ax.set_ylabel(vars.y_label)

    formation, dissipation = get_formation_and_dissipation_timestamps()
    for line in formation:
        plt.axvline(line, color="red")
    for line in dissipation:
        plt.axvline(line, color="green")

    plt.xlim(pd.Timestamp('2018-09-13 21:00:00'), pd.Timestamp('2018-09-14 06:30:00'))
    ax.xaxis.set_major_locator(plt.MaxNLocator(5))
    plt.title(vars.plot_title)
    plt.savefig(vars.output_path)
    plt.close()

def get_formation_and_dissipation_timestamps():
    vis = data_loader.load_raw_visibility_data()

    formation = []
    dissipation = []

    threshold = 1000
    last = 10000000
    for i, row in vis.iterrows():
        current = row["vis_10_min"]
        if last < threshold and current >= threshold:
            dissipation.append(row["time"])
        if last >= threshold and current < threshold:
            formation.append(row["time"])
        last = current
    return formation, dissipation

if __name__=="__main__":
    main(test=False)