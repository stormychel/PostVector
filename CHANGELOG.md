//  Created by Michel Storms - michelstorms@icloud.com

1.32.04: (20210309)
    - Changed paths to current client situation.

1.32.03: (20200131)
    - Fix for issue with Vectorworks naming drawer box fronts differently, resulting in invalid drawing detection.

1.32.02: (20200130)
    - Fixed exception error when selecting valid project names
    - Changed legacy BC_ prefix for .csv to PV_

1.31.02: (20200128)
    - Drawers parts now get a barcode
    - Small optimizations
    - Started progress reporting

1.30.02: (20200127)
    - Hotfix for NETTO parts that still got cut with an oversize, because of NC_STOP blocks being wrongfully counted as a machining.

1.30.01: (20200127)
    - Hotfix for wrongly-dimensioned drawers (because of VW naming them wrong). Bad drawers don't go to the cutting lists, don't get an .mpr
        and get logged to the error log

1.29.00: (20200116)
    - Handles component disabled by default (they should be done AFTER edgebanding)
    
1.28.00: (20200116)
    - Added support for custom .mpr component calls, starting with keyword defined in component_keyword and callable from all fields that are in the
        .csv file.
        Powerful function that might need some testing to get used to, and measure the usefullness...
        The default keyword is _c_ , for example _c_HAWA_120 will add a call to _c_HAWA_120.mpr to the .mpr file for that specific part.

1.27.16: (20200115)
    - Improved logging, summary (Overzicht.txt) now shows project code + project name on top
    - Small optimizations

1.25.16: (20200114)
    - Improved handling of FileNotFoundError when working with .mpr files

v1.25.15: (20200114)
    - Stopped Corpora from logging an error when panel thickness is not found and moved this to debug logging instead of error logging
    - Corpora now ignores cabinets that have "Sokkel" in their name
    
v1.25.14: (20200107) - bugfixes
    - Added some file-related exception handlers.
    
v1.25.11: (20200107)
    - Improved logging to screen, added logging to a file in the projectùs directory.

v1.24.11: (20200107)
    - Added *NETTO* to part labels of cut-to-size part that do not need machining to inform operators.

v1.23.11: (20200107)
    - Parts under a specific size (defined by partwidth_directcut / partlength_directcut) and WITHOUT cnc machinings (except for default formatting macro)
        get their cutting oversize in the .csv file disabled, and their .mpr file removed

v1.22.8: (20200106)
    - Better handling of edgeband widths

v1.21.8: (20191220)
    - Added creation of export summary (Overzicht.txt)

v1.20.8: (20191220)
    - Count edgebands and report total meters used of each type

v1.11.7: (20191220)
    - Disable all routing blocks by default and warn operator during program execution

v1.10.7: (20191219)
    - Added support for dictionary-based renaming of items
    - Started this Changelog
