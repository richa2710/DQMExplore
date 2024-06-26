import plotly.graph_objects as go
import numpy as np
import pandas as pd
from dqmexplore.dataproc import generate_me_dict, trig_normalize
from dqmexplore.exploreutils import check_empty_lss


def compute_trends(data, trigger_rates=None):
    def compute_avg(histbins, x_bins):
        weighted_sums = np.sum(histbins * x_bins, axis=1)
        sum_of_weights = np.sum(histbins, axis=1)
        x_avg = np.nan_to_num(weighted_sums / sum_of_weights, nan=0)
        return x_avg

    def compute_std(histbins, x_bins, x_avg):
        sqrd_devs = np.sum(histbins * (x_bins - x_avg[:, np.newaxis]) ** 2, axis=1)
        sum_of_weights = np.sum(histbins, axis=1)
        variance = np.nan_to_num(sqrd_devs / sum_of_weights, nan=0)
        std_dev = np.sqrt(variance)
        return std_dev

    if isinstance(data, pd.DataFrame):
        data = generate_me_dict(data)

    if trigger_rates is not None:
        data = trig_normalize(data, trigger_rates)

    empty_lss = check_empty_lss(data, thrshld=0)

    trends = {}

    for me in data.keys():
        trends[me] = {}
        histbins = data[me]["data"]
        x_bins = data[me]["x_bins"]
        trends[me]["mean"] = compute_avg(histbins, x_bins)  # e.g. mean charge
        trends[me]["stdev"] = compute_std(
            histbins, x_bins, trends[me]["mean"]
        )  # e.g. std of charge
        trends[me]["max"] = x_bins[np.argmax(histbins, axis=1)]  # e.g. max charge
        trends[me]["std_err_on_mean"] = trends[me]["stdev"] / np.sqrt(
            data[me]["data"].shape[1]
        )
        trends[me]["empty_lss"] = np.array(empty_lss[me]["empty_lss"])

    return trends


def plot_trends(
    trends,
    me,
    to_plot=["mean", "stdev", "max"],
    fig_titles=[],
    ylabels=[],
    norm=False,
    log=False,
    show=False,
):
    to_plot = np.array(to_plot)

    if norm:
        for trend in to_plot:
            trends[me][trend] = trends[me][trend] / np.sum(trends[me][trend])

    fig = go.Figure()

    buttons = []
    for i, stat in enumerate(trends[me].keys()):
        if stat in to_plot:
            fig_title = stat if len(fig_titles) == 0 else fig_titles[i]
            ylabel = "YAXIS" if len(ylabels) == 0 else ylabels[i]
            if i == 0:
                visible = True
                fig.update_layout(title=fig_title)
                fig.update_layout(yaxis={"title": ylabel})
            else:
                visible = False
            trace = go.Scatter()
            trace.y = trends[me][stat]
            trace.x = np.arange(len(trends[me][stat])) + 1
            trace.mode = "lines+markers"
            trace.visible = visible
            fig.add_trace(trace)

            buttons.append(
                dict(
                    args=[
                        {"visible": to_plot == stat},
                        {
                            "title": fig_title,
                            "yaxis": {
                                "title": ylabel,
                                "type": "log" if log else "linear",
                            },
                        },
                    ],
                    label=stat,
                    method="update",
                ),
            )

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=(buttons),
                direction="down",
            ),
        ],
        xaxis_title="LS",
        yaxis_type="log" if log else "linear",
    )

    if show:
        fig.show()
    else:
        return fig
