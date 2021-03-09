# Test module laden en schrijven .mprx via sjabloonbestand met gecodeerde parameters.
#   Quick&Dirty, dient als test voor implementatie in PostVector
#   Source .mprx nieuwe plaats geven in ML4 en script voorzien op CNC om laden aan te maken. (dus origineel ladenprogramma
#   ontoegankelijk maken voor gebruiker)

# (TODO):
# Folderselectie toestaan.
# Programma aanmaken per onderdeel.

import os

debug = False

deel = "1" # Test Value, (TODO): replace with routine writing a program for each part type.

naam = input("\nNaam / nummer van de lade? ")
blade = input("\nBreedte van de lade? ")
dlade = input("\nDiepte van de lade? ")
hlade = input("\nHoogte van de lade? ")

infile_path="X:\\_imosCNC\\BHX_200\\ML4\\Laden\\Zwaluwstaart\\Zwaluwstaartlade_Source.mprx"
outfile_path="X:\\_imosCNC\\BHX_200\\MP4\\Laden\\Zwaluw\\" + str(naam) + ".mprx"

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

input("\nBestand aangemaakt, druk ENTER voor einde!\n")

infile_object.close()
outfile_object.close()