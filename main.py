from datetime import datetime
import glob
import json
from pprint import pprint
import gnuplotlib as gp
import numpy as np

LOGS_PATH = "logs/app.log"

MODULES = {
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

    log_file = glob.glob(MODULES[module_name])
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
                f"{key.replace('T', ' ')}: {grouped_logs[key]['time'] / grouped_logs[key]['count']} ms"
            )

    return grouped_logs


def check_availability(module_name, start_time, end_time, group_by, show=True):
    start_time = datetime.strptime(start_time, DATE_FORMATS["input"]).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_time = datetime.strptime(end_time, DATE_FORMATS["input"]).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

    log_file = glob.glob(MODULES[module_name])
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
                f"{key.replace('T', ' ')}: {grouped_logs[key]['error'] / (grouped_logs[key]['success'] + grouped_logs[key]['error']) * 100}%"
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

        print("Legend:")
        for key, value in legend.items():
            print(f"- [{key}]: {value}")

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

        print("Legend:")
        for key, value in legend.items():
            print(f"- [{key}]: {value}")

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


module = "search-api"
# module = "poke-api"
# module = "poke-stats"
# module = "poke-images"

check_availability(module, "2023-10-07", "2023-10-08", "hour")
print("-----")
check_latency(module, "2023-10-07", "2023-10-08", "hour")
print("-----")
render_graph(module, "2023-10-07", "2023-10-08", "hour", "latency")
