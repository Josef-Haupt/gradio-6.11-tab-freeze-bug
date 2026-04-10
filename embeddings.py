import os

import gradio as gr

import utils as gu


def run_embeddings_with_tqdm_tracking(
    input_path,
    db_directory,
    overlap,
    batch_size,
    producers_number,
    workers_number,
    audio_speed,
    fmin,
    fmax,
    enable_file_output,
    file_output,
    progress=gr.Progress(track_tqdm=True),
):
    return run_embeddings(
        input_path,
        db_directory,
        overlap,
        producers_number,
        workers_number,
        batch_size,
        audio_speed,
        fmin,
        fmax,
        file_output if enable_file_output else None,
        progress,
    )


@gu.gui_runtime_error_handler
def run_embeddings(
    input_path,
    db_directory,
    overlap,
    producers_number,
    workers_number,
    batch_size,
    audio_speed,
    fmin,
    fmax,
    file_output,
    progress,
):
    gu.validate(input_path, "No input directory selected")
    gu.validate(db_directory, "No database directory selected")

    # Stub: original calls birdnet_analyzer.embeddings.core.embeddings(...)
    gr.Info(f"Embeddings saved to {db_directory}")

    return (
        gr.Plot(),
        gr.Slider(interactive=False),
        gr.Number(interactive=False),
        gr.Number(interactive=False),
    )


def build_embeddings_tab():
    with gr.Tab("Embeddings"):
        input_directory_state = gr.State()
        db_directory_state = gr.State()

        def select_directory_to_state_and_tb(current):
            path = (
                gu.select_directory(collect_files=False)
                or current
                or None
            )
            return path, path

        with gr.Group(), gr.Row(equal_height=True):
            select_audio_directory_btn = gr.Button(
                "Select Input Directory"
            )
            selected_audio_directory_tb = gr.Textbox(
                show_label=False, interactive=False, scale=2
            )
            select_audio_directory_btn.click(
                select_directory_to_state_and_tb,
                inputs=[input_directory_state],
                outputs=[selected_audio_directory_tb, input_directory_state],
                show_progress="hidden",
            )

        with gr.Group(), gr.Row(equal_height=True):
            select_db_directory_btn = gr.Button(
                "Select Database Directory"
            )
            db_path_tb = gr.Textbox(
                show_label=False,
                buttons=["copy"],
                interactive=False,
                info="⚠️ Database path info",
                scale=2,
            )

        with gr.Group(visible=False) as file_output_row, gr.Row(equal_height=True):
            file_output_cb = gr.Checkbox(
                label="Enable file output",
                value=False,
                interactive=True,
            )

            with gr.Column(scale=2), gr.Group():
                select_file_output_directory_btn = gr.Button(
                    "Select File Output Directory",
                    visible=False,
                )
                file_output_tb = gr.Textbox(
                    value=None,
                    placeholder="File output directory",
                    interactive=False,
                    label="File output directory",
                    visible=False,
                )

            def on_cb_click(status, current, db_dir):
                if not current:
                    return gr.update(visible=status), gr.update(
                        visible=status, value=os.path.join(db_dir, "embeddings.csv")
                    )

                return gr.update(visible=status), gr.update(visible=status)

            file_output_cb.change(
                fn=on_cb_click,
                inputs=[file_output_cb, file_output_tb, db_directory_state],
                outputs=[select_file_output_directory_btn, file_output_tb],
                show_progress="hidden",
            )

        with (
            gr.Group(),
            gr.Accordion(
                "Settings", open=False
            ),
        ):
            with gr.Row():
                overlap_slider = gr.Slider(
                    minimum=0,
                    maximum=2.9,
                    value=0,
                    step=0.1,
                    label="Overlap",
                    info="Overlap info",
                )
                audio_speed_slider = gr.Slider(
                    minimum=-10,
                    maximum=10,
                    value=0,
                    step=1,
                    label="Audio speed",
                    info="Audio speed info",
                )

            bs_number, producers_number, workers_number = gu.computing_settings()

            fmin_number, fmax_number = gu.bandpass_settings()

        def select_directory_and_update_tb(current_state):
            dir_name = gu.select_directory(collect_files=False)

            if dir_name:
                return (
                    dir_name,
                    gr.Textbox(value=dir_name),
                    gr.Slider(interactive=True),
                    gr.Number(interactive=True),
                    gr.Number(interactive=True),
                    gr.update(visible=True),
                )

            value = current_state or None

            return (
                value,
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

        select_db_directory_btn.click(
            select_directory_and_update_tb,
            inputs=[db_directory_state],
            outputs=[
                db_directory_state,
                db_path_tb,
                audio_speed_slider,
                fmin_number,
                fmax_number,
                file_output_row,
            ],
            show_progress="hidden",
        )

        def select_file_output_directory_and_update_tb(current):
            file_location = gu.save_file_dialog(
                filetypes=("CSV (*.csv)",),
                default_filename="embeddings.csv",
            )

            return file_location or current

        select_file_output_directory_btn.click(
            select_file_output_directory_and_update_tb,
            inputs=[file_output_tb],
            outputs=[file_output_tb],
            show_progress="hidden",
        )

        progress_plot = gr.Plot(show_label=False)
        start_btn = gr.Button(
            "Run", variant="huggingface"
        )

        start_btn.click(
            run_embeddings_with_tqdm_tracking,
            inputs=[
                input_directory_state,
                db_directory_state,
                overlap_slider,
                bs_number,
                producers_number,
                workers_number,
                audio_speed_slider,
                fmin_number,
                fmax_number,
                file_output_cb,
                file_output_tb,
            ],
            outputs=[progress_plot, audio_speed_slider, fmin_number, fmax_number],
            show_progress_on=progress_plot,
        )
