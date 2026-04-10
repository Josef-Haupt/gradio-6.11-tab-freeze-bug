import base64
import multiprocessing
import os
import sys
import warnings

import gradio as gr
import webview

import settings

warnings.filterwarnings("ignore")

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
_WINDOW = None
_URL = ""
_HEART_LOGO = "data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjE2IiB2aWV3Qm94PSIwIDAgMTYgMTYiIHZlcnNpb249IjEuMSIgd2lkdGg9IjE2IiBkYXRhLXZpZXctY29tcG9uZW50PSJ0cnVlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPg0KICAgIDxwYXRoIGQ9Im04IDE0LjI1LjM0NS42NjZhLjc1Ljc1IDAgMCAxLS42OSAwbC0uMDA4LS4wMDQtLjAxOC0uMDFhNy4xNTIgNy4xNTIgMCAwIDEtLjMxLS4xNyAyMi4wNTUgMjIuMDU1IDAgMCAxLTMuNDM0LTIuNDE0QzIuMDQ1IDEwLjczMSAwIDguMzUgMCA1LjUgMCAyLjgzNiAyLjA4NiAxIDQuMjUgMSA1Ljc5NyAxIDcuMTUzIDEuODAyIDggMy4wMiA4Ljg0NyAxLjgwMiAxMC4yMDMgMSAxMS43NSAxIDEzLjkxNCAxIDE2IDIuODM2IDE2IDUuNWMwIDIuODUtMi4wNDUgNS4yMzEtMy44ODUgNi44MThhMjIuMDY2IDIyLjA2NiAwIDAgMS0zLjc0NCAyLjU4NGwtLjAxOC4wMS0uMDA2LjAwM2gtLjAwMlpNNC4yNSAyLjVjLTEuMzM2IDAtMi43NSAxLjE2NC0yLjc1IDMgMCAyLjE1IDEuNTggNC4xNDQgMy4zNjUgNS42ODJBMjAuNTggMjAuNTggMCAwIDAgOCAxMy4zOTNhMjAuNTggMjAuNTggMCAwIDAgMy4xMzUtMi4yMTFDMTIuOTIgOS42NDQgMTQuNSA3LjY1IDE0LjUgNS41YzAtMS44MzYtMS40MTQtMy0yLjc1LTMtMS4zNzMgMC0yLjYwOS45ODYtMy4wMjkgMi40NTZhLjc0OS43NDkgMCAwIDEtMS40NDIgMEM2Ljg1OSAzLjQ4NiA1LjYyMyAyLjUgNC4yNSAyLjVaIj48L3BhdGg+DQo8L3N2Zz4="  # noqa: E501


def img2base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def gui_runtime_error_handler(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            raise gr.Error(message=str(e), duration=None) from e

    return wrapper


def select_folder():
    if sys.platform == "win32":
        from tkinter import Tk, filedialog

        tk = Tk()
        tk.withdraw()
        folder_selected = filedialog.askdirectory()
        tk.destroy()
    else:
        dirname = _WINDOW.create_file_dialog(webview.FileDialog.FOLDER)
        folder_selected = dirname[0] if dirname else None

    return folder_selected.replace("/", os.sep) if folder_selected else folder_selected


def set_window(window):
    global _WINDOW
    _WINDOW = window


def validate(value, msg):
    if not value:
        raise gr.Error(msg)


def select_directory(collect_files=True, max_files=None):
    dir_name = select_folder()

    if collect_files:
        if not dir_name:
            return None, None
        return dir_name, []

    return dir_name or None


def save_file_dialog(filetypes=(), default_filename=""):
    file = _WINDOW.create_file_dialog(
        webview.FileDialog.SAVE,
        file_types=filetypes,
        save_filename=default_filename,
    )

    if file:
        file = file[0] if isinstance(file, (list, tuple)) else file
        return str(file)

    return None


def build_header(logo="assets/img/birdnet_logo.png"):
    with gr.Row():
        gr.Markdown(
            f"""
<div style='display: flex; align-items: center;'>
    <img src='data:image/png;base64,{img2base64(os.path.join(SCRIPT_DIR, logo))}'
        style='width: 50px; height: 50px; margin-right: 10px;'>
    <h2>BirdNET Analyzer</h2>
</div>
            """
        )


def build_footer():
    with gr.Row():
        gr.Markdown(
            f"""
<div style='display: flex; justify-content: space-around; align-items: center; padding: 10px; text-align: center'>
    <div>
        <div style="display: flex;flex-direction: row;">GUI version:&nbsp<span
                id="current-version">main</span></div>
        <div>Model version: 2.4</div>
    </div>
    <div>K. Lisa Yang Center for Conservation Bioacoustics<br>Chemnitz University of Technology</div>
    <div>Help:&nbsp;<a href='https://birdnet.cornell.edu/analyzer'
            target='_blank'>birdnet.cornell.edu/analyzer</a>
            <br><img id='heart' src='{_HEART_LOGO}'>Support: <a href='https://birdnet.cornell.edu/donate' target='_blank'>birdnet.cornell.edu/donate</a>
    </div>

</div>"""  # noqa: E501
        )


def build_settings():
    with gr.Tab("Settings") as settings_tab:
        with gr.Group():
            with gr.Row():
                theme_radio = gr.Radio(
                    [
                        ("Dark", "dark"),
                        ("Light", "light"),
                    ],
                    value=lambda: settings.theme(),
                    label="Theme",
                    info="⚠️Theme info",
                    interactive=True,
                    scale=10,
                )

        def on_theme_change(value):
            if settings.theme() != value:
                _WINDOW.load_url(_URL.rstrip("/") + f"?__theme={value}")

        theme_radio.input(on_theme_change, inputs=theme_radio, show_progress="hidden")


def plot_map_scatter_mapbox(lat, lon, zoom=4):
    import plotly.express as px

    fig = px.scatter_map(
        lat=[lat], lon=[lon], zoom=zoom, map_style="open-street-map", size=[10]
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


def species_list_coordinates(show_map=False):
    with gr.Row(equal_height=True):
        with gr.Column(scale=1), gr.Group():
            lat_number = gr.Slider(
                minimum=-90,
                maximum=90,
                value=0,
                step=1,
                label="Latitude",
                info="Latitude info",
            )
            lon_number = gr.Slider(
                minimum=-180,
                maximum=180,
                value=0,
                step=1,
                label="Longitude",
                info="Longitude info",
            )

        map_plot = gr.Plot(
            plot_map_scatter_mapbox(0, 0), show_label=False, scale=2, visible=show_map
        )

        lat_number.change(
            plot_map_scatter_mapbox,
            inputs=[lat_number, lon_number],
            outputs=map_plot,
            show_progress="hidden",
        )
        lon_number.change(
            plot_map_scatter_mapbox,
            inputs=[lat_number, lon_number],
            outputs=map_plot,
            show_progress="hidden",
        )

    with gr.Group():
        with gr.Row():
            yearlong_checkbox = gr.Checkbox(
                True,
                label="Yearlong",
            )
            week_number = gr.Slider(
                minimum=1,
                maximum=48,
                value=1,
                step=1,
                interactive=False,
                label="Week",
                info="Week info",
            )

        sf_thresh_number = gr.Slider(
            minimum=0.01,
            maximum=0.99,
            value=0.03,
            step=0.01,
            label="Threshold",
            info="Threshold info",
        )

    def on_change(use_yearlong):
        return gr.Slider(interactive=(not use_yearlong))

    yearlong_checkbox.change(
        on_change, inputs=yearlong_checkbox, outputs=week_number, show_progress="hidden"
    )

    return (
        lat_number,
        lon_number,
        week_number,
        sf_thresh_number,
        yearlong_checkbox,
        map_plot,
    )


def locale():
    return gr.Dropdown(
        ["en"],
        value="en",
        label="Locale",
        info="Locale info",
    )


def bandpass_settings():
    with gr.Row():
        fmin_number = gr.Number(
            0,
            minimum=0,
            label="Minimum frequency (Hz)",
            info="Minimum frequency info",
        )
        fmax_number = gr.Number(
            15000,
            minimum=0,
            label="Maximum frequency (Hz)",
            info="Maximum frequency info",
        )
    return fmin_number, fmax_number


def computing_settings():
    with gr.Row():
        bs_number = gr.Number(
            precision=1,
            label="Batch size",
            value=1,
            info="Batch size info",
            minimum=1,
        )
        producers_number = gr.Number(
            precision=1,
            label="Producers",
            value=1,
            info="Producers info",
            minimum=1,
        )
        workers_number = gr.Number(
            precision=1,
            label="Workers",
            value=1,
            info="Workers info",
            minimum=1,
        )
    return bs_number, producers_number, workers_number


def _get_win_drives():
    from string import ascii_uppercase

    return [f"{drive}:\\" for drive in ascii_uppercase]


def _batched(iterable, n, *, strict=False):
    import itertools

    if n < 1:
        raise ValueError("n must be at least one")
    iterator = iter(iterable)
    while batch := tuple(itertools.islice(iterator, n)):
        if strict and len(batch) != n:
            raise ValueError("batched(): incomplete batch")
        yield batch


def open_window(builder):
    global _URL
    multiprocessing.freeze_support()

    with gr.Blocks(analytics_enabled=False) as demo:
        build_header()

        map_plots = []

        if callable(builder):
            map_plots.append(builder())
        elif isinstance(builder, (tuple, set, list)):
            map_plots.extend(build() for build in builder)

        build_settings()
        build_footer()

        map_plots = [plot for plot in map_plots if plot]

        if map_plots:
            inputs = []
            outputs = []
            for lat, lon, plot in map_plots:
                inputs.extend([lat, lon])
                outputs.append(plot)

            def update_plots(*args):
                return [
                    plot_map_scatter_mapbox(lat, lon)
                    for lat, lon in _batched(args, 2, strict=True)
                ]

            demo.load(update_plots, inputs=inputs, outputs=outputs)

    with (
        open(os.path.join(SCRIPT_DIR, "assets/gui.css")) as css_file,
        open(os.path.join(SCRIPT_DIR, "assets/gui.js")) as js_file,
    ):
        _URL = demo.queue(api_open=False).launch(
            css=css_file.read(),
            js=js_file.read(),
            theme=gr.themes.Default(),
            prevent_thread_lock=True,
            quiet=True,
            enable_monitoring=False,
            allowed_paths=_get_win_drives() if sys.platform == "win32" else ["/"],
            footer_links=[],
        )[1]

    webview.settings["ALLOW_DOWNLOADS"] = True
    _WINDOW = webview.create_window(
        "BirdNET-Analyzer",
        _URL.rstrip("/") + f"?__theme={settings.theme()}",
        width=1300,
        height=900,
        min_size=(1300, 900),
    )
    set_window(_WINDOW)

    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        from webview.platforms.winforms import BrowserView

        dwmapi = ctypes.windll.LoadLibrary("dwmapi")
        _WINDOW.events.loaded += lambda: dwmapi.DwmSetWindowAttribute(
            BrowserView.instances[_WINDOW.uid].Handle.ToInt32(),
            20,  # DWMWA_USE_IMMERSIVE_DARK_MODE
            ctypes.byref(ctypes.c_bool(settings.theme() == "dark")),
            ctypes.sizeof(wintypes.BOOL),
        )

    webview.start(private_mode=False, debug=True)
