- Projectnaam: eerste 5 LOWERCASE letters van bestandsnaam. Indien deze al bestaat beginnen met laatste positie te nummeren
    bvb: CallensKeuken wordt calle - Indien zelfde naam voorkomt wordt deze dan call0, call1, ... tot callZ (36 combinaties mogelijk)
    Wel bekijken of Upper/Lowercase invloed heeft bij scanner?

- Centraal besand bijhouden met naam van elke bronmap en conversiemap

- Originele en geconverteerde bestandsnamen bijhouden in apart logbestand PV_Files.Log (ofzoiets)

- Gecompilede versie voor gebruik op elke PC

- Meer info over voortgang geven aan gebruiker

- VW licentie met 2wop wisselen naar PC Dempsey

- Sourceprogramma laden voorzien van positionering CUPS (projectie)

- Sourcecode scannen op TODO tags en deze aanpakken

- Dringend oplossing zoeken voor veranderde optimalisatiemodus bij programma's die op buro of BMG geopend en opgeslagen werden...
    Modus moet ALTIJD deze zijn: IF _BHX THEN 31 ELSE 1 !!! DRINGEND OP TE LOSSEN !!! Eventueel controleren wat 31 doet op BMG en deze als
    default zetten in woodWOP. Config file???

- Bandje "Verdikte kant" juist behandelen. Eventueel deuvelen, alsook de uitdiklat? Of andere oplossing?
    Best voorlopig SPECIFIEKE waarschuwing geven tot we hierover iets overeen gekomen zijn.

- Herkenning voor  _P_GYPROC_BU bijprogrammeren? (ook _BI) _BU komt overeen met bewerking op NASZ

- Clamex op positie X>0 en Y0 of DY aanpakken, moet F4 of F5 worden. Aanpakken in component zelf!

- Ingefreesde bankdragers converteren van horizontale boring naar component. Best met bepaalde diameter, of symbool werken.

- Contourfrezingen: waar mogelijk kamerfrezing bijmaken voor BHX

- Panelen met DY > DX onbewerkbaar maken op BHX + operator waarschuwen.
    Dit mag minder strikt zijn, dus parameter op machine zelf voorzien om te tweaken

- CUPS rekening houden met "oversteek" van type 12. breedte veranderen OF extra functie invoegen. Dit is geen probleem voor de alu cups. Nog bezien dus.
    Kan eventueel eenvoudig aan te passen zijn door "between_Y" aan te passen als dit type cups gebruikt wordt... Echter wel opletten dat we hierdoor de alu cups niet minder nuttig maken...

- Detectie clamexen met niet-standaard orientatie, zoals bij binnenzijde voor binnenladen... Kan getest worden met retouren in TEST
    Keuken(fred).rar

- Bij berekening CUPS bevat DY soms waarde van DX. Uitzoeken waarom en oplossing zoeken.
    20191220: Op het eerste zicht nog geen duidelijke reden gevonden...
    20200115: Tot nu toe is dit probleem niet meer voorgevallen. Verder in het oog houden!

- Custom classes van DesignExpress (zie mail) toevoegen en testen.

- Reeks virtuele tools aanmaken, gekoppeld aan bepaalde VW bewerkingen zoals uitfrezen greeplijst enz. Als PV een bewerking
    met dit tool tegenkomt kan dit dan vertaald worden naar bruikbare bewerkingen.

- Rotatiefunctie maken voor stukken met DX<DY (vooral voor _BHX!)

- Foute ladeconstructie detecteren, mss op basis van DZ != 15mm?

- Afwijkingen detecteren in kastafmetingen dmv Machine Learning.

- Coriangrepen 150 (gat 0.115) en 75 (gat 0.175) herkennen en omzetten naar component
    (orientatie H of V afleiden uit positie van zijkant)
    InteriorCAD maakt hiervoor een pocket aan ipv gat, dus deze onderscheppen
    <112 \Gat\ = ID / XA="357" = center X / YA="258" = center Y
    Identificatie lengte: RD="0.12/2" = 150mm / RD="0.17/2" = 75mm / (???waarvan afgeleid???)

- In functie mpr_cups juiste DY gebruiken ipv herberekende, anders problemen met stukken die kleiner waren dan 60 maar vergoot zijn. (center zit dan op 30)

- Bij stukken die enkel passen op 1 rij smalle CUPS, calibreren met zaag ipv frees.

- Offset van 40m aanbieden met CONTROLESTOP indien stuk korter (DX) is dan 355mm. Deze maat parametriseren via Globale Variabelen.
    Dit ENKEL doen voor stukken tot DX van 315mm omdat vanaf dan 2 CUPS onmogelijk zijn.
    Bij voorkeur enkel gebruiken bij stukken met DY die te klein is voor 160mm CUP.
    Afmetingen nog eens checken met smallere CUPS omdat deze iets langer zijn!

- Globale Variabelen van _BMG uitlezen en gebruiken in script waar van toepassing.

- Extra cup in DY/2 bij stukken met DY>800mm.

- Aantal pogingen tot bereiken ongebruikt willekeurig projectnummer bijhouden en aanraden om de map op te kuisen.
    Deze melding ook in PV_Overzicht bewaren

- Systeem maken om IMOS map op te kuisen, evt adhv datums in WoodScan.log?
