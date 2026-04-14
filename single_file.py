import os
from datetime import timedelta

import gradio as gr
import librosa
import numpy as np

import utils as gu

MATPLOTLIB_FIGURE_NUM = "single-file-tab-spectrogram-plot"
HEADER_START_LBL = "Start"
HEADER_END_LBL = "End"
HEADER_SCI_NAME_LBL = "Scientific Name"
HEADER_COMMON_NAME_LBL = "Common Name"
HEADER_CONFIDENCE_LBL = "Confidence"


def open_audio_file(path, offset=0.0, duration=None):
    sig, rate = librosa.load(
        path,
        sr=48000,
        offset=offset,
        duration=duration,
        mono=True,
        res_type="kaiser_fast",
    )
    return sig, rate


def spectrogram_from_file(path, fig_size=(20, 4), fig_num=None):
    import matplotlib
    import matplotlib.pyplot as plt

    matplotlib.use("agg")

    sig, rate = librosa.load(path, sr=48000, mono=True, res_type="kaiser_fast")

    if isinstance(fig_size, tuple):
        f = plt.figure(fig_num, figsize=fig_size)
    else:
        f = plt.figure(fig_num)

    f.clf()
    ax = f.add_subplot(111)
    ax.set_axis_off()
    f.tight_layout(pad=0)

    D = librosa.stft(sig, n_fft=1024, hop_length=512)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

    return librosa.display.specshow(S_db, ax=ax, n_fft=1024, hop_length=512).figure


@gu.gui_runtime_error_handler
def run_single_file_analysis(
    input_path,
    use_top_n,
    top_n,
    confidence,
    sensitivity,
    overlap,
    merge_consecutive,
    audio_speed,
    fmin,
    fmax,
    species_list_choice,
    species_list_file,
    lat,
    lon,
    week,
    use_yearlong,
    sf_thresh,
    selected_model,
    custom_classifier_file,
    locale,
):
    import pandas as pd

    gu.validate(input_path, "No file selected")

    def convert_to_time_str(seconds: float) -> str:
        time_str = str(timedelta(seconds=seconds))
        if "." in time_str:
            time_str = time_str[: time_str.index(".") + 2]
        return time_str

    # Stub: generate dummy predictions
    rows = [
        {
            "start_time": i * 3.0,
            "end_time": (i + 1) * 3.0,
            "species_name": f"Genus{i}_CommonBird{i}",
            "confidence": round(0.5 + i * 0.05, 3),
        }
        for i in range(5)
    ]
    table = pd.DataFrame(rows)
    n_rows = table.shape[0]

    table[[HEADER_SCI_NAME_LBL, HEADER_COMMON_NAME_LBL]] = table[
        "species_name"
    ].str.split("_", n=1, expand=True)

    table[" "] = ["▶"] * n_rows
    table.rename(
        columns={
            "start_time": HEADER_START_LBL,
            "end_time": HEADER_END_LBL,
            "confidence": HEADER_CONFIDENCE_LBL,
        },
        inplace=True,
    )
    table[HEADER_START_LBL] = table[HEADER_START_LBL].apply(convert_to_time_str)
    table[HEADER_END_LBL] = table[HEADER_END_LBL].apply(convert_to_time_str)
    table = table[
        [
            " ",
            HEADER_START_LBL,
            HEADER_END_LBL,
            HEADER_SCI_NAME_LBL,
            HEADER_COMMON_NAME_LBL,
            HEADER_CONFIDENCE_LBL,
        ]
    ]
    table[HEADER_CONFIDENCE_LBL] = table[HEADER_CONFIDENCE_LBL].apply(
        lambda x: f"{x:0.3f}"
    )

    return (
        table,
        gr.update(visible=True),
        {
            "fmin": fmin,
            "fmax": fmax,
            "overlap": overlap,
            "sensitivity": sensitivity,
            "lat": lat,
            "lon": lon,
            "week": week,
        },
    )


def build_single_analysis_tab():
    with gr.Tab("Single File Analysis"):
        with gr.Group(), gr.Row(equal_height=True):
            select_file_button = gr.Button(
                "Select Audio File",
                variant="primary",
            )
            selected_file_label = gr.Textbox(
                show_label=False,
                interactive=False,
                placeholder="No file selected",
                scale=3,
            )

        audio_input = gr.Audio(
            type="numpy",
            label="Audio",
            interactive=False,
            visible=False,
            editable=False,
        )

        with gr.Group():
            spectogram_output = gr.Plot(
                label="Spectrogram",
                visible=False,
                show_label=False,
            )
            generate_spectrogram_cb = gr.Checkbox(
                value=False,
                label="Generate spectrogram",
                info="Enable to show a spectrogram of the selected file.",
            )

        audio_path_state = gr.State()
        last_prediction_state = gr.State()

        sample_settings, species_settings, model_settings = (
            gu.sample_species_model_settings(opened=False)
        )
        locale_radio = gu.locale()

        single_file_analyze = gr.Button(
            "Analyze",
            variant="huggingface",
            interactive=False,
        )

        with gr.Row(visible=False) as action_row:
            with gr.Group(), gr.Column():
                rtable_download_button = gr.Button("Download Raven table")
                csv_download_button = gr.Button("Download CSV")
                kaleidoscope_download_button = gr.Button(
                    "Download Kaleidoscope table"
                )
            segment_audio = gr.Audio(
                autoplay=True,
                type="numpy",
                buttons=["download"],
                show_label=False,
                editable=False,
                visible=False,
            )

        output_dataframe = gr.Dataframe(
            type="pandas",
            headers=[
                " ",
                HEADER_START_LBL,
                HEADER_END_LBL,
                HEADER_SCI_NAME_LBL,
                HEADER_COMMON_NAME_LBL,
                HEADER_CONFIDENCE_LBL,
            ],
            elem_id="single-file-output",
            interactive=False,
        )

        # -- Callbacks --------------------------------------------------------

        def select_and_load_audio_file(generate_spectrogram):
            file_path = gu.select_file(
                filetypes=(
                    "Audio files (*.wav;*.flac;*.mp3;*.ogg;*.m4a;*.wma;*.aiff;*.aif)",
                ),
                state_key="single_file_audio",
            )

            if file_path:
                try:
                    data, sr = open_audio_file(file_path)

                    spectrogram = (
                        gr.update(
                            visible=True,
                            value=spectrogram_from_file(
                                file_path,
                                fig_size=(20, 4),
                                fig_num=MATPLOTLIB_FIGURE_NUM,
                            ),
                        )
                        if generate_spectrogram
                        else gr.update(visible=False)
                    )

                    return (
                        file_path,
                        os.path.basename(file_path),
                        gr.update(
                            visible=True,
                            value=(sr, data),
                            label=os.path.basename(file_path),
                        ),
                        spectrogram,
                        gr.update(interactive=True),
                    )
                except Exception as e:
                    raise gr.Error("Could not load audio file") from e

            return (
                None,
                "",
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(interactive=False),
            )

        def try_generate_spectrogram(audio_path, generate_spectrogram):
            if audio_path and generate_spectrogram:
                try:
                    return gr.Plot(
                        visible=True,
                        value=spectrogram_from_file(
                            audio_path,
                            fig_size=(20, 4),
                            fig_num=MATPLOTLIB_FIGURE_NUM,
                        ),
                    )
                except Exception as e:
                    raise gr.Error("Could not generate spectrogram") from e
            else:
                return gr.Plot(visible=False)

        def time_to_seconds(time_str: str):
            try:
                hours, minutes, seconds = time_str.split(":")
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            except ValueError as e:
                raise ValueError(
                    "Input must be in the format hh:mm:ss or hh:mm:ss.ssssss "
                    "with numeric values."
                ) from e

        def get_selected_audio(evt: gr.SelectData, audio_path):
            if evt.index[1] == 0 and evt.row_value[1] and evt.row_value[2]:
                start = time_to_seconds(evt.row_value[1])
                end = time_to_seconds(evt.row_value[2])

                data, sr = open_audio_file(
                    audio_path, offset=start, duration=end - start
                )

                return gr.update(visible=True, value=(sr, data))

            return gr.update()

        def download_rtable(prediction_state):
            if prediction_state:
                file_location = gu.save_file_dialog(
                    default_filename="BirdNET_SelectionTable.txt",
                    filetypes=("txt (*.txt)",),
                )
                if file_location:
                    gr.Info(f"Would save Raven table to: {file_location}")

        def download_csv(prediction_state):
            if prediction_state:
                file_location = gu.save_file_dialog(
                    default_filename="BirdNET_CombinedTable.csv",
                    filetypes=("CSV (*.csv)",),
                )
                if file_location:
                    gr.Info(f"Would save CSV to: {file_location}")

        def download_kaleidoscope(prediction_state):
            if prediction_state:
                file_location = gu.save_file_dialog(
                    default_filename="BirdNET_Kaleidoscope.csv",
                    filetypes=("Kaleidoscope (*.txt)",),
                )
                if file_location:
                    gr.Info(f"Would save Kaleidoscope to: {file_location}")

        # -- Wiring -----------------------------------------------------------

        generate_spectrogram_cb.change(
            try_generate_spectrogram,
            inputs=[audio_path_state, generate_spectrogram_cb],
            outputs=spectogram_output,
        )

        select_file_button.click(
            select_and_load_audio_file,
            inputs=[generate_spectrogram_cb],
            outputs=[
                audio_path_state,
                selected_file_label,
                audio_input,
                spectogram_output,
                single_file_analyze,
            ],
        )

        inputs = [
            audio_path_state,
            sample_settings["use_top_n_checkbox"],
            sample_settings["top_n_input"],
            sample_settings["confidence_slider"],
            sample_settings["sensitivity_slider"],
            sample_settings["overlap_slider"],
            sample_settings["merge_consecutive_slider"],
            sample_settings["audio_speed_slider"],
            sample_settings["fmin_number"],
            sample_settings["fmax_number"],
            species_settings["species_list_radio"],
            species_settings["species_file_input"],
            species_settings["lat_number"],
            species_settings["lon_number"],
            species_settings["week_number"],
            species_settings["yearlong_checkbox"],
            species_settings["sf_thresh_number"],
            model_settings["model_selection_radio"],
            model_settings["selected_classifier_state"],
            locale_radio,
        ]

        single_file_analyze.click(
            run_single_file_analysis,
            inputs=inputs,
            outputs=[output_dataframe, action_row, last_prediction_state],
        )
        output_dataframe.select(
            get_selected_audio, inputs=audio_path_state, outputs=segment_audio
        )
        rtable_download_button.click(download_rtable, inputs=last_prediction_state)
        csv_download_button.click(download_csv, inputs=last_prediction_state)
        kaleidoscope_download_button.click(
            download_kaleidoscope, inputs=last_prediction_state
        )

    return (
        species_settings["lat_number"],
        species_settings["lon_number"],
        species_settings["map_plot"],
    )


if __name__ == "__main__":
    gu.open_window(build_single_analysis_tab)
