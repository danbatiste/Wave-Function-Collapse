import numpy as np
from PIL import Image
import random as rand
import cv2
from PIL import Image, ImageTransform
from pprint import pprint
from functools import lru_cache
import time


# Unit directions
RIGHT = np.array([1, 0])
DOWN = np.array([0, 1])

# Custom error
class ContradictionError(Exception):
    pass

def rules_from_array(arr, radius=1, dims=2):
    flattened_arr = list(arr.reshape((np.prod(arr.shape))))
    elements = np.unique(arr)
    weights = {e : flattened_arr.count(e) for e in elements}

    # rule set, does not allow duplicates
    rules = dict()
    rules.update({"weights" : weights})

    height, width = arr.shape[0], arr.shape[1]
    unit_directions = [RIGHT, DOWN, RIGHT + DOWN, RIGHT - DOWN] # unit directions; backwards is taken care of automatically
    reverse_unit_directions = [-u for u in unit_directions]
    unit_directions.extend(reverse_unit_directions)

    # rules = {
    #    1 : {
    #       (-1, -1) : {1, 0},
    #       (-1, 0) : {0},
    # }
    #    0 : {
    #      (-1, 0) : {1},
    # }
    # }

    # Get all horizontal
    for j in range(height):
        for i in range(width):
            element = arr[j][i]
            if not element in rules:
                rules.update({element : dict()}) # Make sure there is a dictionary entry for the element
            # Get rules (and inverse rules) for each unit direction (and inverse direction)
            for jdistance in range(1, radius+1): # Iterate over all distances from 1 to radius, inclusive.
                for idistance in range(1, radius+1):
                    for UNIT_DIRECTION in unit_directions:
                        DIRECTION = UNIT_DIRECTION*np.array([idistance, jdistance])
                        REVERSE_DIRECTION = -DIRECTION
                        DIRECTION, REVERSE_DIRECTION = tuple(DIRECTION), tuple(REVERSE_DIRECTION) # Convert to tuples to make compatible with dictionary
                        if (-1 < i+DIRECTION[0] < width) and (-1 < j+DIRECTION[1] < height):
                            # Make sure there is a dictionary entry for the direction
                            if not DIRECTION in rules[element]:
                                rules[element].update({DIRECTION : frozenset()})
                            
                            # Get direction's rule
                            neighbor = arr[j+DIRECTION[1]][i+DIRECTION[0]] # for radius > 1, TODO: implement getting all neighbors between i and i+radius
                            rules[element][DIRECTION] = rules[element][DIRECTION].union({neighbor})

                            # Get inverse (for the neighbor)
                            if not neighbor in rules:
                                rules.update({neighbor : dict()})
                            if not REVERSE_DIRECTION in rules[neighbor]:
                                rules[neighbor].update({REVERSE_DIRECTION : frozenset()})
                            rules[neighbor][REVERSE_DIRECTION] = rules[neighbor][REVERSE_DIRECTION].union({element})
    return rules


def collapse(canvas, loc, rulesdict, character=None):
    i, j = loc
    # If the cell we are trying to collapse has already been collapsed, raise an error
    if not (type(canvas[j][i]) == type(frozenset())):
        raise NotADirectoryError
    # Default behavior: no character chosen, so pick one from the cell's possibilities
    if character is None:
        canvas[j][i] = rand.choice(list(canvas[j][i]))
        character = canvas[j][i]
    # If a character has been chosen:
    else:
        if character not in list(canvas[j][i]):
            print("Collapse not possible!", character)
            raise BufferError
        canvas[j][i] = character

    height, width = len(canvas), len(canvas[0])
    rules = rulesdict[character]
    # Go to all neighbors and check off possibilities
    for direction, possible_character_set in rules.items():
        # Get neighbor's location
        neighbor_loc = (i + direction[0], j + direction[1])
        if neighbor_loc == loc:
            continue
        # Check if out of bounds
        if not ((-1 < i+direction[0] < width) and (-1 < j+direction[1] < height)):
            #print((i, j), "+", direction, "=", neighbor_loc, "OUT OF BOUNDS")
            continue # Skip this rule if out of bounds
        neighbor = canvas[neighbor_loc[1]][neighbor_loc[0]]
        # If neighbor is a character:
        if type(neighbor) not in [type(set()), type(frozenset())]:
            if neighbor not in possible_character_set:
                print("Contradiction!")
                raise ContradictionError
            continue # Cell already collapsed, skip this.
        elif type(neighbor) in [type(set()), type(frozenset())]:
            remaining_possible_characters = possible_character_set.intersection(neighbor)
            if len(remaining_possible_characters) == 0:
                print("Contradiction!")
                raise ContradictionError
            elif len(remaining_possible_characters) == 1: # Collapse neighbor
                canvas = collapse(canvas, neighbor_loc, rulesdict, list(remaining_possible_characters)[0])
                #canvas[neighbor_loc[1]][neighbor_loc[0]] = list(remaining_possible_characters)[0]
                continue
            else:
                canvas[neighbor_loc[1]][neighbor_loc[0]] = remaining_possible_characters
        else:
            print("Unknown error")
            raise ZeroDivisionError
    return canvas

def is_collapsed(canvas):
    for j in range(len(canvas)):
        for i in range(len(canvas[0])):
            if type(canvas[j][i]) == frozenset:
                return False
    return True

# Randomly collapse a cell.
def randomcollapse(canvas, rulesdict, character=None):
    possible_coords = []
    for j in range(len(canvas)):
        for i in range(len(canvas[0])):
            if type(canvas[j][i]) == type(frozenset()):
                possible_coords.append((i, j))
    next_coords = rand.choice(possible_coords)
    return collapse(canvas, next_coords, rulesdict, character=character)


# Collapse the lowest entropy cell
def entropy_collapse(canvas, rulesdict, character=None):
    next_coords, _ = get_lowest_entropy(canvas, rulesdict)
    return collapse(canvas, next_coords, rulesdict, character=character)


# Calculate the entropy of a set of possibilities
@lru_cache(maxsize=10000)
def shannon_entropy(weight_list):
    # Entropy formula
    a = np.log(sum(weight_list))
    b = sum([w * np.log(w) for w in weight_list])
    c = sum(weight_list)
    entropy = a - (b/c)
    return entropy

# Gets the coords of the cell with the lowest entropy. If multiple, randomly choose.
def get_lowest_entropy(canvas, rulesdict):
    min_entropy = 10000000000
    coords = []
    weights = rulesdict["weights"]
    # Search through and find cell w lowest entropy
    for j in range(len(canvas)):
        for i in range(len(canvas[0])):
            possibilities = canvas[j][i]
            # if already collapsed, skip
            if not type(possibilities) == frozenset:
                continue
            # generate list of weights
            weight_list = []
            for outcome in possibilities:
                weight_list.append(weights[outcome])
            # Get the entropy
            entropy = shannon_entropy(tuple(weight_list))
            # Figure out if you should store cell's location
            if entropy < min_entropy:
                min_entropy = entropy
                coords = [(i, j)]
            if entropy == min_entropy:
                coords.append((i, j))
    return rand.choice(coords), min_entropy

# Loads an image into an array of tuples
def load_image(path):
    img = Image.open(path)
    img_array = np.array(img)
    input_list = [[tuple(rgb) for rgb in row] for row in img_array]
    shape = (len(input_list), len(input_list[0]))
    input_array = np.empty(shape, object)
    input_array[...] = input_list
    return input_array


# main program
if __name__ == "__main__":
    input_array = np.array([
        [1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1],
        [1, 1, 0, 1, 1],
        [1, 0, 7, 0, 1],
        [0, 7, 7, 7, 0],
    ])

    # Load the input img or array
    input_array = load_image("1658243361.jpg")
    print(input_array, input_array.shape)
    radius = 1
    rules = rules_from_array(input_array, radius=radius)
    
    # Get all characters and create the canvas of uncollapsed cells
    characters = frozenset(np.unique(input_array))
    shape = (10, 10) # shape of extended array
    canvas = np.full(shape, characters) # initialize array of sets of possible characters

    # collapse cell by cell until entire thing is collapsed
    last_canvas = canvas
    while not is_collapsed(canvas):
        last_canvas = canvas
        try:
            canvas = entropy_collapse(canvas, rules)
        except ContradictionError:
            canvas = last_canvas

    canvas = np.array(canvas) # convert tuples to arrays
    img = Image.fromarray(canvas)
    img = img.convert("RGB")
    img = img.resize(np.array(canvas.shape)*20, Image.Transform.AFFINE)
    img.save(str(int(time.time())) + ".jpg")
    img.show()

