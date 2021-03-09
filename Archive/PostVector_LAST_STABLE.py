# PostVector - Compatibility for Vectorworks + InteriorCAD + woodWOP + WoodScan + HHOS - By Michel Storms for Alluur and NDJ Meubelen

# Versie 1.2.0 (Major, Minor, Patch)

# TODO LIST:
# Detectie verstekken op orde zetten met juiste benamingen
# Logica extra verstekken aanmaken (wacht op Frederik, Verstek-45 & Verstek-45.3 of ???) side=11, 111, 44, ... ?
# mpr COMMENT & NC_STOP functions to communiate with Operator (IN PROGRESS)
# Aanmaak toesteken automatisch, vermoedelijk beter idee is een script in VW maken en van daaruit bedienen
# Detectie niet-te-boren ruggen verbeteren. Ideaal zou zijn pas uitvoeren als alle afmetingen kast bekend zijn...
# Afwijkingen detecteren in kastafmetingen
# Zaaglijst laden groeperen per identiek stuk
# Laden cijfers achter comma beperken
# Teller aantal lopende meter bandjes

# IMPORTS
import csv, os
import tkinter as tk
import re
from tkinter import filedialog
from random import randrange

# GLOBALS (TODO): move out of global space
debug = False
folderselection = 1 # 0=current dir / 1=dialog
zwamiDX = 400.00 # Zwaluwstaart Lade Minimum DX (komt uit globale variabelen BMG) (!!! FLOAT !!!)
projects_folder = "W:\\MP4\\IMOS\\" # Folder which holds the projects, MUST END WITH \\, ie "W:\\MP4\\IMOS\\"
miter_keyword = "Verstek" #The name VW InteriorCAD gives to miters (edgebands)
partwidth_min = 60 #Minimum machinable part width - Both Flaenge & Fbreite will be checked against it. (std60 - kantenbander)
partlength_min = partwidth_min #Same for now to stay safe with very short threaded parts
panel_oversize = 5 #Cutting oversize of panel length & width for CNC contouring, in mm. (std5)
panel_thick_def = 18.0 #Defaults to 18.0 for now, but needs better approach in CORPORA functions.

# FUNCTIONS
def main():
    # Variable Definitions
    errors = 0
    prog_counter_max = 9999 #Maximum value for prog_counter. Do not remove or optimize! DEFAULT=9999
    infoparts = { #For parts that can give info about the cabinet
        "LZ": "Zijwand_links",
        "RZ": "Zijwand_rechts",
        "BOD": "Plank_onderzijde",
        "KOP": "Plank_bovenzijde"
    }
    partnames = { #For parts that need modification / Format -> our_name: vectorworks_part_of_filename
        "rug": "Achterwand",
        "lade_bod": "lade_bodem",
        "lade_voor": "lade_voorzijde",
        "lade_achter": "lade_achterzijde",
        "lade_lz": "lade_linkerzijde",
        "lade_rz": "lade_rechterzijde",
        "lade_fout": "holzschubkasten" # Fout aangemaakte programma's beginnend met "holzschubkasten"
    }

    back_smaller = 2.0 #Back smaller than cabinet H&W, in mm. (std2.0) (for inner back detection)

    drawers = [] #A list of found drawers
    corpora = [] #A list of found cabinets

    global row_rewrite # Try to find a more elegant solution later
    prog_counter = prog_counter_max #Added at end of program name, starts with 9999 after subtraction of header iteration
    path = ""

    # Get directory and file names and report to user
    if folderselection == 0: # Get path from current directory (OLD METHOD)
        path = (os.path.dirname(os.path.realpath(__file__)))
    else: # Get path through dialog (NEW AND SHINY)
        os.system('cls' if os.name == 'nt' else 'clear') # Clear terminal
        print ("Dubbelklik op de projectmap in W:\\MP4\\IMOS\\ en bevestig:")
        root = tk.Tk()
        root.withdraw()

        while path == "": #Making sure user doesn't submit invalid path.
            path = filedialog.askdirectory(initialdir=projects_folder).replace("/", "\\")

            if path.__contains__(projects_folder) == False: #Only accept a path in the projects_folder
                path=""

    path_split = (path.split('\\')) # Get current folder
    n = len(path_split)
    current_dir = path_split[n-1]

    print ("\n\tVerwerken van Project: {}" .format(current_dir))  

    if (len(current_dir)) != 5: # Filename too short or long, try rename project with a random name.
        
        path_list = os.listdir(path.rpartition('\\')[0]) #Make directory listing of parent folder.

        path_new = "" # Try to find a unique project name.
        while path_new == "":
            current_dir_new = str(randrange(10000, 99999))

            if path_list.__contains__(current_dir_new):
                print ("PROJECT NAME ALREADY EXISTS, RETRYING")
            else:
                path_new = projects_folder + current_dir_new

        # Rename folder & CSV
        print ("\nProberen om ongeldige projectnaam ***{}*** te vervangen door ***{}***...".format(current_dir, current_dir_new))

        try:  #Renaming .csv first to make sure it exists... If it doesn't, we are dealing with an incorrect or incomplete project...
            os.rename((path + "\\" + current_dir + ".csv"), (path + "\\" + current_dir_new + ".csv"))
            os.rename(path, path_new)
        except:
            print ("\nERROR -> Ongeldige map of projectnaam onjuist en hernoemen mislukt!\n")
            print ("Verwijder map in IMOS, hernoem tekening volgens het juiste formaat en exporteer opnieuw!\n")
            input("\nDruk enter om te sluiten...\n")
            return

        current_dir = current_dir_new
        path = path_new
        path_split = (path.split('\\')) # Get current folder

    # Create logfile at current path
    log_outfile = (path + "\\BC_logfile.txt")
    log_writer = open(log_outfile, "a")

    # Open and prepare .csv files + report to user
    csv_infile = (path + "\\" + current_dir + ".csv")
    csv_outfile = (path + "\\BC_" + current_dir + ".csv")
    
    print ("\nOriginele zaaglijst: {}" .format(csv_infile))
    print ("Bewerkte zaaglijst: {}\n" .format(csv_outfile))

    with open(csv_infile, 'r') as infile, open(csv_outfile, 'a') as outfile:
        csv_reader = csv.DictReader(infile, delimiter=';')
        row_count = 0

        for row in csv_reader:
            row_rewrite = True # Rewrite this row? DEFAULT = TRUE
            cabinet_exists = False #Keep track wheter cabinet exists
            options = [] #Clear list of options for mpr_rewrite

            if row_count == 0: # Process CSV-header
                if debug: print ("\nRow {} -> Writing header: {}" .format(row_count, row))

                csv_writer = csv.DictWriter(outfile, fieldnames=row, delimiter=';', lineterminator='\n')
                csv_writer.writeheader()

            # Process CSV file
            if debug: print ("\nRow {} -> Writing line: {}" .format(row_count, row))
                
            prog_name = row["Info8"]
            
            if prog_name == "": #Sometimes VW puts the program name in the wrong column...
                prog_name = row["Info9"]
            
            part_name = prog_name #Remap this. Dirty but will get optimised later (TODO)

            prog_name_new = current_dir + "\\" + prog_name[:6] + "_" + str(prog_counter) #Alter program name
            filename_new = (prog_name_new.split('\\'))[1]
            
            cabinet_current = row["Info3"] #Get cabinet name before we overwrite this.
            
            if debug: print("cabinet_current: {}".format(cabinet_current))
            row["Info3"] = prog_name_new
            row["Info8"] = prog_name_new
            full_path_filename_old = path + "\\" + prog_name
            full_path_filename_new = path + "\\" + filename_new + ".mpr"

            for cabinet in corpora: #Build a list of cabinets, gather names and data.
                if cabinet["naam"] == cabinet_current:
                    cabinet_exists=True
                    break
            if cabinet_exists == False and cabinet_current != "":
                cabinet = {
                "naam": cabinet_current,
                "hoogte": 0.0,
                "breedte": 0.0,
                "diepte": 0.0,
                "pd_zijden": panel_thick_def, #Defaults to panel_thickness, see if we can improve detection of real value (TODO)
                "pd_bodemkop": panel_thick_def
                }
                corpora.append(cabinet)

            flaenge = float(row["FLaenge"].replace(",", ".")) #Load some non-conditional data into variables 
            fbreite = float(row["FBreite"].replace(",", "."))

            rohlaenge = flaenge + panel_oversize #Adjust raw panel dimensions
            rohbreite = fbreite + panel_oversize
            row["RohLaenge"] = str(rohlaenge).replace(".", ",")
            row["RohBreite"] = str(rohbreite).replace(".", ",")
            if debug: print ("Changed oversize to {} x {}".format(rohlaenge, rohbreite))

            if flaenge < partlength_min: #Check if part is too SHORT for machining and fix
                print("BETA: Changing part length {} to a machinable {}\n".format(flaenge, partlength_min))
                flaenge = partlength_min
                rohlaenge = flaenge + panel_oversize
                row["FLaenge"] = str(flaenge).replace(".", ",")
                row["RohLaenge"] = str(rohlaenge).replace(".", ",")

            if fbreite < partwidth_min: #Check if part is too NARROW for machining and fix
                print("BETA: Changing part width {} to a machinable {}\n".format(fbreite, partlength_min))
                fbreite = partlength_min
                rohbreite = fbreite + panel_oversize
                row["FBreite"] = str(fbreite).replace(".", ",")
                row["RohBreite"] = str(rohbreite).replace(".", ",")

            for key in row: # Check if part contains miters
                if debug: print ("key: {}".format(key))
                if row[key] == miter_keyword:
                    if debug: print ("Found miter(s), mpr tagged for rewriting.")
                    options.append("miters")
            
            for key, value in infoparts.items(): #Scan for cabinet dimension info
                if (part_name.find(value)) != -1:
                    
                    panel_thick = float(re.findall(r'\d+', row["Mat"])[0]) #Extract 1st # in string as panel thickness.

                    if {"LZ", "RZ"}.__contains__(key):
                        for item in corpora:
                            if item["naam"] == cabinet_current: #Search for current cabinet. Inefficient. (TODO): improve
                                item["pd_zijden"] = panel_thick
                        item["hoogte"] = flaenge
                        item["diepte"] = fbreite

                    if {"BOD", "KOP"}.__contains__(key):
                        for item in corpora:
                            if item["naam"] == cabinet_current: #Search for current cabinet. Inefficient. (TODO): improve
                                item["pd_bodemkop"] = panel_thick
                        item["breedte"] = flaenge+(panel_thick*2)        
                    break

            for key, value in partnames.items(): #Check if part is in dictionary of parts to be modified
                if (prog_name.find(value)) != -1:
                    if debug: print ("Found part on modify list, mpr tagged for rewriting.")
                    options.append(key)
                    break

            # Keep all IF...KEY comparisons under this line!!!
            if key == "rug": #Special options for specific key (part type). Here we disable drilling for inner backs.
                try:
                    if item["hoogte"] > (flaenge + back_smaller) and item["breedte"] > (fbreite + back_smaller):
                        options.append("rug_nodrill")
                        print ("\nBETA: Inner back possibly detected, disabled drilling.")
                except UnboundLocalError:
                    pass #No worries; back side was probably before other part, so we have no data on the cabinet yet. (TODO): Improve CORPORA

            if options == []: #No options, so just rename mpr (default)
                try:
                    if debug: print("Renaming {} to {}\n".format(full_path_filename_old, full_path_filename_new))
                    os.rename(full_path_filename_old, full_path_filename_new)
                except:
                    errormessage = ("Failed to write {} as {}" .format(path + "\\" + prog_name, path + "\\" + filename_new + ".mpr\n"))
                    print (errormessage)
                    log_writer.write(errormessage + "\n")
                    errors += 1
            else: #We have options; so Rebuild & Rewrite .mpr
                mpr_rebuild(oldfilename=full_path_filename_old, newfilename=full_path_filename_new, row=row, drawers=drawers, options=options)
         
            if row_rewrite: #Write current row to our new CSV file
                csv_writer.writerow(row)

            row_count += 1
            prog_counter -= 1

    if len(drawers) != 0: # Export the list of drawers, if any
        cutlist_drawers(path, drawers)

    # Report to user and quit
    try:
        os.rename(path + "\\" + current_dir + ".csv", path + "\\" + current_dir + ".csv.old")
    except:
        errormessage = ("Hernoemen zaaglijst .csv mislukt, doe dit manueel aub.\n")
        print (errormessage)
        log_writer.write(errormessage + "\n")
        errors += 1
    else:
        print ("Originele zaaglijst .csv hernoemd naar .old!\n")

    errormessage = ("\n {} problemen tijdens verwerking project." .format(errors))
    log_writer.write(errormessage)
    log_writer.close()

    if corpora != []: #Print which cabinets we found. (BETA)
        print ("\nBETA: Kasten gevonden:")
        for item in corpora:
            print (item)

    if drawers != []: # Print which drawers we found.
        print ("\nLaden gevonden:")
        for item in drawers:
            print (item)
        
    input("\n {} problemen tijdens verwerking project. Druk ENTER voor einde!" .format(errors))

def cutlist_drawers(path, drawers): # Convert list of drawers to a separate MANUAL (as requested) cutting list.
    # Could be changed to expport to .csv cutting list later, when we decide to cut drawers that way.
    dz1 = 15 # Plaatdikte onderdelen
    dz2 = 7 # Plaatdikte bodem
    ovm = panel_oversize # Panel oversize.
    spc = 8 # Spaces between output for string formatting
    drawers_outfile = (path + "\\Laden_Zwaluwstaart.txt") # Create logfile at current path
    d_w = open(drawers_outfile, "a")

    d_w.write("Zaaglijst zwaluwstaartladen voor project: {}\n\n".format(path))
    d_w.write("\t*** BRUTOMATEN | (dus zo te zagen) | BRUTOMATEN ***\n\n")

    for d_c in drawers: # d_c is drawer_current
        name = d_c["naam"] # Naam
        d_width = float(d_c["breedte"])
        d_depth = float(d_c["diepte"])
        d_height = float(d_c["hoogte"])
        d_w.write("Lade #{}: B={} x D={} x H={}\n".format(name, d_width, d_depth, d_height))

        drawer_to_mprx(path=path, name=name, width=d_width, depth=d_depth, height=d_height) #TESTING DRAWER MPRX GENERATION

        length = d_width + ovm # Voorstuk
        if length < zwamiDX: length=zwamiDX+ovm # Bescherming tegen te kleine lengtes
        width = d_height + ovm
        d_w.write("\tVoorstuk:   {:>{spc}}mm x {:>{spc}}mm x {:>{spc}}mm x 1 Stuk\n".format(length, width, dz1, spc=spc))
        
        length = d_width - (dz1*2) + ovm # Achterstuk
        if length < zwamiDX: length=zwamiDX+ovm # Bescherming tegen te kleine lengtes
        width = d_height -25 + ovm
        d_w.write("\tAchterstuk: {:>{spc}}mm x {:>{spc}}mm x {:>{spc}}mm x 1 Stuk\n".format(length, width, dz1, spc=spc))

        length = (d_depth * 2) + ovm # Zijstuk
        if length < zwamiDX: length=zwamiDX+ovm # Bescherming tegen te kleine lengtes
        width = d_height + ovm
        d_w.write("\tZijstuk:    {:>{spc}}mm x {:>{spc}}mm x {:>{spc}}mm x 1 Stuk\n".format(length, width, dz1, spc=spc))

        length = d_width - 20 # Bodem
        width = d_depth - 9.5
        d_w.write("\tBodem:      {:>{spc}}mm x {:>{spc}}mm x {:>{spc}}mm x 1 Stuk\n".format(length, width, dz2, spc=spc))

        d_w.write("\n")
    d_w.close() # Close cutting list

def mpr_rebuild(oldfilename, newfilename, row, drawers, options): #Rebuild .mpr file
    if debug: print("mpr_rewrite(oldfilename={}, newfilename={}, options={})".format(oldfilename, newfilename, options))
    
    global row_rewrite

    data = [] # Holds data to append to mpr file
    rewrite = True # Rewrite .mpr? Default, set to False where appropriate / DEFAULT = TRUE

    # Run over options and add relevant lines to data list.
    if options.count("miters") > 0: #Additional modifications based on ROW key data
        for key in row:
            if key == "KaVoBez" and row[key] == miter_keyword: #NEEDS TO BE "IF" insteald of "ELIF"!!! (check ALL conditions)
                print ("BETA: Verstek VOOR\n")
                data.extend(mpr_miter(side=1))   
            if key == "KaHiBez" and row[key] == miter_keyword:
                print ("BETA: Verstek ACHTER\n")
                data.extend(mpr_miter(side=2))
            if key == "KaLiBez" and row[key] == miter_keyword:
                print ("BETA: Verstek LINKS\n")
                data.extend(mpr_miter(side=3))
            if key == "KaReBez" and row[key] == miter_keyword:
                print ("BETA: Verstek RECHTS\n")
                data.extend(mpr_miter(side=4))

    if options.count("rug") > 0:
        if options.count("rug_nodrill") == 0:
            data.extend(mpr_backside())
        else:
            pass #Maybe add some kind of warning that we skipped drilling later... (TODO)

    if (   options.count("lade_bod") > 0
        or options.count("lade_voor") > 0
        or options.count("lade_lz") > 0
        or options.count("lade_achter") > 0
        or options.count("lade_rz") > 0
        or options.count("lade_fout") > 0
        ):

        row_rewrite = False # Do not rewrite row to CSV since we output drawers to a separate cutting list

        drawer_exists=False #Keep record of needing a new drawer or not.
        drawer_tempname=row["Teilbez"] # Get part name
        drawer_id = drawer_tempname.rsplit('-',1)[1] # Extract drawer ID

        for drawer_current in drawers: # Search for current drawer and check if it already exists
            if drawer_current["naam"] == drawer_id:
                drawer_exists=True
                if debug: print("Drawer exists!")
                break

        if drawer_exists==False: #Drawer not found, creating
            if debug: print("Drawer does not exist, creating...")
            drawer_new = {
            "naam": drawer_id,
            "breedte": 0,
            "diepte": 0,
            "hoogte": 0
            }
            drawers.append(drawer_new)
            drawer_current = drawers[-1]

        flaenge = row["FLaenge"].replace(",", ".") # Replace comma by point. ???RESEARCH IF NECESSARY???
        fbreite = row["FBreite"].replace(",", ".")
        
        if options.count("lade_voor") > 0: # Get width and height from part and add to drawer_current object
            drawer_current["breedte"] = float(flaenge)
            drawer_current["hoogte"] = float(fbreite)     
        
        if options.count("lade_lz") > 0: # Get depth from part and add to drawer_current object
            drawer_current["diepte"] = float(flaenge) + 15 # Add 15 for full drawer length

        if debug: print ("Current drawer: {}".format(drawer_current))

        rewrite = False # Do not rewrite, can be safely deleted for now. Later we'll construct a drawer and .mprx from the data we can gather here.!

    if rewrite: # Open mpr file and rewrite + add optional stuff in DATA, finish with a "!"" (terminator)
        infile = open(oldfilename, "r")
        outfile = open(newfilename, "w+")
        
        fl = infile.readlines()

        for line in fl: # Rewrite existing lines
            if line[:1] != "!": # Check for .mpr file terminator
                try:
                    outfile.write(line)
                except:
                    print("Failed to write to {}".format(newfilename))
                    print(line + "\n")
            else: # End of file reached (! terminator found), ignore and keep file open
                break
            
        if len(data) > 0: # Append DATA lines, if any
            for item in data:
                outfile.write(item + '\n')
            
        outfile.write('!' + '\n') # Write file terminator
            
        infile.close()
        outfile.close()

    os.remove(oldfilename) #Remove input file

def mpr_backside():
    component=(
            '<139 \\Komponente\\',
            'IN="Vectorworks\\Rug_BarCon.mpr"',
            'XA="DX/2"',
            'YA="DY/2"',
            'ZA="0.0"',
            'EM="0"',
            'VA="DX DX"',
            'VA="DY DY"',
            'VA="DZ DZ"',
            'VA="pdCorpus 18"',
            'KAT="Komponentenmakro"',
            'MNM="Rug_BarCon"',
            'ORI="1"',
            'KO="00"',
            ''
    )
    return component

def mpr_miter(side):
    component=(
        '<139 \\Komponente\\',
        'IN="Vectorworks\\Verstek_BarCon.mpr"',
        'XA="0.0"',
        'YA="0.0"',
        'ZA="0.0"',
        'EM="0"',
        'VA="DX DX"',
        'VA="DY DY"',
        'VA="DZ DZ"',
        'VA="kant {}"'.format(side), #ID kant
        'KAT="Komponentenmakro"',
        'MNM="Verstek_BarCon"',
        'ORI="1"',
        'KO="00"',
        ''
    )
    return component

def drawer_to_mprx(path, name, width, depth, height):

    deel = "1" # Test Value, (TODO): replace with routine writing a program for each part type.

    naam = str(name)
    blade = str(width)
    dlade = str(depth)
    hlade = str(height)

    infile_path = "X:\\_imosCNC\\BHX_200\\ML4\\Laden\\Zwaluwstaart\\Zwaluwstaartlade_Source.mprx"
    outfile_path = path + "\\Lade_" + naam + ".mprx"

    print(f"\nSource: {infile_path}")
    print(f"New: {outfile_path}\n")

    with open(infile_path, "r") as infile_object, open(outfile_path, "w") as outfile_object:
        
        for line in infile_object: # Replace with method that takes keyword and new value...
            if debug: print (f"Processing: {line}")

            if line.__contains__("POSTVECTOR_Deel"): # Reduce to one if for the given keyword...
                print ("Found: Deel")
                line = line.replace("POSTVECTOR_Deel", deel)
            elif line.__contains__("POSTVECTOR_Blade"):
                print ("Found: Blade")
                line = line.replace("POSTVECTOR_Blade", blade)
            elif line.__contains__("POSTVECTOR_Dlade"):
                print ("Found: Dlade")
                line = line.replace("POSTVECTOR_Dlade", dlade)
            elif line.__contains__("POSTVECTOR_Hlade"):
                print ("Found: Hlade")
                line = line.replace("POSTVECTOR_Hlade", hlade)

            outfile_object.write(line)

    infile_object.close()
    outfile_object.close()

# MAIN LOOP
if __name__ == '__main__':
    main()
