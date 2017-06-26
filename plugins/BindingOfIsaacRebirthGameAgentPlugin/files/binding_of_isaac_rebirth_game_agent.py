from lib.game_agent import GameAgent

import lib.cv

from lib.analytics_client import AnalyticsClient
from lib.frame_grabber import FrameGrabber

from lib.machine_learning.context_classification.context_classifiers import *

from lib.machine_learning.reinforcement_learning.dqn import DQN
from lib.machine_learning.reinforcement_learning.ddqn import DDQN

from lib.machine_learning.reinforcement_learning.keyboard_mouse_action_space import KeyboardMouseActionSpace

from .helpers.frame_processing import *

from .helpers.game_floor import GameFloor
from .helpers.game_minimap import GameMinimap

import offshoot

import time
import uuid
import subprocess
import shlex
import itertools
import collections
import os.path

import gc

import numpy as np

import skimage.io
import skimage.filters
import skimage.morphology
import skimage.measure
import skimage.draw
import skimage.segmentation
import skimage.color

import pyperclip
from termcolor import cprint

from collections import deque

from datetime import datetime, timedelta


class BindingOfIsaacRebirthGameAgent(GameAgent):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.frame_handlers["PLAY"] = self.handle_play
        self.frame_handlers["GAME_TRAIN"] = self.handle_game_train
        self.frame_handlers["BOSS_TRAIN_DQN"] = self.handle_boss_train_dqn
        self.frame_handlers["BOSS_TRAIN_DDQN"] = self.handle_boss_train_dqn

        self.frame_handler_setups["PLAY"] = self.setup_play
        self.frame_handler_setups["GAME_TRAIN"] = self.setup_game_train
        self.frame_handler_setups["BOSS_TRAIN_DQN"] = self.setup_boss_train_dqn
        self.frame_handler_setups["BOSS_TRAIN_DDQN"] = self.setup_boss_train_ddqn

        self.game_state = None
        self._reset_game_state()

        self.analytics_client = None

    @property
    def characters(self):
        return ["ISAAC", "MAGDALENE", "CAIN", "JUDAS", "EVE", "SAMSON", "AZAZEL", "LAZARUS", "EDEN", "RANDOM"]

    @property
    def difficulties(self):
        return ["NORMAL", "HARD"]

    @property
    def game_contexts(self):
        return dict(

        )

    @property
    def game_context_handlers(self):
        return dict(
            intro=self.handle_context_intro,
            splash_screen=self.handle_context_splash_screen,
            file_select_screen=self.handle_context_file_select_screen,
            menu=self.handle_context_menu,
            character_select_screen=self.handle_context_character_select_screen,
            game=self.handle_context_game,
            death_screen=self.handle_context_death_screen
        )

    def setup_play(self):
        plugin_path = offshoot.config["file_paths"]["plugins"]

        ocr_classifier_path = f"{plugin_path}/BindingOfIsaacRebirthGameAgentPlugin/files/ml_models/binding_of_isaac_rebirth_ocr.model"
        self.machine_learning_models["ocr_classifier"] = self.load_machine_learning_model(ocr_classifier_path)

        context_classifier_path = f"{plugin_path}/BindingOfIsaacRebirthGameAgentPlugin/files/ml_models/binding_of_isaac_rebirth_context.model"

        context_classifier = CNNInceptionV3ContextClassifier(input_shape=(270, 480, 3))
        context_classifier.prepare_generators()
        context_classifier.load_classifier(context_classifier_path)

        self.machine_learning_models["context_classifier"] = context_classifier

    def setup_game_train(self):
        pass

    def setup_boss_train_dqn(self):
        self.analytics_client = AnalyticsClient(project_key="AISAAC_MONSTRO")

        input_mapping = {
            "W": ["w"],
            "A": ["a"],
            "S": ["s"],
            "D": ["d"],
            "WA": ["w", "a"],
            "WD": ["w", "d"],
            "SA": ["s", "a"],
            "SD": ["s", "d"],
            "UP": [self.input_controller.keyboard.up_key],
            "LEFT": [self.input_controller.keyboard.left_key],
            "DOWN": [self.input_controller.keyboard.down_key],
            "RIGHT": [self.input_controller.keyboard.right_key]
        }

        action_space = KeyboardMouseActionSpace(
            directional_keys=[None, "W", "A", "S", "D", "WA", "WD", "SA", "SD"],
            projectile_keys=["UP", "LEFT", "DOWN", "RIGHT"]
        )

        model_file_path = "datasets/binding_of_isaac_rebirth_boss_1010_dqn_100000_0.1_.h5555"

        self.dqn = DQN(
            model_file_path=model_file_path if os.path.isfile(model_file_path) else None,
            input_shape=(67, 120, 4),
            input_mapping=input_mapping,
            action_space=action_space,
            replay_memory_size=4000,
            max_steps=100000,
            observe_steps=2000,
            batch_size=64,
            initial_epsilon=1,
            final_epsilon=0.1,
            override_epsilon=False
        )

        pyperclip.set_clipboard("xsel")
        pyperclip.copy(f"goto s.boss.{str(self.config['boss'])}")

    def setup_boss_train_ddqn(self):
        self.analytics_client = AnalyticsClient(project_key="AISAAC_MONSTRO")

        input_mapping = {
            "W": ["w"],
            "A": ["a"],
            "S": ["s"],
            "D": ["d"],
            "WA": ["w", "a"],
            "WD": ["w", "d"],
            "SA": ["s", "a"],
            "SD": ["s", "d"],
            "UP": [self.input_controller.keyboard.up_key],
            "LEFT": [self.input_controller.keyboard.left_key],
            "DOWN": [self.input_controller.keyboard.down_key],
            "RIGHT": [self.input_controller.keyboard.right_key]
        }

        action_space = KeyboardMouseActionSpace(
            directional_keys=[None, "W", "A", "S", "D", "WA", "WD", "SA", "SD"],
            projectile_keys=["UP", "LEFT", "DOWN", "RIGHT"]
        )

        model_file_path = "datasets/binding_of_isaac_rebirth_boss_1010_dqn_100000_0.1_.h5555"

        self.dqn = DDQN(
            model_file_path=model_file_path if os.path.isfile(model_file_path) else None,
            input_shape=(67, 120, 4),
            input_mapping=input_mapping,
            action_space=action_space,
            replay_memory_size=4000,
            max_steps=500000,
            observe_steps=2000,
            batch_size=64,
            initial_epsilon=1,
            final_epsilon=0.1,
            override_epsilon=False
        )

        pyperclip.set_clipboard("xsel")
        pyperclip.copy(f"goto s.boss.{str(self.config['boss'])}")

    def handle_play(self, game_frame):
        pass

        # if self.game_frame_buffer.previous_game_frame:
        #     self.game_frame_ssim = game_frame.compare_ssim(self.game_frame_buffer.previous_game_frame)
        # else:
        #     self.game_frame_ssim = 0.0
        #
        # if self.game_context is None or self.game_frame_ssim <= 0.75:
        #     previous_context = self.game_context
        #     self.game_context = self.machine_learning_models["context_classifier"].predict(game_frame.frame)
        #
        #     if self.game_context == "character_select_screen":
        #         self.game_state["character_select_generator"] = itertools.cycle(self.characters)
        #     elif self.game_context == "game":
        #         if self.game_context != previous_context:
        #             self.flag = "ENTERING_GAME"
        #             print("setting ENTERING_GAME")
        #             time.sleep(3)
        #             return None
        #
        # self.game_context_handlers.get(self.game_context, lambda gf: True)(game_frame)

    def handle_game_train(self, game_frame):
        pass

    def handle_boss_train_dqn(self, game_frame):
        gc.disable()

        if self.dqn.first_run:
            self._goto_boss()
            self.dqn.first_run = False

            return None

        hearts = frame_to_hearts(game_frame.frame, self.game)

        # Check for Curse of Unknown
        if not len(hearts):
            self.input_controller.tap_key("r", duration=1.5)
            self._goto_boss()

            return None

        self.game_state["health"].appendleft(24 - hearts.count(None))
        self.analytics_client.track(event_key="ISAAC_HP", data={"value": self.game_state["health"][0], "min": 0, "max": 6})

        self.game_state["boss_health"].appendleft(self._get_boss_health(game_frame))
        self.analytics_client.track(event_key="BOSS_HP", data={"value": self.game_state["boss_health"][0], "min": 0, "max": 654})

        if self.dqn.frame_stack is None:
            self.dqn.build_frame_stack(game_frame.eighth_resolution_grayscale_frame)
        else:
            reward = self._calculate_boss_train_reward()
            self.game_state["run_reward"] += reward

            self.analytics_client.track(event_key="DQN_REWARD", data=float(reward))

            game_frame_buffer = FrameGrabber.get_frames(
                [0, 8, 16, 24],
                game_frame.frame.shape,
                mode="MINI"
            )

            self.dqn.append_to_replay_memory(
                game_frame_buffer,
                reward,
                terminal=self.game_state["health"] == 0
            )

            if reward != 0:
                self.game_state["activity_log"].appendleft(reward)

            # Every 2000 steps, save latest weights to disk
            if self.dqn.current_step % 2000 == 0:
                self.dqn.save_model_weights(
                    file_path_prefix=f"datasets/binding_of_isaac_rebirth_boss_{self.config['boss']}"
                )

            # Every 20000 steps, save weights checkpoint to disk
            if self.dqn.current_step % 20000 == 0:
                self.dqn.save_model_weights(
                    file_path_prefix=f"datasets/binding_of_isaac_rebirth_boss_{self.config['boss']}",
                    is_checkpoint=True
                )

            print("\033c" + f"EPISODE START TIME: {self.started_at.isoformat()}")
            print("")

            self.dqn.output_step_data()

            print("")
            print(f"CURRENT RUN: {self.game_state['current_run']}")
            print(f"CURRENT RUN REWARD: {self.game_state['run_reward']}")

            if self.dqn.epsilon_greedy_q_policy.epsilon < 0.8:
                print(f"CURRENT RUN PREDICTED ACTIONS: {self.game_state['run_predicted_actions']}")
                print(f"AVERAGE FUTURE REWARDS: {self.game_state['previous_run_future_rewards']}")

            print(f"AVERAGE ACTIONS PER SECOND: {self.game_state['average_aps']}")
            print(f"CURRENT HEALTH: {self.game_state['health'][0]}")
            print(f"CURRENT BOSS HEALTH: {self.game_state['boss_health'][0]}")
            print("")
            print(f"LAST RUN DURATION: {self.game_state['last_run_duration']} second(s)")

            print("")
            print(f"RECORD TIME ALIVE: {self.game_state['record_time_alive']} second(s)")
            print(f"RECORD BOSS HP: {self.game_state['record_boss_hp']}")
            print("")

            print("")
            print("ACTIVITY LOG:")
            print("")

            for reward in self.game_state["activity_log"]:
                if reward < 0:
                    cprint("Isaac got hit by the boss!".ljust(30) + f"=>  Penalty: {round(reward, 6)}", "red")
                elif reward > 0:
                    cprint("Isaac hit the boss".ljust(30) + f"=>  Reward: {round(reward, 6)}", "green")

            is_boss_dead = self._is_boss_dead(self.game_frame_buffer.previous_game_frame)

            if self.game_state["health"][1] <= 0 or is_boss_dead:
                self.analytics_client.track(
                    event_key="ACTIONS",
                    data={
                        "actions": [],
                        "action_type": self.dqn.current_action_type
                    }
                )

                print("\033c")
                timestamp = datetime.utcnow()

                gc.enable()
                gc.collect()
                gc.disable()

                self.game_state["run_epsilon"] = self.dqn.epsilon_greedy_q_policy.epsilon

                timestamp_delta = timestamp - self.game_state["run_timestamp"]

                self.game_state["last_run_duration"] = timestamp_delta.seconds

                # Check for Records
                if self.game_state["last_run_duration"] > self.game_state["record_time_alive"]:
                    self.game_state["record_time_alive"] = self.game_state["last_run_duration"]

                if self.game_state["boss_health"][0] < self.game_state["record_boss_hp"]:
                    self.game_state["record_boss_hp"] = self.game_state["boss_health"][0]

                # Compute APS
                self.game_state["average_aps"] = self.game_state["current_run_steps"] / self.game_state["last_run_duration"]
                self.game_state["current_run_steps"] = 0

                self.input_controller.release_keys()
                self.input_controller.tap_key("r", duration=1.5)

                if self.dqn.mode == "TRAIN":
                    for i in range(50):
                        print("\033c")
                        print(f"TRAINING ON MINI-BATCH: {i + 1}/50")
                        print(f"NEXT RUN: {self.game_state['current_run'] + 1} {'- AI RUN' if (self.game_state['current_run'] + 1) % 20 == 0 else ''}")

                        self.dqn.train_on_mini_batch()

                    self.analytics_client.track(event_key="DQN_MODEL_LOSS", data=float(self.dqn.model_loss))

                self.game_state["previous_run_future_rewards"] = self.game_state["run_future_rewards"] / (self.game_state["run_predicted_actions"] or 1000000)

                self.game_state["boss_skull_image"] = None

                self.game_state["run_timestamp"] = datetime.utcnow()
                self.game_state["current_run"] += 1
                self.game_state["run_reward"] = 0
                self.game_state["run_future_rewards"] = 0
                self.game_state["run_predicted_actions"] = 0
                self.game_state["health"] = collections.deque(np.full((8,), 6), maxlen=8)
                self.game_state["boss_health"] = collections.deque(np.full((8,), 654), maxlen=8)
                self.game_state["activity_log"].clear()

                if self.dqn.mode in ["TRAIN", "RUN"]:
                    if self.game_state["current_run"] > 0 and self.game_state["current_run"] % 40 == 0:
                        if self.dqn.type == "DDQN":
                            self.dqn.update_target_model()

                    if self.game_state["current_run"] > 0 and self.game_state["current_run"] % 20 == 0:
                        self.dqn.enter_run_mode()

                        self.analytics_client.track(
                            event_key="NEW_RUN",
                            data={
                                "run": self.game_state["current_run"],
                                "run_type": "RUN",
                                "last_run_duration": self.game_state["last_run_duration"]
                            }
                        )

                        subprocess.call(shlex.split(f"play -v 0.125 {self.config.get('ai_run_sound_path')}"))
                    else:
                        self.dqn.enter_train_mode()

                        self.analytics_client.track(
                            event_key="NEW_RUN",
                            data={
                                "run": self.game_state["current_run"],
                                "run_type": "TRAIN",
                                "last_run_duration": self.game_state["last_run_duration"]
                            }
                        )

                self._goto_boss()

                return None

        self.dqn.pick_action()

        if self.dqn.current_action_type == "PREDICTED":
            self.analytics_client.track(event_key="DQN_FUTURE_REWARDS", data=[float(q) for q in list(self.dqn.maximum_future_rewards.reshape((self.dqn.action_count,)))])

            self.game_state["run_future_rewards"] += self.dqn.maximum_future_rewards[0][self.dqn.current_action_index]
            self.game_state["run_predicted_actions"] += 1

        self.dqn.generate_action()

        self.dqn.erode_epsilon(factor=2)
        self.analytics_client.track(event_key="DQN_EPSILON", data=self.dqn.epsilon_greedy_q_policy.epsilon)

        self.input_controller.handle_keys(self.dqn.get_input_values())

        self.analytics_client.track(
            event_key="ACTIONS",
            data={
                "actions": [(self.input_controller.human_readable_key_mapping().get(input_value) or input_value).upper()
                            for input_value in self.dqn.get_input_values()],
                "action_type": self.dqn.current_action_type
            }
        )

        self.dqn.next_step()
        self.game_state["current_run_steps"] += 1

    def handle_context_intro(self, game_frame):
        self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        time.sleep(1)

    def handle_context_splash_screen(self, game_frame):
        self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        time.sleep(1)

    def handle_context_file_select_screen(self, game_frame):
        self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        time.sleep(1)

    def handle_context_menu(self, game_frame):
        self._reset_game_state()

        new_game_image = lib.cv.extract_region_from_image(
            game_frame.grayscale_frame,
            self.game.screen_regions["MENU_NEW_GAME"]
        )

        if 400 < new_game_image[new_game_image <= 128].size < 500:
            self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        else:
            self.input_controller.tap_key(self.input_controller.keyboard.up_key)

        self.game_state["seed_entered"] = False

        time.sleep(1)

    def handle_context_character_select_screen(self, game_frame):
        # Difficulty
        if "difficulty" in self.config:
            normal_difficulty_image = lib.cv.extract_region_from_image(
                game_frame.grayscale_frame,
                self.game.screen_regions["CHARACTER_SELECT_DIFFICULTY_NORMAL"]
            )

            hard_difficulty_image = lib.cv.extract_region_from_image(
                game_frame.grayscale_frame,
                self.game.screen_regions["CHARACTER_SELECT_DIFFICULTY_HARD"]
            )

            difficulty_images = [normal_difficulty_image, hard_difficulty_image]
            difficulty_is_selected = [image[image <= 128].size > 100 for image in difficulty_images]

            current_difficulty = self.difficulties[difficulty_is_selected.index(True)]

            if current_difficulty != self.config["difficulty"]:
                self.input_controller.tap_key(self.input_controller.keyboard.down_key)

        # Seed
        if "seed" in self.config and not self.game_state["seed_entered"]:
            self.input_controller.tap_key(self.input_controller.keyboard.tab_key)
            time.sleep(1)

            for character in self.config["seed"].lower():
                self.input_controller.tap_key(character)

            time.sleep(1)
            self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
            time.sleep(1)
            self.game_state["seed_entered"] = True

        current_character = next(self.game_state["character_select_generator"])

        if current_character == self.config.get("character", "ISAAC"):
            self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        else:
            self.input_controller.tap_key(self.input_controller.keyboard.right_key)

        time.sleep(1)

    def handle_context_game(self, game_frame):
        self.visual_debugger.store_image_data(
            game_frame.quarter_resolution_frame,
            game_frame.quarter_resolution_frame.shape,
            "quarter_frame"
        )

    def handle_context_death_screen(self, game_frame):
        self._reset_game_state()
        self.input_controller.tap_key(" ")

        time.sleep(1)

    def _reset_game_state(self):
        self.game_state = {
            "character_select_generator": itertools.cycle(self.characters),
            "seed_entered": False,
            "health": collections.deque(np.full((2,), 6), maxlen=2),
            "inventory": {
                "pickups": {
                    "coins": 0,
                    "bombs": 0,
                    "keys": 0
                },
                "items": [],
                "trinkets": [],
                "single_use_item": None,
                "charge_item": None
            },
            "game_floor": None,
            "minimap": None,
            "boss_health": collections.deque(np.full((2,), 654), maxlen=2),
            "boss_skull_image": None,
            "current_run": 1,
            "current_run_steps": 0,
            "average_aps": 0,
            "previous_run_future_rewards": 0,
            "run_reward": 0,
            "run_future_rewards": 0,
            "run_predicted_actions": 0,
            "run_epsilon": 1.0,
            "run_timestamp": datetime.utcnow(),
            "last_run_duration": 0,
            "activity_log": deque(maxlen=15),
            "record_time_alive": 0,
            "record_boss_hp": 654
        }

    def _update_current_room(self, game_frame):
        door_image_data = get_door_image_data(game_frame.grayscale_frame, self.game, debug=True)
        door_white_pixel_counts = [(image[image >= 1].size, label) for label, image in door_image_data.items()]
        door_label = max(door_white_pixel_counts, key=lambda t: t[0])[1]

        # TODO: Add support for irregular room layouts... Assuming Normal Room layout
        if door_label == "GAME_ISAAC_DOOR_TOP":
            self.game_state["game_floor"].current_room = (
                self.game_state["game_floor"].current_room[0],
                self.game_state["game_floor"].current_room[1] - 1
            )
        elif door_label == "GAME_ISAAC_DOOR_RIGHT":
            self.game_state["game_floor"].current_room = (
                self.game_state["game_floor"].current_room[0] - 1,
                self.game_state["game_floor"].current_room[1]
            )
        elif door_label == "GAME_ISAAC_DOOR_BOTTOM":
            self.game_state["game_floor"].current_room = (
                self.game_state["game_floor"].current_room[0],
                self.game_state["game_floor"].current_room[1] + 1
            )
        elif door_label == "GAME_ISAAC_DOOR_LEFT":
            self.game_state["game_floor"].current_room = (
                self.game_state["game_floor"].current_room[0] + 1,
                self.game_state["game_floor"].current_room[1]
            )

    def _discover_rooms(self, room_layout):
        adjacent_cells = self.game_state["minimap"].get_adjacent_cells(room_layout)

        for coordinates, minimap_cell in adjacent_cells.items():
            room_type = minimap_cell.identify()

            if room_type == "empty":
                continue

            self.game_state["game_floor"].register_room(coordinates, minimap_cell)

        print(self.game_state["game_floor"].rooms)

    def _goto_boss(self):
        self.input_controller.tap_key(" ")
        time.sleep(1)
        self.input_controller.tap_key("~")
        time.sleep(0.5)

        # self.input_controller.type_string(f"g c334")
        # self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        # self.input_controller.tap_key(self.input_controller.keyboard.up_key)
        # self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        # self.input_controller.tap_key(self.input_controller.keyboard.up_key)
        # self.input_controller.tap_key(self.input_controller.keyboard.enter_key)

        self.input_controller.tap_keys([self.input_controller.keyboard.control_key, "v"])

        self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        time.sleep(0.5)
        self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        time.sleep(0.5)
        self.input_controller.tap_key(self.input_controller.keyboard.enter_key)
        time.sleep(0.2)

    def _get_boss_health(self, game_frame):
        gray_boss_health_bar = lib.cv.extract_region_from_image(
            game_frame.grayscale_frame,
            self.game.screen_regions["HUD_BOSS_HP"]
        )

        try:
            threshold = skimage.filters.threshold_otsu(gray_boss_health_bar)
        except ValueError:
            threshold = 1

        bw_boss_health_bar = gray_boss_health_bar > threshold

        return bw_boss_health_bar[bw_boss_health_bar > 0].size

    def _is_boss_dead(self, game_frame):
        gray_boss_skull = lib.cv.extract_region_from_image(
            game_frame.grayscale_frame,
            self.game.screen_regions["HUD_BOSS_SKULL"]
        )

        if self.game_state["boss_skull_image"] is None:
            self.game_state["boss_skull_image"] = gray_boss_skull

        is_dead = False

        if skimage.measure.compare_ssim(gray_boss_skull, self.game_state["boss_skull_image"]) < 0.5:
            is_dead = True

        self.game_state["boss_skull_image"] = gray_boss_skull

        return is_dead

    def _calculate_boss_train_reward(self):
        reward = 0

        reward -= (self.game_state["health"][1] - self.game_state["health"][0]) / 6
        reward += (self.game_state["boss_health"][1] - self.game_state["boss_health"][0]) / 654

        return reward

    def _eta_on_epsilon(self, target_epsilon, epsilon_delta, timestamp_delta):
        target_epsilon_delta = (self.dqn.epsilon_greedy_q_policy.epsilon - target_epsilon)
        eta = timedelta(seconds=(timestamp_delta.seconds * target_epsilon_delta) / epsilon_delta)

        return f"{eta.days} day(s), {eta.seconds // 3600} hour(s), {(eta.seconds // 60) % 60} minutes, {eta.seconds % 60} seconds"
