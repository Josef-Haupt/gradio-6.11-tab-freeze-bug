import gradio as gr

import utils as gu


@gu.gui_runtime_error_handler
def run_species_list(
    out_path, filename, lat, lon, week, use_yearlong, sf_thresh, locale
):
    gu.validate(out_path, "No directory selected")

    # Stub: original calls birdnet_analyzer.species.core.species(...)
    gr.Info(f"Species list saved to {out_path}")


def build_species_tab():
    with gr.Tab("Species") as species_tab:
        output_directory_state = gr.State()
        select_directory_btn = gr.Button("Select Output Directory")
        classifier_name = gr.Textbox(
            "species_list.txt",
            visible=False,
            info="Output filename",
        )

        def select_directory_and_update_tb(name_tb):
            dir_name = gu.select_folder()

            if dir_name:
                return (
                    dir_name,
                    gr.Textbox(label=dir_name, visible=True, value=name_tb),
                )

            return None, name_tb

        select_directory_btn.click(
            select_directory_and_update_tb,
            inputs=classifier_name,
            outputs=[output_directory_state, classifier_name],
            show_progress="hidden",
        )

        (
            lat_number,
            lon_number,
            week_number,
            sf_thresh_number,
            yearlong_checkbox,
            map_plot,
        ) = gu.species_list_coordinates(show_map=True)

        locale = gu.locale()

        start_btn = gr.Button("Run", variant="huggingface")
        start_btn.click(
            run_species_list,
            inputs=[
                output_directory_state,
                classifier_name,
                lat_number,
                lon_number,
                week_number,
                yearlong_checkbox,
                sf_thresh_number,
                locale,
            ],
        )

    species_tab.select(
        lambda lat, lon: gu.plot_map_scatter_mapbox(lat, lon, zoom=3),
        inputs=[lat_number, lon_number],
        outputs=map_plot,
    )

    return lat_number, lon_number, map_plot
