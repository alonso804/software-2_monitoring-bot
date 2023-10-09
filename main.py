from datetime import datetime
import glob
import json
from pprint import pprint
import gnuplotlib as gp
import numpy as np
import argparse
import re

COLORS = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKCYAN": "\033[96m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
}

LOGS_PATH = "logs/app.log"

MODULES_LOG_PATH = {
    "search-api": f"../search-api/{LOGS_PATH}",
    "poke-api": f"../poke-api/{LOGS_PATH}",
    "poke-stats": f"../poke-stats/{LOGS_PATH}",
    "poke-images": f"../poke-images/{LOGS_PATH}",
}

DATE_FORMATS = {"input": "%Y-%m-%d", "log": "%Y-%m-%dT%H:%M:%S.%fZ"}

GROUP_BY = {
    "month": "%Y-%m",
    "day": "%Y-%m-%d",
    "hour": "%Y-%m-%dT%H",
}


def check_latency(module_name, start_time, end_time, group_by, show=True):
    start_time = datetime.strptime(start_time, DATE_FORMATS["input"]).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_time = datetime.strptime(end_time, DATE_FORMATS["input"]).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

    log_file = glob.glob(MODULES_LOG_PATH[module_name])
    grouped_logs = {}

    with open(log_file[0], "r") as file:
        for line in file:
            log = json.loads(line)

            timestamp = datetime.strptime(log["timestamp"], DATE_FORMATS["log"])

            if start_time <= timestamp <= end_time and "time" in log:
                key = ""

                if group_by == "month":
                    key = timestamp.strftime(GROUP_BY[group_by])

                if group_by == "day":
                    key = timestamp.strftime(GROUP_BY[group_by])

                if group_by == "hour":
                    key = timestamp.strftime(GROUP_BY[group_by])

                if key not in grouped_logs:
                    grouped_logs[key] = {"count": 1, "time": log["time"]}
                else:
                    grouped_logs[key]["count"] += 1
                    grouped_logs[key]["time"] += log["time"]

    if show:
        for key in grouped_logs:
            print(
                COLORS["HEADER"] + f"- {key.replace('T', ' ')}: " + COLORS["ENDC"],
                end="",
            )
            print(f"{grouped_logs[key]['time'] / grouped_logs[key]['count']} ms")

    return grouped_logs


def check_availability(module_name, start_time, end_time, group_by, show=True):
    start_time = datetime.strptime(start_time, DATE_FORMATS["input"]).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_time = datetime.strptime(end_time, DATE_FORMATS["input"]).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

    log_file = glob.glob(MODULES_LOG_PATH[module_name])
    grouped_logs = {}

    with open(log_file[0], "r") as file:
        for line in file:
            log = json.loads(line)

            timestamp = datetime.strptime(log["timestamp"], DATE_FORMATS["log"])

            if start_time <= timestamp <= end_time and "status" in log:
                key = ""

                if group_by == "month":
                    key = timestamp.strftime(GROUP_BY[group_by])

                if group_by == "day":
                    key = timestamp.strftime(GROUP_BY[group_by])

                if group_by == "hour":
                    key = timestamp.strftime(GROUP_BY[group_by])

                if key not in grouped_logs:
                    grouped_logs[key] = {"success": 0, "error": 0}

                if log["status"] == 200:
                    grouped_logs[key]["success"] += 1
                else:
                    grouped_logs[key]["error"] += 1

    if show:
        for key in grouped_logs:
            print(
                COLORS["HEADER"] + f"- {key.replace('T', ' ')}: " + COLORS["ENDC"],
                end="",
            )
            print(
                f"{grouped_logs[key]['error'] / (grouped_logs[key]['success'] + grouped_logs[key]['error']) * 100}%"
            )

    return grouped_logs


def render_graph(module_name, start_time, end_time, group_by, action):
    if action == "availability":
        data = check_availability(module_name, start_time, end_time, group_by, False)

        xy = []

        for key in data:
            xy.append(
                {
                    "timestamp": key,
                    "availability": data[key]["error"]
                    / (data[key]["success"] + data[key]["error"])
                    * 100,
                }
            )

        xy = sorted(xy, key=lambda k: k["timestamp"])

        legend = {}

        for i in range(len(xy)):
            legend[i] = xy[i]["timestamp"].replace("T", " ")

        x = np.array([i for i in range(len(xy))])
        y = np.array([y["availability"] for y in xy])

        print(COLORS["HEADER"], "Legend:", COLORS["ENDC"])
        for key, value in legend.items():
            print(COLORS["HEADER"], f"- [{key}]:", COLORS["ENDC"], end="")
            print(f"{value} - {y[key]}%")

        gp.plot(
            x,
            y,
            _with="lines",
            terminal="dumb 80,40",
            unset="grid",
            title="Availability",
            xlabel="Time",
            ylabel="Availability (%)",
        )

    if action == "latency":
        data = check_latency(module_name, start_time, end_time, group_by, False)

        xy = []

        for key in data:
            xy.append(
                {"timestamp": key, "latency": data[key]["time"] / data[key]["count"]}
            )

        xy = sorted(xy, key=lambda k: k["timestamp"])

        legend = {}

        for i in range(len(xy)):
            legend[i] = xy[i]["timestamp"].replace("T", " ")

        x = np.array([i for i in range(len(xy))])
        y = np.array([y["latency"] for y in xy])

        print(COLORS["HEADER"], "Legend:", COLORS["ENDC"])
        for key, value in legend.items():
            print(COLORS["HEADER"], f"- [{key}]:", COLORS["ENDC"], end="")
            print(f"{value} - {y[key]} ms")

        gp.plot(
            x,
            y,
            _with="lines",
            terminal="dumb 80,40",
            unset="grid",
            title="Latency",
            xlabel="Time",
            ylabel="Latency (ms)",
        )


if __name__ == "__main__":
    modules = [module for module in MODULES_LOG_PATH]
    group_by = [group_by for group_by in GROUP_BY]
    actions = ["availability", "latency", "graph-availability", "graph-latency"]

    parser = argparse.ArgumentParser(description="CLI for log analysis")

    parser.add_argument("-m", "--module", help=f"module name ({', '.join(modules)})")
    parser.add_argument("-st", "--start_time", help="start time (YYYY-MM-DD)")
    parser.add_argument("-et", "--end_time", help="end time (YYYY-MM-DD)")
    parser.add_argument("-gb", "--group_by", help=f"group by ({', '.join(group_by)})")
    parser.add_argument("-a", "--action", help=f"action ({', '.join(actions)})")

    args = parser.parse_args()

    if args.module not in modules:
        print(f"Invalid module name ({', '.join(modules)})")
        exit()

    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    if (
        re.fullmatch(date_regex, args.start_time) is None
        or re.fullmatch(date_regex, args.end_time) is None
    ):
        print("Invalid start or end time format (YYYY-MM-DD)")
        exit()

    if args.group_by not in group_by:
        print(f"Invalid group by ({', '.join(group_by)})")
        exit()

    if args.action not in actions:
        print(f"Invalid action ({', '.join(actions)})")
        exit()

    if args.action == "availability":
        print(COLORS["OKGREEN"] + "Availability" + COLORS["ENDC"])
        check_availability(args.module, args.start_time, args.end_time, args.group_by)

    if args.action == "latency":
        print(COLORS["WARNING"] + "Latency" + COLORS["ENDC"])
        check_latency(args.module, args.start_time, args.end_time, args.group_by)

    if args.action == "graph-availability":
        print(COLORS["OKBLUE"] + "Availability" + COLORS["ENDC"])
        render_graph(
            args.module, args.start_time, args.end_time, args.group_by, "availability"
        )

    if args.action == "graph-latency":
        print(COLORS["OKCYAN"] + "Latency" + COLORS["ENDC"])
        render_graph(
            args.module, args.start_time, args.end_time, args.group_by, "latency"
        )
