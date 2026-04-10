import utils as gu
import species
import embeddings


def main():
    gu.open_window(
        [
            species.build_species_tab,
            embeddings.build_embeddings_tab,
        ]
    )


if __name__ == "__main__":
    main()
