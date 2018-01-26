from effects.effect import Effect

from effects.misc import *

from effects.cylinder import Cylinder
from effects.wander import Wander
from effects.wavy import Wavy


def create_effects(num_leds):
    """Returns an {effect name => initialized effect} dict.
    """
    all_effect_classes = Effect.__subclasses__()
    return {
        effect_class.__name__: effect_class(num_leds)
        for effect_class in all_effect_classes
        }
