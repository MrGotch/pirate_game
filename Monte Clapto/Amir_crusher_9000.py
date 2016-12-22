"""
This is an example for a bot.
"""

# Imports
from Pirates import *
import random
import copy
import math

# Class Definitions


class Action:
    """
    A class that defines an action that the bot should preform
    """
    def __init__(self, type, org, target):
        self._type = type  # type of the action
        self._org = org  # origination of the action - who does it
        self._target = target  # target of the action - to where or on who

    def get_type(self):
        """
        returns the type of the Action
        :return: type of this Action
        :rtype String
        """
        return self._type

    def get_target(self):
        """
        returns the target of the Action
        :return: target of this Action
        :rtype Location or Aircraft
        """
        return self._target

    def get_org(self):
        """
        returns the origin of the Action
        :return: origin of this Action
        :rtype Pirate
        """
        return self._org
    def print_action(self):
        """
        Return str of what an action contains. For debugging
        :return:  str containing all values of action
        """
        return str(self._type)+' '+str(self._org)+' '+str(self._target)

# Constants and global variables
N = 40  # number of trials
turns = 4  # number of turns per trial
# calculate the distance between my city an enemy city
# set half of that distance to be the distance drones should "wait" around the city
min_drone_stack = 12  # number of drones to stack until mass attack

# Function Definitions


def switch_player(game):
    """
    switches "myself" to enemy and vice-versa
    :param game:
    """
    me = game.get_myself()
    if me.id == me_id:  # if I'm original me
        me.id = enemy_id  # make me the enemy
    else:  # if Im the original enemy
        me.id = me_id  # make me myself


def handle_pirates(game, save_acts, org_game):
    """
    give command to pirates this random turn
    :param game: the game to play on
    :type game: PiratesGame
    :param save_acts: flag that tells if we should save the acts we preform (so we can do them in the real game)
    :type save_acts: boolean
    """
    actions = []
    for pirate in game.get_my_living_pirates():  # give command to each pirate
        r = random.random()  # pick a random number, r in range [0,1)
        attacked = False  # flag to check if pirate attacked or not
        if r < 0.5:  # 50% chance to attack
            can_be_attacked = []  # find and store all enemies in range of attack
            for enemy in game.get_enemy_living_aircrafts():  # loop over al enemies
                if pirate.in_attack_range(enemy):
                    can_be_attacked.append(enemy)  # add to list if in range
            if len(can_be_attacked) > 0:  # if we can attack at least one enemy
                rnd_target = random.choice(can_be_attacked)  # choose a random enemy in range
                game.attack(pirate, rnd_target)  # attack the chosen enemy
                attacked = True  # set flag to true - we just attacked
                if save_acts:
                    actions.append(Action("ATTACK", pirate, rnd_target))
        if r > 0.5 or (not attacked):  # 50% chance to move
            islands = game.get_all_islands()
            dest = random.choice(islands)  # pick a random island as destination
            sails_ops = game.get_sail_options(pirate, dest)  # find all ways to sail to the island
            if len(sails_ops) < 0:  # if we can't reach the island
                dest = game.get_my_cities()[0]  # sail to my city as a default move
                sails_ops = game.get_sail_options(pirate, dest)
            way = random.choice(sails_ops)  # choose a random way to reach the destination
            game.set_sail(pirate, way)  # sail to the chosen island in the chosen way
            if save_acts:
                actions.append(Action("MOVE", pirate, way))
    return actions


def handle_drones(game, save_acts, org_game):
    """
    give command to drones this random turn
    :param game: the game to play on
    :type game: PiratesGame
    :param save_acts: flag that tells if we should save the acts we preform (so we can do them in the real game)
    :type save_acts: boolean
    """
    num_waiting = 0  # count how many drones ware "waiting" to be satcked
    waiting = []  # save all waiting drones
    not_waiting = []  # save all not-waiting drones
    actions = []
    for drone in game.get_my_living_drones():  # count how many drones are waiting and sort them by type
        if drone.distance(game.get_my_cities()[0]) == drone_wait_dist:
            num_waiting += 1
            waiting.append(drone)
        else:
            not_waiting.append(drone)
    if num_waiting > min_drone_stack:  # if we have enough drones waiting
        for drone in waiting:  # sail them all to my city
            game.set_sail(drone, game.get_my_cities()[0])
            if save_acts:
                actions.append(Action("MOVE", drone, game.get_my_cities()[0]))
    for drone in not_waiting:  # sail all not-waiting drones to the city range
        angle = random.randrange(0, 359)  # choose a random degrees in the "circle" around the city
        loc = Location(int(drone_wait_dist * math.sin(angle)),
                       int(drone_wait_dist * math.cos(angle)))  # add a the chosen location
        ops = game.get_sail_options(drone, loc)
        way = random.choice(ops)
        game.set_sail(drone, way)
        if save_acts:
            actions.append(Action("MOVE", drone, way))
    return actions


def play_rand_turn(game, save_acts, org_game):
    """
    plays one random turn
    :param game: the game to play on
    :type game: PiratesGame
    :param save_acts: flag that tells if we should save the acts we preform (so we can do them in the real game)
    :type save_acts: boolean
    """
    turn_acts = []  # save the actions we intend to preform
    turn_acts.extend(handle_pirates(game, save_acts, org_game))  # handle pirate commands
    turn_acts.extend(handle_drones(game, save_acts, org_game))  # handle drone commands
    return turn_acts


def score_game(game):
    """
    Return the scoring for the game board given.

    Score includes:
    - dif between my score and enemy score (between -19 to 19)
    - 0.5 * (dif between my total HP and enemy total HP)
    - 2 * (dif between my islands and enemy islands) (between -2*num_of_cities to 2*num_of_cities)
    - 0.5 * (dif between my num of drones and enemy num of drones)
    - k * average distance between my drone and my city
    - (-k) * average distance between enemy drone and enemy city

    :param game
    :type game: PirateGame
    :return: score of game board
    :type: float
    """

    score = 0
    score += game.get_my_score() - game.get_enemy_score()

    # Score takes into consideration the HP difference
    my_total_hp = sum([pirate.current_health for pirate in game.get_my_living_pirates()])
    enemy_total_hp = sum([pirate.current_health for pirate in game.get_enemy_living_pirates()])
    score += 0.5 * (my_total_hp - enemy_total_hp)

    # Score takes into consideration the dif between num of islands
    score += 2 * (len(game.get_my_islands()) - len(game.get_enemy_islands()))

    # Score takes into cosideration the dif between num of drones:
    score += 0.5 * (len(game.get_my_living_drones()) - len(game.get_enemy_living_drones()))

    # Score takes into consideration the average distance between my drone and my city
    if len(game.get_my_living_drones()) > 0:
        my_drone_to_city_distances = [drone.distance(game.get_my_cities()[0]) for drone in game.get_my_living_drones()]
        score += 0.1 * (sum(my_drone_to_city_distances) / float(len(my_drone_to_city_distances)))
    if len(game.get_enemy_living_drones()) > 0:
        enemy_drone_to_city_distances =\
            [drone.distance(game.get_enemy_cities()[0]) for drone in game.get_enemy_living_drones()]
        score -= 0.1 * (sum(enemy_drone_to_city_distances) / float(len(enemy_drone_to_city_distances)))

    return score


def run_trial(game, org_game):
    """
    run a trial of 6 turns of the game
    :type game: object
    :param game: the game to play on
    :return: a list with 2 parts, the first is the score of the trial, the second is the list of actions to preform
    :type: list[int,list[Action]]
    """
    # do the first turn and save the actions
    my_action = play_rand_turn(game, True, org_game)  # play a turn, save actions
    switch_player(game)  # switch player
    # we need to do "turns" number of turns, so twice the number of plays (each turn is one me play one enemy play)
    # we did above the first turn, so we need 2*(turns-1) plays + 1 play to finish turn 1, so 2*turns-1 play
    for dummy_i in range(2*turns-1):
        play_rand_turn(game, False, org_game)  # play a turn, don't save actions
        switch_player(game)  # switch player
    score = score_game(game)  # calculate score
    return [score, my_action]


def choose_best_acts(scores, actions):
    """
    finds the best score in scores and returns the corresponding set of actions
    :param scores: list of scores of all action sets
    :type scores: list[int
    :param actions: list of all sets of actions
    :type actions: list[list[Action]]
    :return: the best action set
    :rtype: list[Action]
    """
    maxs = max(scores)  # find the best score
    idx = scores.index(maxs)  # find the index of the score
    return actions[idx]  # return the set of actions in the same index
    # (score[n] corresponds to actions[n] set of actions)


def execute_turn(best, game):
    """
    do the turn, i.e. the game calls
    :param best: the set of actions with the highest score
    :type best: ;ist[Actions]
    :param game: the game to do the commands
    :type game: PiratesGame
    """

    for act in best:  # go over all acts in set
        if act.get_type() == "MOVE":  # if a move command, move the org to target
            game.set_sail(act.get_org(), act.get_target())
        else:  # if not move -> therefore attack, make org attack target
            game.attack(act.get_org(), act.get_target())


def do_turn(game):
    """
    Makes the bot run a single turn
    :param game: the current game state
    :type game: PiratesGame
    """
    me_id = game.get_myself().id
    enemy_id = game.get_enemy().id
    drone_wait_dist = game.get_my_cities()[0].distance(game.get_enemy_cities()[0]) / 2
    global me_id  # ID of my player
    global enemy_id  # ID of enemy player
    global drone_wait_dist
    scores = []
    actions = []
    for dummy_i in range(N):  # do this N times
        cp = copy.deepcopy(game)  # copy game
        ret = run_trial(cp, game)  # run a trial
        scores.append(ret[0])  # add the score to scores
        actions.append(ret[1])  # add the actions to actions
    best = choose_best_acts(scores, actions)  # choose the best score
    execute_turn(best, game)  # do the actions
