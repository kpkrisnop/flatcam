# ##########################################################
# FlatCAM: 2D Post-processing for Manufacturing            #
# http://flatcam.org                                       #
# File Author: Marius Adrian Stanciu (c)                   #
# MIT Licence                                              #
# ##########################################################

from preprocessors.default import default


class default_M6_macro(default):
    """
    Identical to the default (MACH3) preprocessor but emits only T{n} + M6
    for tool changes. All retract/move/pause/spindle logic is left to the
    controller's internal M6 macro.
    """

    include_header = True
    coordinate_format = "%.*f"
    feedrate_format = '%.*f'

    def toolchange_code(self, p):
        return '\nT{tool}\nM6\n'.format(tool=int(p.tool))
