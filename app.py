import utils as gu
import species
import embeddings
import single_file
import multi_file


def main():
    gu.open_window(
        [
            single_file.build_single_analysis_tab,
            multi_file.build_multi_analysis_tab,
            species.build_species_tab,
            embeddings.build_embeddings_tab,
        ]
    )


if __name__ == "__main__":
    main()
