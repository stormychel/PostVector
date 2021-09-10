# Created by Michel Storms - michelstorms@icloud.com
# PostVector - Compatibility for Vectorworks + InteriorCAD + woodWOP + WoodScan + HHOS

version="1.32.04" # (Major, Minor, Patch)
date="20210309" # (YYYYMMDD)

# DEBUGGING
debug=False

# IMPORTS
import csv, os
import tkinter as tk
import re
import logging
import time
from tkinter import filedialog
from random import randrange

# OPTIONS
rewrite_always = True #Always rewrite .mpr from 20200101 on, because we also scan for and correct issues --->>> !!!MUST BE SET TO TRUE!!!
clamex_drill = False #Clamex vijsgaten? Uitgeschakeld ivm BHX problemen. Later beslissen of we deze of die in component gebruiken!
add_cups = True #Add CUPS?

#VARIABLES
errors = 0 #Error counter
folderselection = 1 # 0=current dir / 1=dialog (default)
zwamiDX = 400.00 # Zwaluwstaart Lade Minimum DX (komt uit globale variabelen BMG) (!!! FLOAT !!!)
drawers_materialthickness = 15 #Materiaaldikte voor onderdelen zwaluwstaartladen. std15!!!
projects_folder = "P:\Morbi_share\_imosCNC\BHX_200\MP4\\" # Folder which holds the projects, MUST END WITH \\, ie "W:\\MP4\\IMOS\\"
temp_folder = projects_folder+"Temp\\"
miter_keyword = "Verstek" #The name VW InteriorCAD gives to miters (edgebands). Should not include <space>+<angle>!
handle_keyword = "Greeplijst" #Greeplijst aan deur, recht kantje, dan af te plakken verstek.
component_keyword = "_c_" #Component, vrij te benoemen, bvb: _c_Gyprocslag_Voor / Kant indien van toepassing bepalen in naam. (BETA_20200116)
clamex_component_name = "Lamello_4s_45.mpr" #For Clamex detection.
partwidth_min = 60 #Minimum machinable part width - Both Flaenge & Fbreite will be checked against it. (std60 - kantenbander)
partlength_min = partwidth_min #Same for now to stay safe with very short threaded parts
partwidth_directcut = 200 #Direct cutting to size under this width and when no CNC machinings are needed.
partlength_directcut = 200 #Direct cutting to size under this length and when no CNC machinings are needed.
panel_oversize = 5 #Cutting oversize of panel length & width for CNC contouring, in mm. (std5)
panel_thick_def = 18.0 #Defaults to 18.0 for now, but needs better approach in CORPORA functions.
woodcsan_maxchars = 17 #Maximum characters for Homag Woodscan filenames
control_stop = False #Can be set to True from within all functions to request operator to check PROGRAM + DRAWING before continuing. Defaults to False! (BETA)
renamable_row_items = { #Takes any word that needs to be renamed in ROW as a KEY, with its new name as VALUE (BETA)
    "Kastelement-": "K",
    "Kastelement": "K"
    #"Zijwand": "Z" # -----> Later optioneel toe te voegen na tests en in overleg met tekenburo en montage.
    #"Achterwand": "AW", -----> Ook in infoparts (main) aanpassen!!! (anders werkt CORPORA niet meer)
    #"Plank_onderzijde": "PO", -----> Eventueel infoparts houden en vertaalsysteem opstellen omdat infoparts originele namen 
    #"Plank_bovenzijde": "PB", -----> heeft en dit een voordeel kan zijn naar latere verbeteringen toe... (TODO)
    #"Onderdeel_op_maat": "OOM"
}
block_contouring = True #Block all Vectorworks contouring blocks (105)
drawers_valid = 0 #Number of valid drawers found. Starts with 0!

# SETUP LOGGING
if debug:
    log_level=logging.INFO
else: 
    log_level=logging.WARNING
log_format = "  %(message)s"
log_filename = "PV_Log.txt"

while True:
    try:
        log_handlers = [logging.FileHandler(temp_folder+log_filename), logging.StreamHandler()]
        break
    except FileNotFoundError:
        print("The temp_folder doesn not exist, creating...") #(TODO): Move this to a more common place so the whole script can benefit from it.
        os.mkdir(temp_folder)
        time.sleep(1)
        pass
logging.basicConfig(level=log_level, format=log_format, handlers=log_handlers)

# FUNCTIONS
def main():
    global errors, projects_folder, row_oversize, row_rewrite #(TODO): minimize use of globals
    
    # Variable Definitions
    prog_counter_max = 999 #Maximum value for prog_counter. Do not remove or optimize! DEFAULT=9999
    infoparts = { #For parts that can give info about the cabinet
        "LZ": "Zijwand_links",
        "RZ": "Zijwand_rechts",
        "BOD": "Plank_onderzijde",
        "KOP": "Plank_bovenzijde"
    }
    partnames = { #For parts that need modification / Format -> our_name: vectorworks_part_of_filename
        "rug": "Achterwand",
        "lade_bod": "lade_bodem",
        #"lade_voor": "lade_voorzijde", #Ignore to get rid of error where VW exports front with other number.
        "lade_achter": "lade_achterzijde",
        "lade_lz": "lade_linkerzijde",
        "lade_rz": "lade_rechterzijde",
        "lade_fout": "holzschubkasten" # Fout aangemaakte programma's beginnend met "holzschubkasten"
    }

    back_smaller = 2.0 #Back smaller than cabinet H&W, in mm. (std2.0) (for inner back detection)

    drawers = [] #A list of found drawers
    corpora = [] #A list of found cabinets
    edgebands = [] #A list of found edgeband dictionaries
    edgeband_headers = { #Dictionary of edgeband side and relevant panel dimension row header names -> side: dimension
        "KaVoBez": "FLaenge",
        "KaHiBez": "FLaenge",
        "KaLiBez": "FBreite",
        "KaReBez": "FBreite"
    }
    edgeband_waste = 50 #Waste per side on edgebanding machine.
    edgeband_ignore = ( #List of descriptions in edgebands to be ignored, to exclude stock and profiling macros. Automate gathereing of this info! (TODO)
        "_P_", #Profile macros, to be integrated later in development cycle.
        miter_keyword,
        handle_keyword 
    )

    prog_counter = prog_counter_max #Added at end of program name.
    path = ""

    # Get directory and file names and report to user
    if folderselection == 0: # Get path from current directory (OLD METHOD)
        path = (os.path.dirname(os.path.realpath(__file__)))
    else: # Get path through dialog (NEW AND SHINY)
        os.system('cls' if os.name == 'nt' else 'clear') # Clear terminal
        print ("Dubbelklik op de projectmap in W:\\MP4\\IMOS\\ en bevestig:\n")
        root = tk.Tk()
        root.withdraw()

        while path == "": #Making sure user doesn't submit invalid path.
            path = filedialog.askdirectory(initialdir=projects_folder).replace("/", "\\")

            if path.__contains__(projects_folder) == False: #Only accept a path in the projects_folder
                path=""

    #path_original = path #Keeping this for reference.

    path_split = (path.split('\\')) #Get current folder.
    n = len(path_split)
    current_dir = path_split[n-1]

    if path_split[n-2]=="Test": #If path is in Test folder, stay there and enable debugging.
        projects_folder += "Test\\"

    print ("\tVerwerken van Project: {}\n" .format(current_dir))  

    if (len(current_dir)) != 5: # Filename too short or long, try rename project with a random name.
        
        path_list = os.listdir(path.rpartition('\\')[0]) #Make directory listing of parent folder.

        path_new = "" # Try to find a unique project name.
        while path_new == "":
            current_dir_new = str(randrange(10000, 99999))

            if path_list.__contains__(current_dir_new):
                print("PROJECT NAME ALREADY EXISTS, RETRYING")
            else:
                path_new = projects_folder + current_dir_new

        # Rename folder & CSV
        print ("Proberen om ongeldige projectnaam ***{}*** te vervangen door ***{}***...\n".format(current_dir, current_dir_new))

        try:  #Renaming .csv first to make sure it exists... If it doesn't, we are dealing with an incorrect or incomplete project...
            os.rename((path + "\\" + current_dir + ".csv"), (path + "\\" + current_dir_new + ".csv"))
            os.rename(path, path_new)
        except:
            print ("\nERROR -> Ongeldige map of projectnaam onjuist en hernoemen mislukt!\n")
            print ("Verwijder map in IMOS, hernoem tekening volgens het juiste formaat en exporteer opnieuw!\n")
            input("\nDruk enter om te sluiten...\n")
            return

        current_dir_old = current_dir #Keeping this for reference.

        current_dir = current_dir_new
        path = path_new
        path_split = (path.split('\\')) # Get current folder
    else: #Filename OK, keeping it.
        current_dir_old = current_dir #No change, but we need this variable later.

    # Open and prepare .csv files + report to user
    csv_infile = (path + "\\" + current_dir + ".csv")
    csv_outfile = (path + "\\PV_" + current_dir + ".csv")
    
    print("Originele zaaglijst: {}" .format(csv_infile))
    print("Bewerkte zaaglijst: {}\n" .format(csv_outfile))

    with open(csv_infile, 'r') as infile, open(csv_outfile, 'a') as outfile:
        print("Onderdelen in zaaglijst categoriseren...\n")

        csv_reader = csv.DictReader(infile, delimiter=';')
        row_count = 0

        for row in csv_reader:
            row_rewrite = True # Rewrite this row? DEFAULT = TRUE
            row_oversize = True # DEFAULT=TRUE
            cabinet_exists = False #Keep track wheter cabinet exists
            band_exists=False #Keep track whether edgeband exists
            options = [] #Clear list of options for mpr_rewrite

            if row_count==0: #Process CSV-header
                csv_writer = csv.DictWriter(outfile, fieldnames=row, delimiter=';', lineterminator='\n')
                csv_writer.writeheader()
            
            # Process CSV file
            prog_name_original = get_progname_from_row(row) #Get original name before changing the ROW

            row = renamer(row) # Rename unwanted stuff by changing the ROW.
            
            prog_name = get_progname_from_row(row) #Get changed name from the ROW

            part_name = prog_name #Remap this. Dirty but will get optimised later (TODO)

            name_length = (woodcsan_maxchars - len(str(current_dir)) - len("\\") - len("_") - len(str(prog_counter)) ) #Calc namelength.
            prog_name_new = current_dir + "\\" + prog_name[:name_length] + "_" + str(prog_counter) #Alter program name.
            filename_new = (prog_name_new.split('\\'))[1]

            cabinet_current = row["Info3"] #Get cabinet name before we overwrite this. (needed by CORPORA)
                        
            row["Info3"] = prog_name_new
            row["Info8"] = prog_name_new
            full_path_filename_old = path + "\\" + prog_name_original
            full_path_filename_new = path + "\\" + filename_new + ".mpr"
            
            panel_thickness = find_panel_thickness(row) #Find thickness of current panel.

            for key_name, key_dimension in edgeband_headers.items(): #Build a list of used edgebands, gather data.
            
                name = row[key_name] + "_" + find_edgeband_width(panel_thickness)
                    
                length = float(row[key_dimension].replace(",", ".")) + edgeband_waste
                for band in edgebands:
                    if band["naam"] == name:
                        band_exists=True
                        band["lengte"] += length
                        break #Save some processing time.
                    else:
                        band_exists=False
                if band_exists == False and row[key_name] != "": #Using name from row to skip unnamed edgebands.
                    band = {
                    "naam": name,
                    "lengte": length
                    }
                    edgebands.append(band)

            for cabinet in corpora: #Build a list of cabinets, gather names and data.
                if cabinet["naam"] == cabinet_current:
                    cabinet_exists=True
                    break
            if cabinet_exists == False and cabinet_current != "" and cabinet_current.__contains__("Sokkel-") != True: #Ignore "Sokkel"! 
                cabinet = {
                "naam": cabinet_current,
                "hoogte": 0.0,
                "breedte": 0.0,
                "diepte": 0.0,
                "pd_zijden": panel_thick_def, #Just a placeholder now, (TODO): use find_panel_thickness(row) ???
                "pd_bodemkop": panel_thick_def
                }
                corpora.append(cabinet)

            flaenge = float(row["FLaenge"].replace(",", ".")) #Load some non-conditional data into variables 
            fbreite = float(row["FBreite"].replace(",", "."))

            rohlaenge = flaenge + panel_oversize #Adjust raw panel dimensions
            rohbreite = fbreite + panel_oversize
            row["RohLaenge"] = str(rohlaenge).replace(".", ",")
            row["RohBreite"] = str(rohbreite).replace(".", ",")

            if fbreite < partwidth_min: #Check if part is too NARROW for machining and fix. (Keep this before FLAENGE block!)
                row["Teilbez"] = (f"(B={fbreite}) " + row["Teilbez"]) #Show real width in part description.
                fbreite = partlength_min
                rohbreite = fbreite + panel_oversize
                row["FBreite"] = str(fbreite).replace(".", ",")
                row["RohBreite"] = str(rohbreite).replace(".", ",")

            if flaenge < partlength_min: #Check if part is too SHORT for machining and fix. (Keep this after FBREITE block!)
                row["Teilbez"] = (f"(L={flaenge}) " + row["Teilbez"]) #Show real length in part description.
                flaenge = partlength_min
                rohlaenge = flaenge + panel_oversize
                row["FLaenge"] = str(flaenge).replace(".", ",")
                row["RohLaenge"] = str(rohlaenge).replace(".", ",")

            if fbreite < partwidth_directcut: #Flag for checking on disabling oversize (skips CNC).
                options.append("partwidth_directcut")

            if flaenge < partlength_directcut: #Flag for checking on disabling oversize (skips CNC).
                options.append("partlength_directcut")

            if rewrite_always==True: #Check variable declaration for info.
                options.append("rewrite_always_is_true")

            if add_cups==True: #CUPS requested
                options.append("cups")

            for key in row: # Scan row for special attributes.
                if row[key].__contains__(miter_keyword):
                    options.append("miters")
                if row[key].__contains__(handle_keyword):
                    options.append("handle")
                if row[key].__contains__(component_keyword): #Add an mpr component based on a name in the .csv starting with _c_ (BETA)
                    options.append(component_keyword) #Was _c_
                    options.append(row[key])
                    logging.debug("component_keyword: " + row[key])

            for key, value in infoparts.items(): #Scan for cabinet dimension info
                if (part_name.find(value)) != -1:

                    #(TODO): replace with new function "find_panel_thickness"
                    try:
                        panel_thick = float(re.findall(r'\d+', row["Mat"])[0]) #Extract 1st # in string as panel thickness.
                    except IndexError:
                        panel_thick = 0.00
                        logging.debug(f"No panel thickness provided, defaulting to {panel_thick}!")
                        #errors+=1 #Not really an error, so stopped logging this...
                    #(TODO): replace with new function "find_panel_thickness"

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
                    options.append(key)
                    break

            # Keep all IF...KEY comparisons under this line!!!
            if key == "rug": #Special options for specific key (part type). Here we disable drilling for inner backs.
                logging.debug (f'Found "rug" (part {row["BAZPgm"]})')
                try:
                    logging.debug (str(item["hoogte"]) + " / " + str((flaenge + back_smaller)))
                    logging.debug (str(item["breedte"]) + " / " + str((fbreite + back_smaller))) 
                    if item["hoogte"] > (flaenge + back_smaller) or item["breedte"] > (fbreite + back_smaller): #normally AND
                        logging.debug("Added rug_nodrill to part options.")
                        options.append("rug_nodrill") #kv
                    logging.debug('')
                except UnboundLocalError:
                    pass #No worries; back side was probably before other part, so we have no data on the cabinet yet. (TODO): Improve CORPORA

            if options==[]: #No options, so just rename mpr (default). MS20200106: See declaration of rewrite_always for latest info on this. (TODO)
                try:
                    os.rename(full_path_filename_old, full_path_filename_new)
                except:
                    errormessage = ("Failed to write {} as {}" .format(path + "\\" + prog_name, path + "\\" + filename_new + ".mpr\n"))
                    logging.error(errormessage)
                    errors += 1
            else: #We have options; so Rebuild & Rewrite .mpr. MS20200106: See declaration of rewrite_always for latest info on this. (TODO)
                mpr_rebuild(oldfilename=full_path_filename_old, newfilename=full_path_filename_new, row=row, drawers=drawers, options=options)
         
            if row_oversize==False: #Remove oversize for this row
                logging.info("Removing oversize from current row...")
                row["RohLaenge"] = row["FLaenge"]
                row["RohBreite"] = row["FBreite"]
                row["Teilbez"] = "*NETTO* " + row["Teilbez"] #Add NETTO to label to inform operators.

            if row_rewrite: #Write current row to our new CSV file
                csv_writer.writerow(row)

            row_count += 1
            prog_counter -= 1

        if len(drawers) != 0: # Export the list of drawers, if any
            cutlist_drawers(path, drawers, csv_writer)

    # Report to user and quit
    try:
        os.rename(path + "\\" + current_dir + ".csv", path + "\\" + current_dir + ".csv.old")
    except:
        logging.error("Hernoemen zaaglijst .csv mislukt, doe dit manueel aub.\n")
        errors += 1
    else:
        print("\nOriginele zaaglijst .csv hernoemd naar .old!")

    summary_file = open(path+"\\PV_Overzicht.txt", "w")

    summary_file.write(f"\tProjectcode: {current_dir} / Projectnaam: {current_dir_old}\n\n")

    if corpora != []: #Print which cabinets we found.
        print("\nKasten gevonden:")
        summary_file.write("Kasten gevonden:\n")
        for item in corpora:
            print(item)
            summary_file.write(str(item)+"\n")
        summary_file.write("\n")

    if drawers_valid!=0: # Print which drawers we found.
        print ("\nLaden gevonden:")
        summary_file.write("Laden gevonden:\n")
        for item in drawers:
            print (item)
            summary_file.write(str(item)+"\n")
        summary_file.write("\n")

    if edgebands != []: #Print lengths of found edgebands and convert them to meters instead of millimeters.
        print ("\nBandjes gevonden:")
        summary_file.write("Bandjes gevonden:\n")
        for item in edgebands:
            item["lengte"] = int(item["lengte"]/1000)+1 #Convert this to metric meters, add 1m for safety.
            ignore=False
            for edgebandignore in edgeband_ignore: #Check if band is on ignore list.
                if item["naam"].__contains__(edgebandignore):
                    logging.debug(f"Ignored edgeband: {item}")
                    ignore=True
                    break
                else:
                    ignore=False
            if ignore==False:
                print(item)
                summary_file.write(str(item)+"\n")
        summary_file.write("\n")

    input("\n{} problemen tijdens verwerking project. Druk ENTER voor einde!\n" .format(errors))

    summary_file.close()

    logging.shutdown()
    os.rename( temp_folder+log_filename , path+"\\"+log_filename )


def cutlist_drawers(path, drawers, file): # Convert list of drawers to a separate MANUAL (as requested) cutting list.
    # Eerste test met .csv zaaglijst ok, nog verbeteren, dikte correct weergeven, juiste materiaal uit VW, barcodes...
    global drawers_valid, errors, drawers_materialthickness

    print("Laden verwerken...\n")

    project=path.split('\\')[-1]

    dz1 = drawers_materialthickness # Plaatdikte onderdelen
    dz2 = 7 # Plaatdikte bodem
    ovm = panel_oversize # Panel oversize.
    spc = 8 # Spaces between output for string formatting
    mat_bodem = "MDF-07 Eik" # (TODO): Nog uit werkelijk materiaal originele csv halen! 
    mat_lade = "MASS-15 Eik" # (TODO): Nog uit werkelijk materiaal originele csv halen! 
    drawers_outfile = (path + "\\Laden_Zwaluwstaart.txt") # Create cutting list.
    d_w = open(drawers_outfile, "a")

    d_w.write("Zaaglijst zwaluwstaartladen voor project: {}\n\n".format(path))
    d_w.write("\t*** BRUTOMATEN | (dus zo te zagen) | BRUTOMATEN ***\n\n")

    for d_c in drawers: # d_c is drawer_current
        name = d_c["naam"] # Naam
        drawer_info3 = "\\ZwLa_"+name
        d_width = float(d_c["breedte"])
        d_depth = float(d_c["diepte"])
        d_height = float(d_c["hoogte"])

        if (d_width * d_depth * d_height)!=0: #Valid drawer, add to lists and create .mpr program.
            
            drawers_valid+=1 #Found a valid drawer.

            d_w.write("Lade #{}: B={} x D={} x H={}\n".format(name, d_width, d_depth, d_height))

            drawer_to_mprx(path=path, name=drawer_info3, width=d_width, depth=d_depth, height=d_height) # Generate .mprx for current drawer

            length = d_width + ovm # Voorstuk
            if length < zwamiDX: length=zwamiDX+ovm # Bescherming tegen te kleine lengtes
            width = d_height + ovm
            d_w.write("\tVoorstuk:   {:>{spc}}mm x {:>{spc}}mm x {:>{spc}}mm x 1 Stuk\n".format(length, width, dz1, spc=spc))    

            csv_add_row(file=file,
                        Teilbez="Lade_"+name+"_V",
                        Mat=mat_lade,
                        FLaenge=length-ovm,
                        RohLaenge=length,
                        FBreite=width-ovm,
                        RohBreite=width,
                        Info3=project+drawer_info3+"_V"
                        )

            length = d_width - (dz1*2) + ovm # Achterstuk
            if length < zwamiDX: length=zwamiDX+ovm # Bescherming tegen te kleine lengtes
            width = d_height -25 + ovm
            d_w.write("\tAchterstuk: {:>{spc}}mm x {:>{spc}}mm x {:>{spc}}mm x 1 Stuk\n".format(length, width, dz1, spc=spc))

            csv_add_row(file=file,
                        Teilbez="Lade_"+name+"_A",
                        Mat=mat_lade,
                        FLaenge=length-ovm,
                        RohLaenge=length,
                        FBreite=width-ovm,
                        RohBreite=width,
                        Info3=project+drawer_info3+"_A"
                        )

            length = (d_depth * 2) + ovm # Zijstuk
            if length < zwamiDX: length=zwamiDX+ovm # Bescherming tegen te kleine lengtes
            width = d_height + ovm
            d_w.write("\tZijstuk:    {:>{spc}}mm x {:>{spc}}mm x {:>{spc}}mm x 1 Stuk\n".format(length, width, dz1, spc=spc))

            csv_add_row(file=file,
                        Teilbez="Lade_"+name+"_Z",
                        Mat=mat_lade,
                        FLaenge=length-ovm,
                        RohLaenge=length,
                        FBreite=width-ovm,
                        RohBreite=width,
                        Info3=project+drawer_info3+"_Z"
                        )

            length = d_width - 20 # Bodem
            width = d_depth - 9.5
            d_w.write("\tBodem:      {:>{spc}}mm x {:>{spc}}mm x {:>{spc}}mm x 1 Stuk\n".format(length, width, dz2, spc=spc))

            csv_add_row(file=file,
                        Teilbez="Lade_"+name+"_B",
                        Mat=mat_bodem,
                        FLaenge=length,
                        RohLaenge=length,
                        FBreite=width,
                        RohBreite=width
                        )

            d_w.write("\n")

        else: #Found an invalid drawer: log, ignore and continue!
            logging.error(f"Fout gedimensioneerde lade: {d_c}")
            errors+=1

    d_w.close() # Close cutting list

def csv_add_row(file, Mat="", Drehbar="0", KaVoBez="", KaVoTyp="",  KaVoRohdicke="", KaHiBez="",KaHiTyp="",
                KaHiRohdicke="", KaLiBez="", KaLiTyp="", KaLiRohdicke="", KaReBez="", KaReTyp="", KaReRohdicke="",
                BelagI="", BelagA="", Info1="", Info2="", Info3="", Info4="", Info5="", Info6="", Info7="",
                Info8="", Info9="", BAZPgm="", AEndDatum="", AInfo1="", AInfo2="", AInfo3="", Teilbez="",
                Stueck="1", FLaenge="", FBreite="", RohLaenge="", RohBreite=""): #Add row to referred csv file.
    csv_row={
            "Mat" : Mat,
            "Drehbar" : Drehbar,
            "KaVoBez" : KaVoBez,
            "KaVoTyp" : KaVoTyp,         
            "KaVoRohdicke" : KaVoRohdicke,
            "KaHiBez" : KaHiBez,
            "KaHiTyp" : KaHiTyp,
            "KaHiRohdicke" : KaHiRohdicke,
            "KaLiBez" : KaLiBez,
            "KaLiTyp" : KaLiTyp,
            "KaLiRohdicke" : KaLiRohdicke,
            "KaReBez" : KaReBez,
            "KaReTyp" : KaReTyp,
            "KaReRohdicke" : KaReRohdicke,
            "BelagI" : BelagI,
            "BelagA" : BelagA,
            "Info1" : Info1,
            "Info2" : Info2,
            "Info3" : Info3,
            "Info4" : Info4,
            "Info5" : Info5,
            "Info6" : Info6,
            "Info7" : Info7,
            "Info8" : Info8,
            "Info9" : Info9,
            "BAZPgm" : BAZPgm,
            "AEndDatum" : AEndDatum,
            "AInfo1" : AInfo1,
            "AInfo2" : AInfo2,
            "AInfo3" : AInfo3,
            "Teilbez" : Teilbez,
            "Stueck" : Stueck,
            "FLaenge" : FLaenge,
            "FBreite" : FBreite,
            "RohLaenge" : RohLaenge,
            "RohBreite" : RohBreite
            }
    file.writerow(csv_row)

def mpr_rebuild(oldfilename, newfilename, row, drawers, options): #Rebuild .mpr file    
    global row_rewrite, row_oversize, version, control_stop, block_contouring, errors

    data = [] # Holds data to append to mpr file
    rewrite = True # Rewrite .mpr? Default, set to False where appropriate / DEFAULT = TRUE

    # Add a comment line referring to PostVector version, marking start of machinigs added by PV.
    data.extend(mpr_comment(title="Added by PostVector v"+version+":", body=""))

    # Run over options and add relevant lines to data list.
    if options.count("cups") > 0: #Add CUPS        
        dx_calc=float(row["FLaenge"].replace(",", ".")) #Could be on data.extend line but kept separate for readability.
        dy_calc=float(row["FBreite"].replace(",", "."))
        data.extend(mpr_cups(DX=dx_calc , DY=dy_calc))
  
    data_first_block_length=len(data) #Needed to exclude this comment block when checking how many machinings .mpr file has. !!!COMES AFTER CUPS PART!!!

    # Handle rest of options, AFTER defining data_first_block_length.
    if options.count("miters") > 0: #Additional modifications based on ROW key data (TODO): Iterate instead of multiple IF!
        control_stop=True #Needs control stop to make sure miters are correctly oriented (woodgrain-related bug in Vectorworks2019)
        for key in row:
                if key == "KaVoBez" and row[key].__contains__(miter_keyword): #NEEDS TO BE "IF" insteald of "ELIF"!!! (check ALL conditions)
                    try:
                        angle = row[key].split(" ")[1]
                        data.extend(mpr_miter(side=1, angle=angle))
                    except IndexError:
                        pass #Nothing to see here, move on!
                if key == "KaHiBez" and row[key].__contains__(miter_keyword):
                    try:
                        angle = row[key].split(" ")[1]
                        data.extend(mpr_miter(side=2, angle=angle))
                    except IndexError:
                        pass #Nothing to see here, move on!
                if key == "KaLiBez" and row[key].__contains__(miter_keyword):
                    try:
                        angle = row[key].split(" ")[1]
                        data.extend(mpr_miter(side=3, angle=angle))
                    except IndexError:
                        pass #Nothing to see here, move on!
                if key == "KaReBez" and row[key].__contains__(miter_keyword):
                    try:
                        angle = row[key].split(" ")[1]
                        data.extend(mpr_miter(side=4, angle=angle))
                    except IndexError:
                        pass #Nothing to see here, move on!
                else:
                    pass

    if options.count("handle") > 0: #Additional modifications based on ROW key data (TODO): Iterate instead of multiple IF!
        control_stop=True #Needs control stop to make sure miters are correctly oriented (woodgrain-related bug in Vectorworks2019)
        for key in row:
                if key == "KaVoBez" and row[key].__contains__(handle_keyword): #NEEDS TO BE "IF" insteald of "ELIF"!!! (check ALL conditions)
                    try:
                        data.extend(mpr_handle(side=1))
                    except IndexError:
                        pass #Nothing to see here, move on!
                if key == "KaHiBez" and row[key].__contains__(handle_keyword):
                    try:
                        data.extend(mpr_handle(side=2))
                    except IndexError:
                        pass #Nothing to see here, move on!
                if key == "KaLiBez" and row[key].__contains__(handle_keyword):
                    try:
                        data.extend(mpr_handle(side=3))
                    except IndexError:
                        pass #Nothing to see here, move on!
                if key == "KaReBez" and row[key].__contains__(handle_keyword):
                    try:
                        data.extend(mpr_handle(side=4))
                    except IndexError:
                        pass #Nothing to see here, move on!
                else:
                    pass

    if options.count("rug") > 0:
        if options.count("rug_nodrill") == 0:
            data.extend(mpr_backside())
        else:
            data.extend(mpr_backside(enabled="0"))

    #Laden:
    if (   options.count("lade_bod") > 0
        #or options.count("lade_voor") > 0
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
                break

        if drawer_exists==False: #Drawer not found, creating
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
        

        #Get info from lade_achter because lade_voor gets wrongly numbered by VectorWorks sometimes... MS20200131
        #   Keep this for now until we're 100% sure this solves the problems... It could be possible that VW sometimes gives the backside a different
        #   number instead, so stay watchful... (TODO)
        #if options.count("lade_voor") > 0: # Get width and height from part and add to drawer_current object
        #    drawer_current["breedte"] = float(flaenge)
        #    drawer_current["hoogte"] = float(fbreite)     
        
        if options.count("lade_achter") > 0: # Get width and height from part and add to drawer_current object
            drawer_current["breedte"] = float(flaenge) + (drawers_materialthickness*2)  

        if options.count("lade_lz") > 0: # Get depth from part and add to drawer_current object
            drawer_current["diepte"] = float(flaenge) + drawers_materialthickness # Add drawers_materialthickness for full drawer length
            drawer_current["hoogte"] = float(fbreite) #Getting this from sides now because we skip drawer fronts because of VW naming errors. MS20200131.
            #   Also see comments above about this issue... 

        rewrite = False #Don't rewrite .mpr because we make our own program for this.

    if (options.count("partlength_directcut")>0 or options.count("partwidth_directcut")>0) and (mpr_countmachinings(oldfilename)<=1):
        #Found part that doesn't need machining.
        if len(data) == data_first_block_length: #Last check to see if no machinings were added after by us after our comment block.
            rewrite = False #Disable rewrite so we don't get a cnc program for this part.
            row_oversize = False #Disable oversizing in cutlist for this part. 

    if options.count(component_keyword)>0: #(BETA_20200116)
        for option_item in options:
            if option_item.__contains__(component_keyword) and option_item != component_keyword: #Ignore the keyword itself.
                data.extend(mpr_c_(option_item)) #Add to .mpr.

    if rewrite: # Open mpr file and rewrite + add optional stuff in DATA, finish with a "!" (terminator)
        print(oldfilename)
        print(newfilename)
        
        infile = open(oldfilename, "r")
        outfile = open(newfilename, "w+")
        
        fl = infile.readlines()

        logging.debug("-----------------------------------") #Divider between .mpr files.

        #Init variables:
        partdef_processing=False #Detected PART DEFINITION block?
        clamex_processing=False #Detected CLAMEX block?
        hole_processing=False #Detected HOLE block?
        contour_processing=False #Detected CONTOUR block?
        dx=0.00
        dy=0.00
        dz=0.00
        drill_offset=50 #Offset schroeven van center Clamex
        comment="" #Comment for additional NC_STOP triggered in certain conditions.

        # Rewrite existing lines:
        for line in fl:
            if line[:1] != "!": # Check for .mpr file terminator
                try:
                    if dx==0 and line.__contains__('DX="'): #Found DX
                        dx=float(line.split('"')[1])
                        logging.debug(f"dx={dx}")

                    if dy==0 and line.__contains__('DY="'): #Found DY
                        dy=float(line.split('"')[1])
                        logging.debug(f"dy={dy}")

                    if dz==0 and line.__contains__('DZ="'): #Found DZ
                        dz=float(line.split('"')[1])
                        logging.debug(f"dz={dz}")

                    if line.__contains__('<100 \\WerkStck\\') or line.__contains__('<100 \\Werkstuk\\'): #Found PART_DEFINITION block!
                        partdef_processing=True

                    if partdef_processing and line=="\n": #End of PART_DEFINITION block
                        if control_stop: #Control Stop requested, so adding an NC_STOP with comment for operator.
                            logging.debug(f'{newfilename}: PV_CONTROLESTOP toegevoegd (BETA)')
                            outfile.write('\n') #Add line before next component.
                            for component_line in mpr_ncstop(title="PV_CONTROLESTOP", comment="Programma & Tekening eerst controleren!"): #Add component to .mpr file for other holes.
                                    outfile.write(component_line + "\n")
                        partdef_processing=False
                        control_stop=False



                    if line.__contains__('<105 \\Konturfraesen\\'): #Found CONTOUR block (BETA)
                        contour_processing=True

                    if contour_processing and block_contouring and (line.__contains__('??=') or line=="\n"): #Disabling contouring block
                        line_old = line #We need this later on.

                        line='??="0"'
                        logging.info("Disabled CONTOURING block! (BETA)")

                        if line_old=="\n": #Line was last of block so ?? didn't exist and was created instead of modified. Ending the block now.
                            outfile.write(line) #Write ?? line first.
                            line=line_old #Re-create "last" line.
                            comment="Uitgeschakelde contourfrezing gevonden, check programma & tekening!"
                            
                    if contour_processing and line=="\n": #End of CONTOUR block
                        contour_processing=False



                    if line.__contains__('<102 \\BohrVert\\') or line.__contains__('<102 \\Verticale boring\\'): #Found HOLE block.
                        hole_processing=True

                    if hole_processing and line.__contains__('LA="0"'): #Probably found wrong drilling block
                        logging.debug(f'{newfilename}: Foute boring "LA=0" vervangen door "AN=1"')
                        line = 'AN="1"\n'

                    if hole_processing and line=="\n": #End of HOLE block
                        hole_processing=False



                    if clamex_drill: #Clamex drill holes enabled, so find and process Clamex entries. (TODO): add support for other angles!
                        logging.info("CLAMEX HOLES ENABLED (BETA)")
                        if line.__contains__(clamex_component_name): #Found CLAMEX Block
                            logging.info("Found CLAMEX!")
                            clamex_processing=True
                        
                        if clamex_processing and line.split(' ')[0]=='VA="X': #Found Clamex X Coordinate
                            clamex_x = float( (line.split(' ')[1]).split('"')[0])
                            if clamex_x==0 or clamex_x==dx: #Probably horizontal, dismiss!
                                clamex_processing=False
                            logging.info(f"\t X={clamex_x}")
                        
                        if clamex_processing and line.split(' ')[0]=='VA="Y': #Found Clamex Y Coordinate
                            clamex_y = float( (line.split(' ')[1]).split('"')[0])
                            logging.info(f"\t Y={clamex_y}")

                        if clamex_processing and line=="\n": #End of CLAMEX block.
                            logging.info("-") #Divider.
                            outfile.write('\n') #Add an empty line between component and holes.

                            #logica positie gaten Y
                            xa=clamex_x #Voorlopig gewoon op X, later rotatie toevoegen volgens Angle 1 XY_Angle
                            if clamex_y < (dy/2): #ASY side.
                                ya=clamex_y + drill_offset
                            elif clamex_y > (dy/2): #NASY side.
                                ya=clamex_y - drill_offset
                            else: #CENTERY side.
                                ya=clamex_y - drill_offset
                                for component_line in mpr_hole(xa=xa, ya=ya+(drill_offset*2)): #Add component to .mpr file for extra CENTERY hole.
                                    logging.info(component_line)
                                    outfile.write(component_line + "\n")
                                outfile.write("\n") #Extra empty line.
                            
                            for component_line in mpr_hole(xa=xa, ya=ya): #Add component to .mpr file for other holes.
                                logging.info(component_line)
                                outfile.write(component_line + "\n")

                            clamex_processing=False #Clamex done, saving some processing power until next occurence!



                    outfile.write(line) #Write line to new program.

                    if comment != "": #We have a comment, generate an NC_STOP for it.
                        for component_line in mpr_ncstop(title="PV_CONTROLESTOP", comment=comment):
                                    outfile.write(component_line + "\n")
                        comment=""


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

    try: #Remove input file
        os.remove(oldfilename)
    except FileNotFoundError:
        logging.error(f"FileNotFoundError: Could not remove {oldfilename}")
        errors+=1

def get_progname_from_row(row): #Get program name from row
    prog_name = row["Info8"]

    if prog_name == "": #Sometimes VW puts the program name in the wrong column...
        prog_name = row["Info9"]

    return prog_name

def renamer(row): #Renames unwanted names in row with wanted ones. Should be able to process a list of offenders later!
    global renamable_row_items #(TODO) move this dictionary to a separate, user-accessable config file?

    for key, value in row.items(): #Get keys and values from ROW
        if key=="Teilbez": #Never edit this key! Might bu upgraded to more keywords later.
            pass
        else:
            for replace_this, with_that in renamable_row_items.items(): #Get keys that need to be changed to their value
                if value.__contains__(replace_this):
                    row[key] = value.replace(replace_this, with_that) 
                    
                    #Add key-specific fixes here:
                    if key=="Info3" and row[key] == "K": #Fix for Kastelement that begins without a number. (Info3 field)
                        row[key] = "K0"

                    if row[key][:2] == "K_": #Fix for Kastelement that begins without a number.
                        row[key] = "K0_" + row[key][2:]

                    logging.info(f"Renamed {value} in {key} to {row[key]} (BETA)")

                    value=row[key] #Remap so we can do further checks on the modified name.

    return row

def mpr_backside(enabled="1"):
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
            f'??="{enabled}"',
            ''
    )
    return component

def mpr_miter(side, angle):
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
        'VA="hoek {}"'.format(angle.replace(",", ".")), #ID hoek
        'KAT="Komponentenmakro"',
        'MNM="Verstek_BarCon"',
        'ORI="1"',
        'KO="00"',
        ''
    )
    return component

def mpr_c_(name): #Adds a custom-named component to .mpr. Operator needs to provide the component itself!
    component=(
        '', #Starting with a new line (preferred way). (TODO) Find a way to make this uniform across functions that add to an .mpr file.
        '<139 \\Komponente\\',
        f'IN="Vectorworks\\{name}'+'.mpr"',
        'XA="0.0"',
        'YA="0.0"',
        'ZA="0.0"',
        'EM="0"',
        'VA="DX DX"',
        'VA="DY DY"',
        'VA="DZ DZ"',
        'KAT="Komponentenmakro"',
        f'MNM="{name}"',
        'ORI="1"',
        'KO="00"',
    )
    return component

def mpr_handle(side):
    component=(
        '<139 \\Komponente\\',
        'IN="Vectorworks\\Deur_Greeplijst.mpr"',
        'XA="0.0"',
        'YA="0.0"',
        'ZA="0.0"',
        'EM="0"',
        'VA="DX DX"',
        'VA="DY DY"',
        'VA="DZ DZ"',
        'VA="kant {}"'.format(side), #ID kant
        'KAT="Komponentenmakro"',
        'MNM="PV_Deur_Greeplijst_!!!NA_AFPLAKKEN!!!"',
        'ORI="1"',
        'KO="00"',
        '??="0"', #Keep disabled because this had to be done AFTER edgebanding.
        ''
    )
    return component

def mpr_ncstop(comment="", title="PV_Stop"):
    component=(
            '<117 \\NCStop\\',
            f'KM="{comment}"',
            'VL="0"',
            'XA="0"',
            'F_="30"',
            'YA="0"',
            '_Y="0"',
            '_X="0"',
            'XV="0"',
            'YV="0"',
            'WT="0.0"',
            'ZVA="1"',
            'ZV="0"',
            'ZR="1"',
            'KAT="NC-Stop"',
            f'MNM="{title}"',
            'ORI="2"',
            'KO="00"'
    )
    return component

def mpr_hole(xa=0, ya=0):
    component=(
            '<102 \\BohrVert\\',
            f'XA="{xa}"',
            f'YA="{ya}"',
            'BM="SSS"',
            'DU="4"',
            'AN="1"',
            'MI="0"',
            'S_="2"',
            'AB="0"',
            'WI="90"',
            'F_="1"',
            'ZT="0"',
            'RM="0"',
            'VW="0"',
            'HP="0"',
            'SP="0"',
            'YVE="0"',
            'WW="60,61,62,86,87,88,90,91,92,148,149,150,191,192"',
            'ASG="2"',
            'KAT="Bohren vertikal"',
            'MNM="Clamex Vijsgat"',
            'ORI="1"',
            'MX="0"',
            'MY="0"',
            'MZ="0"',
            'MXF="1"',
            'MYF="1"',
            'MZF="1"',
            'SYA="0"',
            'SYV="0"',
            'KO="00"'
    )
    return component

def mpr_comment(title="title", body="body"):
    component=(
            '<101 \\Kommentar\\',
            f'KM="{body}"',
            'KAT="Kommentar"',
            f'MNM="{title}"',
            'ORI="1"'
    )
    return component

def mpr_cups(DX=0.00, DY=0.00): #Add CUPS to .mpr
    startX = 110 #Start center X CUPS.
    side_Y = 40 #Normal CUP distance from sides.
    min_Y = 10 #Minimum CUP distance from sides.
    between_Y = 5 #Minimum distance between CUPS in Y.
    maxTssCX = 500 # Maximum tussen balken in mm.
    rest_Y=0

    cups_library = { #Available CUPS for BMG. type:width_y LAST KEY SHOULD BE: 0:999 (=no suitable cup found, so width is 0=)
    160:0,
    80:2,
    36:12,
    0:999
    }
    
    #Calculate CUP type.
    for cup_f_width in cups_library:
        for cup_b_width in cups_library:
            if (DY - (cup_f_width + between_Y + cup_b_width)) >= (side_Y * 2):
                break

        if cup_b_width==0: #If only one cup, change the rules.
            rest_Y = 0
            side_Y = min_Y
        else: #Two cups!
            rest_Y = between_Y+cup_b_width
            side_Y = side_Y

        if (DY - cup_f_width + rest_Y) >= (side_Y * 2):
            break

    logging.debug(f"Panel: {DX} x {DY}")
    logging.debug(f"Front: {cup_f_width}")
    logging.debug(f"Back : {cup_b_width}")
    logging.debug("-------------------")

    #Calculate # in X.
    DX = float(DX)
    aantalX = int((DX/maxTssCX)+1)
    if aantalX<2: aantalX=2 #Minimum 2!

    #Caclulate CUP Y position info and number of CUPS. (TODO): Add a solution for NO CUPS (NC_STOP???)
    if cup_b_width==0: #Single cup, centered in Y.
        ya1=DY/2
        ya2=0
        an=1
    else:
        ya1 = side_Y + (cup_f_width/2) #Two cups, positioned normally.
        ya2 = DY - side_Y - (cup_b_width/2)
        an=2

    ty1=cups_library[cup_f_width]
    ty2=cups_library[cup_b_width]

    component=(
            '<121 \\Block\\',
            f'XP="{startX}"',
            'YP="0.0"',
            'ZP="0.0"',
            f'AX="{aantalX}"',
            'AY="1"',
            f'RX="(DX-{startX}-{startX}) / ({aantalX}-1)"',
            'RY="0.0"',
            'CS="0"',
            'OC="0"',
            'KAT="BlockMakro"',
            'MNM="PV_CUPS"',
            'ORI="1"',
            'NM=""',
            'DP="1"',
            'KO="00"',
            '??="IF _BHX THEN 0 ELSE 1"',
            '',
            '<115 \\SaugerK\\',
            'XA="0"',
            'GR="0"',
            f'AN="{an}"',
            f'YA1="{ya1}"',
            f'YA2="{ya2}"',
            'YA3="0"',
            'YA4="0"',
            'YA5="0"',
            'YA6="0"',
            'YA7="0"',
            'YA8="0"',
            f'TY1="{ty1}"',
            f'TY2="{ty2}"',
            'TY3="0"',
            'TY4="0"',
            'TY5="0"',
            'TY6="0"',
            'TY7="0"',
            'TY8="0"',
            'WI1="0"',
            'WI2="0"',
            'WI3="0"',
            'WI4="0"',
            'WI5="0"',
            'WI6="0"',
            'WI7="0"',
            'WI8="0"',
            'TR1="_BSZ"',
            'TR2="_BSZ"',
            'TR3="_BSZ"',
            'TR4="_BSZ"',
            'TR5="_BSZ"',
            'TR6="_BSZ"',
            'TR7="_BSZ"',
            'TR8="_BSZ"',
            'W11="0.0"',
            'W12="0.0"',
            'W13="0.0"',
            'W14="0.0"',
            'W15="0.0"',
            'W16="0.0"',
            'W17="0.0"',
            'W18="0.0"',
            'VA1="1"',
            'VA2="1"',
            'VA3="0"',
            'VA4="0"',
            'VA5="0"',
            'VA6="0"',
            'VA7="0"',
            'VA8="0"',
            'GA="0"',
            'KAT="Konsole"',
            'MNM="Spanmiddelen op console"',
            'ORI="2"',
            'KO="00"'
    )

    return component

def mpr_countmachinings(filename): #Return number of machinings in .mpr file
    global errors
    machining_count=0
    try:
        infile = open(filename, "r")

        fl = infile.readlines()

        for line in fl:
            if line[0] == "<": #Found a block, analyze and count.
                try: #Try to get block code and check if it's a machining.
                    if int(line[1:4]) > 101 and int(line[1:4]) != 117: #Ignore COMMENT and NC_STOP!
                        machining_count+=1
                except ValueError:
                    print(f"\nValueError (non-numeric block code)in mpr_countmachinings(), filename={filename}, line={line} ")
                    errors+=1
    except FileNotFoundError:
        logging.error(f"FileNotFoundError: Could not open {filename}")
        errors+=1

    return machining_count

def drawer_to_mprx(path, name, width, depth, height):

    deel = 1 #Start with part 1 (sidewalls)
    deel_naam = ( #Tuple with correct drawer part names (TODO: Move to top of code??? Conventions???)
        "_",
        "Z",
        "V",
        "A"
    )

    naam = str(name)
    blade = str(width)
    dlade = str(depth)
    hlade = str(height)

    while deel != 4: #Write a program for part# 1-3
        # infile_path = "P:\\_imosCNC\\BHX_200\\ML4\\Laden\\Zwaluwstaart\\Zwaluwstaartlade_Source.mprx"
        
        infile_path = "P:\\Morbi_share\\_imosCNC\\BHX_200\\ML4\\Laden\\Zwaluwstaart\\Zwaluwstaartlade_Source.mprx"


        outfile_path = path + "\\" + naam + "_" + str(deel_naam[deel]) + ".mprx"

        with open(infile_path, "r") as infile_object, open(outfile_path, "w") as outfile_object:
            
            for line in infile_object: # Replace with method that takes keyword and new value...
                if line.__contains__("POSTVECTOR_Deel"): # Reduce to one if for the given keyword...
                    line = line.replace("POSTVECTOR_Deel", str(deel))
                elif line.__contains__("POSTVECTOR_Blade"):
                    line = line.replace("POSTVECTOR_Blade", blade)
                elif line.__contains__("POSTVECTOR_Dlade"):
                    line = line.replace("POSTVECTOR_Dlade", dlade)
                elif line.__contains__("POSTVECTOR_Hlade"):
                    line = line.replace("POSTVECTOR_Hlade", hlade)

                outfile_object.write(line)

        infile_object.close()
        outfile_object.close()
        deel+=1

def find_panel_thickness(row):
    global errors
    try:
        panel_thick = float(re.findall(r'\d+', row["Mat"])[0]) #Extract 1st # in string as panel thickness.
    except IndexError:
        panel_thick = 0.00
        logging.debug(f"No panel thickness provided, defaulting to {panel_thick}!")
        #errors+=1 #Not really an error, so disabled logging this.

    return panel_thick

def find_edgeband_width(thick): #Find a fitting edgeband width for panel thickness. Returns a string.
    min_oversize=4 #Minimum oversize vs panel thickness.
    bands=( #Available band widths
        23,
        33,
        43,
        54
    )
    for width in bands:
        if thick + min_oversize <= width:
            return str(width)

    return "+++" + str(width) + "+++" #No suitable width found, so communicate this to user.

# MAIN LOOP
if __name__ == '__main__':
    main()
