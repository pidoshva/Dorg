"""Messy preset: pure chaos for fun."""

import random
from pathlib import Path

from classifier.signals import FileClassification
from engine import MoveAction
from . import BasePreset, register

FUNNY_FOLDERS = [
    "definitely_not_homework",
    "tax_returns_2077",
    "grandmas_secret_recipes",
    "area_51_leaked_docs",
    "minecraft_server_backup",
    "cats_wearing_tiny_hats",
    "my_startup_idea",
    "please_dont_open",
    "nothing_to_see_here",
    "the_forbidden_folder",
    "secret_pizza_recipes",
    "time_travel_research",
    "alien_communication_logs",
    "my_mixtape_fire_emoji",
    "todo_lists_from_2019",
    "very_important_stuff",
    "NOT_a_virus",
    "wedding_plans_ignore",
    "mystery_meat_folder",
    "the_good_memes",
    "totally_organized",
    "ask_your_mother",
    "folder_of_mystery",
    "stuff_and_things",
    "misc_do_not_delete",
    "probably_fine",
    "im_helping",
    "the_drawer_of_doom",
    "garage_sale_leftovers",
    "lost_and_found",
    "this_sparks_joy",
    "new_folder_final_FINAL_v2",
    "old_stuff_DO_NOT_DELETE",
    "budget_2099",
    "vacation_plans_mars",
    "fitness_goals_lol",
    "recipe_for_disaster",
    "my_memoirs_draft_47",
    "passwords_definitely_not",
    "the_junk_drawer",
    "quantum_physics_notes",
    "sock_inventory",
    "conspiracy_board",
    "pet_photos_hall_of_fame",
    "error_404_folder_not_found",
    "abandoned_projects",
    "things_I_googled_at_3am",
    "the_bermuda_folder",
    "dads_dad_jokes",
    "cursed_images",
    "homework_real_this_time",
    "untitled_folder_237",
    "snack_ideas",
    "world_domination_plans",
]


@register
class MessyPreset(BasePreset):
    name = "Messy"
    description = "Pure chaos — for when you just want to watch the world burn"
    icon = "🌪️"

    def organize(
        self,
        files: list[tuple[Path, FileClassification]],
        base_dir: Path,
    ) -> list[MoveAction]:
        actions = []
        available_folders = list(FUNNY_FOLDERS)
        random.shuffle(available_folders)

        file_list = list(files)
        random.shuffle(file_list)

        for file_path, classification in file_list:
            # Random nesting depth 1-4
            depth = random.randint(1, 4)

            # Pick random folder names (with replacement across files, but not within a single path)
            path_parts = random.sample(
                FUNNY_FOLDERS,
                min(depth, len(FUNNY_FOLDERS)),
            )

            folder = Path(*path_parts)
            dest = base_dir / folder / file_path.name

            actions.append(MoveAction(
                source=file_path,
                destination=dest,
                classification=classification,
            ))

        return actions
