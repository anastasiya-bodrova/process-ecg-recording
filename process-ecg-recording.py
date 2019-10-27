import argparse
import jinja2
import pdfkit
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime, timedelta
from statistics import mean


parser = argparse.ArgumentParser(description="Report from 24h ECG")
parser.add_argument(
    "--start",
    required=True,
    type=lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
    help="start of the ECG recording in yyyy-mm-dd hh:mm:ss format",
)
parser.add_argument(
    "--record", required=True, type=str, help="file with ECG recording in CSV format"
)
parser.add_argument(
    "--pdf", action="store_true", default=False, help="output report in a pdf-file"
)
args = parser.parse_args()

# Constants
HOURS = 24
MS_IN_M = 60000

START_TIME = args.start
RECORD_FILE = args.record
PDF_OUTPUT = args.pdf

# Read data
with open(RECORD_FILE) as f:
    data = []
    for line in f:
        data.append(line.strip().split(",", 3))

ECG_records = pd.DataFrame(
    data, columns=["wave_type", "wave_onset", "wave_offset", "tags"]
)

# Count p-wave and qrs-complex ith "premature" tags
p_wave_premature = len(
    ECG_records[
        (ECG_records.wave_type == "P") & (
            ECG_records.tags.str.contains("premature"))
    ]
)
qrs_complex_premature = len(
    ECG_records[
        (ECG_records.wave_type == "QRS") & (
            ECG_records.tags.str.contains("premature"))
    ]
)


# count min, max, mean heart rate
onset_time = [int(x)
              for x in ECG_records[ECG_records.wave_type == "QRS"]["wave_onset"]]

max_heart_rate = 0
min_heart_rate = 1000
max_heart_rate_time = 0
min_heart_rate_time = 0

n_minute = 1
n_qrs_per_min = 0
heart_rates_per_minute = []
for ms_time in onset_time:
    if ms_time >= n_minute * MS_IN_M:
        n_minute += 1
        heart_rates_per_minute.append(n_qrs_per_min)
        datetime = (START_TIME + timedelta(milliseconds=ms_time)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if n_qrs_per_min > max_heart_rate:
            max_heart_rate = n_qrs_per_min
            max_heart_rate_time = datetime
        elif n_qrs_per_min < min_heart_rate:
            min_heart_rate = n_qrs_per_min
            min_heart_rate_time = datetime

        n_qrs_per_min = 0
    n_qrs_per_min += 1

mean_heart_rate_per_hour = []
min_heart_rate_per_hour = []
max_heart_rate_per_hour = []

for h in range(HOURS):
    heart_rates_per_hour = heart_rates_per_minute[h * 60: (h + 1) * 60]
    mean_heart_rate_per_hour.append(mean(heart_rates_per_hour))
    min_heart_rate_per_hour.append(min(heart_rates_per_hour))
    max_heart_rate_per_hour.append(max(heart_rates_per_hour))

mean_heart_rate = round(mean(mean_heart_rate_per_hour))
max_heart_rate = max(max_heart_rate_per_hour)
min_heart_rate = min(min_heart_rate_per_hour)

# plot
hours = [(START_TIME + timedelta(hours=h)).strftime("%H:%M")
         for h in range(HOURS + 1)]
hour_intervals = [f"{hours[i]} - {hours[i+1]}" for i in range(len(hours[:-1]))]

f = plt.figure()
plt.plot(mean_heart_rate_per_hour, color="r", marker="o")
plt.plot(max_heart_rate_per_hour, color="b", marker="o")
plt.plot(min_heart_rate_per_hour, color="g", marker="o")

plt.title(f"Heart rate mean, min, max per hour for 24h ECG from {START_TIME}")
plt.legend(["HR mean", "HR max", "HR min"])
plt.xticks(range(24), hour_intervals, rotation="vertical")
plt.yticks(range(40, 210, 10))
plt.ylabel("Heart rate (bpm)")
plt.xlabel("Hour interval")
plt.grid()

f.savefig("plot.png", bbox_inches="tight")

if PDF_OUTPUT:
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "template.html"
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(
        start_time=START_TIME,
        p_wave_premature=p_wave_premature,
        qrs_complex_premature=qrs_complex_premature,
        mean_heart_rate=mean_heart_rate,
        max_heart_rate=max_heart_rate,
        min_heart_rate=min_heart_rate,
        max_heart_rate_time=max_heart_rate_time,
        min_heart_rate_time=min_heart_rate_time,
        plot="plot.png",
    )

    html_file = open("report.html", "w")
    html_file.write(outputText)
    html_file.close()
    pdfkit.from_url("report.html", "report.pdf")
else:
    print("'Premature' tags amount:")
    print(f"P-wave: {p_wave_premature}")
    print(f"QRS-complex: {qrs_complex_premature}")
    print("\n")
    print("Heart rate:")
    print(f"Mean heart rate: {mean_heart_rate} bpm")
    print(f"Max heart rate: {max_heart_rate} bpm at {max_heart_rate_time}")
    print(f"Min heart rate: {min_heart_rate} bpm at {min_heart_rate_time}")
    plt.show()
