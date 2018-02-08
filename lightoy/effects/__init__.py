from lightoy.effects.effect import Effect

from lightoy.effects.misc import *

from lightoy.effects.cylinder import Cylinder
from lightoy.effects.wander import Wander
from lightoy.effects.wavy import Wavy


def create_effects(num_leds):
    """Returns an {effect name => initialized effect} dict.
    """
    all_effect_classes = Effect.__subclasses__()
    return {
        effect_class.__name__: effect_class(num_leds)
        for effect_class in all_effect_classes
        }
