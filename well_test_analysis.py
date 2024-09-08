import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from matplotlib.widgets import Button


class Derivative:
    def __init__(self, filename, x, y):
        self.filename = filename
        self.data = pd.read_csv(self.filename)
        self.time = self.data["time"]
        self.pressure = self.data["pressure"]
        self.x = x
        self.y = y

    def dlt_P(self):
        return [self.pressure[i] - self.pressure[0] for i in range(len(self.pressure))]

    def drv_p(self):
        drvp = []
        line_point1s = []
        for i in range(len(self.pressure) - 2):
            dps = (
                self.time[i + 1]
                * ((self.pressure[i + 2]) - (self.pressure[i]))
                / ((self.time[i + 2]) - (self.time[i]))
            )
            drvp.append(dps)
            if self.pressure[i] == self.y[0]:
                line_point1s.append(dps)
            if self.pressure[i] == self.y[1]:
                line_point1s.append(dps)
        return drvp, line_point1s

    def plotss(self):
        drvp, line_point1s = self.drv_p()
        plt.figure(figsize=(6, 4))
        plt.loglog(self.time, self.dlt_P(), label="ΔP", marker="o", linestyle="")
        plt.loglog(
            self.time[:-2], drvp, label="d(ΔP)/d(log(t))", marker="x", linestyle=""
        )
        plt.axhline(y=line_point1s[0], color="r", linestyle="-")
        plt.xlabel("Time (hours)")
        plt.ylabel("Pressure Change (psi) and Derivatives")
        plt.title("Log-Log Plot of Pressure Change and Derivatives")
        plt.legend()
        plt.grid(True, which="both", ls="-")
        plt.show()


class Horner:
    def __init__(self, tp, filePath):
        self.filePath = filePath
        self.tp = tp
        self.df = pd.read_csv(self.filePath)
        self.validate_data()
        self.p = self.df["pressure"]
        self.t = self.df["time"]

    def validate_data(self):
        if not all(col in self.df.columns for col in ["pressure", "time"]):
            raise ValueError("CSV file must contain 'pressure' and 'time' columns")

    def horner_plot(self):
        return [(self.tp + t) / t for t in self.t if t != 0], self.p[1:]


class BuildUpCalculator(Horner):
    def __init__(self, tp, filePath, Qo, Bo, mo, Ø, Ct, rw, h):
        super().__init__(tp, filePath)
        self.Qo = Qo
        self.Bo = Bo
        self.mo = mo
        self.Ø = Ø
        self.Ct = Ct
        self.rw = rw
        self.h = h

    @property
    def Ph0(self):
        return self.p[0]

    def Ph1(self, slope, intercept):
        return intercept + (slope * np.log(self.tp + 1))

    def k(self, slope):
        return abs(162.6 * self.Qo * self.Bo * self.mo / (slope * self.h))

    def skin(self, intercept, slope, k):
        P1hr = self.Ph1(slope, intercept)
        return (
            1.151 * ((P1hr - self.Ph0) / slope)
            - np.log10(k / (self.Ø * self.mo * self.Ct * self.rw**2))
            + 3.23
        )


class InteractivePlot(BuildUpCalculator):
    def __init__(self, fig, ax, **kwargs):
        super().__init__(**kwargs)
        self.fig = fig
        self.ax = ax
        self.points = []
        self.horner_list, self.pressure_list = self.horner_plot()
        self.create_plot()
        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        axreset = plt.axes([0.8, 0.05, 0.1, 0.04])
        self.button = Button(axreset, "Reset")
        self.button.on_clicked(self.reset_plot)

    def create_plot(self):
        self.ax.clear()
        self.ax.set_title("Horner Plot")
        self.ax.set_xlabel("Horner Time Ratio (tp + t) / t")
        self.ax.set_ylabel("Pressure (psi)")
        self.ax.grid(True, which="both", linestyle="--")
        self.ax.semilogx(self.horner_list, self.pressure_list, "ko", ms=4)

    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        nearest_point = min(
            zip(self.horner_list, self.pressure_list),
            key=lambda p: (p[0] - event.xdata) ** 2 + (p[1] - event.ydata) ** 2,
        )
        self.points.append(nearest_point)
        self.ax.plot(*nearest_point, "rx")
        if len(self.points) == 2:
            x = np.log([p[0] for p in self.points])
            y = [p[1] for p in self.points]
            model = LinearRegression().fit(x.reshape(-1, 1), y)
            slope, intercept = model.coef_[0], model.intercept_
            self.ax.plot(
                self.horner_list, intercept + slope * np.log(self.horner_list), "b-"
            )
            plt.draw()
            self.display_results(slope, intercept)
            app = Derivative(self.filePath, y=y, x=self.points)
            app.plotss()

    def display_results(self, slope, intercept):
        k = self.k(slope)
        s = self.skin(intercept, abs(slope), k)
        textstr = f"Permeability (k): {k:.4f} mD\nSkin factor (s): {s:.4f}"
        self.ax.text(
            0.10,
            0.20,
            textstr,
            transform=self.ax.transAxes,
            fontsize=14,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

    def reset_plot(self, event):
        self.points = []
        self.create_plot()
        plt.draw()


if __name__ == "__main__":
    fig, ax = plt.subplots()
    interactive_plot = InteractivePlot(
        fig,
        ax,
        tp=15724.26,
        filePath=r"C:\Users\pc\Desktop\projects\oil_and_gas\project_build_up\worked_data.csv",
        Qo=542,
        Bo=2.5052,
        mo=0.108,
        Ø=0.031,
        Ct=3.91e-5,
        rw=0.245,
        h=787,
    )
    plt.show()
