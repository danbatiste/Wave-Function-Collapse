## Wave-Function-Collapse

Wave-Function-Collapse is a Python library for generating patterns from a given set of rules. It is based on the Wave Function Collapse algorithm developed by [Marius Watz](https://github.com/mxgmn/WaveFunctionCollapse).

### Usage

The Wave-Function-Collapse library can be used to generate patterns from a given set of rules. It is composed of two main functions: `rules_from_array` and `collapse`. 

#### `rules_from_array`

The `rules_from_array` function takes an array of elements, a radius, and a number of dimensions as its parameters. It creates a list of unique elements and a dictionary of weights for each element. It then iterates over each element in the array and creates rules for each element. For each element, it looks in each of the unit directions (and their inverse) up to the given radius, and adds the elements in those directions to the rules for the element. The function then returns the dictionary of rules.

#### `collapse`

The `collapse` function takes in the canvas, a location, and a rules dictionary, and applies the rules to the canvas at the given location, either randomly choosing a character from the cell's possibilities or using a given character. This code is used to collapse a canvas into a single image based on given rules.

The `get_rules` and `collapse` functions are used to generate and apply rules to a canvas in order to collapse it. The `randomcollapse` function randomly collapses a single cell in the canvas given a rules dictionary and an optional character. The `entropy_collapse` function collapses the lowest entropy cell in the canvas given a rules dictionary and an optional character. The `is_collapsed` function is used to check if the canvas has been completely collapsed.

The code also contains functions for loading an input array from a given image, creating a canvas of uncollapsed cells from the unique characters in the array, and collapsing each cell until the entire thing is collapsed. It then converts the result to an image, resizes it, and saves and displays it.

### Example

Here is an example of how to use the Wave-Function-Collapse library to generate a pattern from a given set of rules.

```python
import wavefunction

# Load input image
input_image = "input.jpg"
input_array = wavefunction.load_image(input_image)

# Get rules from array
radius = 2
rulesdict = wavefunction.rules_from_array(input_array, radius)

# Initialize canvas
canvas = wavefunction.np.full(input_array.shape, wavefunction.frozenset(rulesdict.keys()))

# Collapse canvas
while not wavefunction.is_collapsed(canvas):
    wavefunction.entropy_collapse(canvas, rulesdict)

# Convert canvas to image
img = wavefunction.Image.fromarray(canvas.astype(wavefunction.np.uint8))

# Resize image
img = img.transform((input_array.shape[1], input_array.shape[0]), wavefunction.Image.AFFINE, (1, 0, 0, 0, 1, 0))

# Save image
img.save("output.jpg")
```

This code will generate a pattern from the given input image and save it to output.jpg.