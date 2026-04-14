import base64
import multiprocessing
import os
import platform
import sys
import warnings
from pathlib import Path

import gradio as gr
import webview

import settings

warnings.filterwarnings("ignore")

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
_WINDOW = None
_URL = ""

_CUSTOM_SPECIES = "Custom species list"
_PREDICT_SPECIES = "Predicted species list"
_CUSTOM_CLASSIFIER = "Custom classifier"
_ALL_SPECIES = "All species"
_USE_PERCH = "Perch v2"
_USE_BIRDNET_2_4 = "BirdNET 2.4"
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


def read_lines(path, fail_on_blank_lines=False):
    if not path:
        return []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    cleaned = []
    for line in lines:
        if not line and fail_on_blank_lines:
            raise ValueError(f"Blank lines are not allowed\nFile: {path}")
        cleaned.append(line)
    return cleaned


def select_file(filetypes=(), state_key=None):
    if sys.platform == "win32":
        from tkinter import Tk, filedialog

        tk = Tk()
        tk.withdraw()
        file_path = filedialog.askopenfilename()
        tk.destroy()
        return file_path or None

    assert _WINDOW is not None
    files = _WINDOW.create_file_dialog(
        webview.FileDialog.OPEN, file_types=filetypes
    )
    return files[0] if files else None


def format_seconds(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}:{secs:02d}"


def get_audio_files_and_durations(folder):
    import librosa

    audio_extensions = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aiff", ".aif"}
    files_and_durations = []

    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in audio_extensions:
                full = os.path.join(root, f)
                try:
                    duration = format_seconds(librosa.get_duration(path=full))
                except Exception:
                    duration = "0:00"
                files_and_durations.append([os.path.relpath(full, folder), duration])

    return files_and_durations


def show_species_choice(choice, file_input):
    if choice == _CUSTOM_SPECIES:
        return [
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=bool(file_input)),
        ]
    if choice == _PREDICT_SPECIES:
        return [
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        ]
    return [
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
    ]


def sample_sliders(opened=True):
    with (
        gr.Group(),
        gr.Accordion("Inference Settings", open=opened),
    ):
        with gr.Group():
            with gr.Row():
                use_top_n_checkbox = gr.Checkbox(
                    label="Use top N results",
                    value=False,
                    info="Use top N info",
                )
                top_n_input = gr.Number(
                    value=5,
                    minimum=1,
                    precision=1,
                    visible=False,
                    label="Top N",
                    info="Top N info",
                )
                confidence_slider = gr.Slider(
                    minimum=0.05,
                    maximum=0.95,
                    value=0.25,
                    step=0.05,
                    label="Minimum confidence",
                    info="Confidence info",
                )

            use_top_n_checkbox.change(
                lambda use_top_n: (
                    gr.Number(visible=use_top_n),
                    gr.Slider(visible=not use_top_n),
                ),
                inputs=use_top_n_checkbox,
                outputs=[top_n_input, confidence_slider],
                show_progress="hidden",
            )

            with gr.Row():
                sensitivity_slider = gr.Slider(
                    minimum=0.5,
                    maximum=1.5,
                    value=1.0,
                    step=0.01,
                    label="Sensitivity",
                    info="Sensitivity info",
                )
                overlap_slider = gr.Slider(
                    minimum=0,
                    maximum=2.9,
                    value=0.0,
                    step=0.1,
                    label="Overlap (s)",
                    info="Overlap info",
                )

            with gr.Row():
                merge_consecutive_slider = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=1,
                    step=1,
                    label="Merge consecutive",
                    info="Merge consecutive info",
                )
                audio_speed_slider = gr.Slider(
                    minimum=-10,
                    maximum=10,
                    value=0,
                    step=1,
                    label="Audio speed",
                    info="Audio speed info",
                )

            fmin_number, fmax_number = bandpass_settings()

        return {
            "use_top_n_checkbox": use_top_n_checkbox,
            "top_n_input": top_n_input,
            "confidence_slider": confidence_slider,
            "sensitivity_slider": sensitivity_slider,
            "overlap_slider": overlap_slider,
            "merge_consecutive_slider": merge_consecutive_slider,
            "audio_speed_slider": audio_speed_slider,
            "fmin_number": fmin_number,
            "fmax_number": fmax_number,
        }


def species_lists(opened=True):
    with (
        gr.Group(),
        gr.Accordion("Species List", open=opened),
    ):
        with gr.Row():
            values = [_ALL_SPECIES, _CUSTOM_SPECIES, _PREDICT_SPECIES]

            species_list_radio = gr.Radio(
                values,
                value=_ALL_SPECIES,
                label="Species list type",
                info="Species list info",
                elem_classes="d-block",
            )

            with gr.Column(visible=False) as position_row:
                (
                    lat_number,
                    lon_number,
                    week_number,
                    sf_thresh_number,
                    yearlong_checkbox,
                    map_plot,
                ) = species_list_coordinates()

            species_file_input = gr.File(
                file_types=[".txt"], visible=False, show_label=False
            )
            empty_col = gr.Column()

        list_df = gr.List(
            value=[],
            headers=["Species"],
            max_height=200,
            show_label=False,
            visible=False,
        )

    species_list_radio.change(
        show_species_choice,
        inputs=[species_list_radio, species_file_input],
        outputs=[position_row, species_file_input, empty_col, list_df],
        show_progress="hidden",
    )

    def on_species_file_change(file):
        if not file:
            return gr.update(value=[], visible=False)

        species_list = read_lines(file, fail_on_blank_lines=True)
        return gr.update(value=species_list, visible=True)

    species_file_input.change(
        on_species_file_change,
        inputs=species_file_input,
        outputs=list_df,
        show_progress="hidden",
    )

    return {
        "species_list_radio": species_list_radio,
        "species_file_input": species_file_input,
        "lat_number": lat_number,
        "lon_number": lon_number,
        "week_number": week_number,
        "sf_thresh_number": sf_thresh_number,
        "yearlong_checkbox": yearlong_checkbox,
        "map_plot": map_plot,
    }


def model_selection(opened=True):
    with (
        gr.Group(),
        gr.Accordion("Model Selection", open=opened),
    ):
        with gr.Row():
            values = [_USE_BIRDNET_2_4, _CUSTOM_CLASSIFIER, _USE_PERCH]

            if platform.system() == "Darwin":
                values.pop()

            model_selection_radio = gr.Radio(
                choices=values,
                value=_USE_BIRDNET_2_4,
                label="Model",
                info="Model info",
            )

            with gr.Column(visible=False) as custom_classifier_selector:
                classifier_selection_button = gr.Button(
                    "Select custom classifier"
                )
                classifier_file_input = gr.Files(
                    file_types=[".tflite"],
                    visible=False,
                    interactive=False,
                    show_label=False,
                )
                selected_classifier_state = gr.State()

                def on_custom_classifier_selection_click():
                    file = select_file(
                        ("TFLite classifier (*.tflite)",),
                        state_key="custom_classifier_file",
                    )

                    if not file:
                        return None, None, None

                    base_name = os.path.splitext(file)[0]
                    labels = base_name + "_Labels.txt"

                    if not os.path.isfile(labels):
                        labels = file.replace("Model_FP32.tflite", "Labels.txt")

                    if not os.path.isfile(labels):
                        gr.Warning("No label file found for classifier.")
                        return (
                            file,
                            gr.update(value=file, visible=True),
                            gr.update(visible=False),
                        )

                    return (
                        file,
                        gr.update(value=file, visible=True),
                        gr.update(
                            value=read_lines(labels, fail_on_blank_lines=True),
                            visible=True,
                        ),
                    )

        species_list_df = gr.List(
            value=[],
            headers=["Species"],
            max_height=200,
            show_label=False,
            visible=False,
        )

    classifier_selection_button.click(
        on_custom_classifier_selection_click,
        outputs=[selected_classifier_state, classifier_file_input, species_list_df],
        show_progress="hidden",
    )

    def on_model_selection_change(choice, cc_state):
        if choice == _CUSTOM_CLASSIFIER:
            return gr.update(visible=True), gr.update(visible=cc_state is not None)
        return gr.update(visible=False), gr.update(visible=False)

    model_selection_radio.change(
        on_model_selection_change,
        inputs=[model_selection_radio, selected_classifier_state],
        outputs=[custom_classifier_selector, species_list_df],
        show_progress="hidden",
    )

    return {
        "model_selection_radio": model_selection_radio,
        "selected_classifier_state": selected_classifier_state,
    }


def sample_species_model_settings(opened=True):
    sample_settings = sample_sliders(opened=opened)
    species_settings = species_lists(opened=opened)
    model_settings = model_selection(opened=opened)

    def on_species_list_change(value):
        is_perch = value == _USE_PERCH
        return (
            gr.update(interactive=not is_perch),
            gr.update(maximum=4.9 if is_perch else 2.9),
            gr.update(
                choices=[_CUSTOM_SPECIES, _ALL_SPECIES]
                if is_perch
                else [_CUSTOM_SPECIES, _PREDICT_SPECIES, _ALL_SPECIES],
                value=_ALL_SPECIES,
            ),
        )

    model_settings["model_selection_radio"].change(
        on_species_list_change,
        inputs=model_settings["model_selection_radio"],
        outputs=[
            sample_settings["sensitivity_slider"],
            sample_settings["overlap_slider"],
            species_settings["species_list_radio"],
        ],
        show_progress="hidden",
    )

    return sample_settings, species_settings, model_settings


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
