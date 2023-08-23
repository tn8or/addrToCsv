import sys, os, logging, csv, json, argparse
from dataclasses import dataclass


@dataclass
class street:
    streetId: int
    streetName: str
    parish: str = None
    postCode: str = None
    town: str = None
    district: str = None


@dataclass
class streetexception:
    streetId: int
    exceptionType: str
    exceptionValue: str
    evenNumbers: bool
    oddNumbers: bool
    exceptionFrom: int = None
    exceptionFromSuffix: str = None
    exceptionTo: int = None
    exceptionToSuffix: str = None


@dataclass
class person:
    streetId: int
    streetNo: int
    streetNoSuffix: str
    floor: str
    door: str
    firstName: str
    lastName: str
    occupation: str
    careOf: str


streets = []
streetExceptions = []
persons = []


def parsePersons(Lines):
    global persons
    # Strips the newline character
    for line in Lines:
        # split the line so we can see the control fields
        fields = line.split()
        # print(fields)
        # if fields[0] == "00":
        #    logging.info("New street found with id: " + fields[2])

        if fields[0] == "07":
            streetId = fields[1]
            lastName = " ".join(line[35:61].split())
            firstName = " ".join(line[61:99].split())
            occupation = " ".join(line[99:114].split())
            careOf = " ".join(line[114:160].split())
            streetNo = line[8:11]
            floor = line[15:17].lower()
            door = line[20:22].lower()
            streetNoSuffix = line[12].upper()

            logging.debug(
                "We've got a live one! "
                + "streetid"
                + streetId
                + " houseNo "
                + streetNo
                + " suffix: "
                + streetNoSuffix
                + " lastName: "
                + lastName
                + " firstName: "
                + firstName
                + " occupation: "
                + occupation
                + " careof: "
                + careOf
            )
            newPerson = person(
                streetId=streetId,
                streetNo=streetNo,
                streetNoSuffix=streetNoSuffix,
                floor=floor,
                door=door,
                firstName=firstName,
                lastName=lastName,
                occupation=occupation,
                careOf=careOf,
            )
            persons.append(newPerson)


def parseStreets(Lines: list) -> any:
    curStreet = 0
    postCode = 0
    count = 0
    global streets
    for line in Lines:
        # for now, just stop after 4 streets
        if count > 4:
            break
        fields = line.split()
        match fields[0]:
            case "00":
                count += 1
                if count > 1:
                    # If this is not the first iteration, lets store the data.
                    # We start a new street-gathering routine every time field 0 is "00",
                    # designating the start of a new object
                    # store the last street before we move on - we're at the next one
                    streetObj = street(
                        streetId=curStreet,
                        streetName=streetName,
                        postCode=postCode,
                        parish=parish,
                        town=town,
                        district=district,
                    )
                    streets.append(streetObj)
                    streetName = None
                    parish = None
                    town = None
                    postcode = None
                    streetObj = None
                    district = None

                # this starts a new street section
                curStreet = fields[2]
                streetName = " ".join(line[12:63].split())
                logging.debug("streetName: " + streetName + " curstreet: " + curStreet)

            # All the following cases may have exceptions (house no 1 -> 2, postcode X) -
            # so for each line, call parseLineForExceptions() which will store the exception in its own dataclass if required

            case "02":
                # postcodes live here
                if curStreet == fields[2]:
                    postCode = parseLineforExceptions(
                        line=line,
                        fields=fields,
                        curStreet=curStreet,
                        fieldtype="postCode",
                    )
            case "03":
                # parish live here
                if curStreet == fields[2]:
                    parish = parseLineforExceptions(
                        line=line,
                        fields=fields,
                        curStreet=curStreet,
                        fieldtype="parish",
                    )
            case "04":
                # town live here
                if curStreet == fields[2]:
                    town = parseLineforExceptions(
                        line=line, fields=fields, curStreet=curStreet, fieldtype="town"
                    )
            case "05":
                # district live here
                if curStreet == fields[2]:
                    district = parseLineforExceptions(
                        line=line,
                        fields=fields,
                        curStreet=curStreet,
                        fieldtype="district",
                    )


def parseLineforExceptions(
    line: str, fields: list, curStreet: int, fieldtype: str
) -> any:
    global streetExceptions
    if len(fields) >= 5:
        if fields[4] == "nr":
            logging.debug("exception found " + line)

            # is this even or uneven numbers?
            if line[12:17] == "Ulige":
                oddNumbers = True
            elif line[12:16] == "Lige":
                evenNumbers = True
            else:
                logging.error("Wasn't an even or odd number, bailing out")
                quit()

            # set even or odd numbers to zero if not defined
            if not "oddNumbers" in locals():
                oddNumbers = 0
            if not "evenNumbers" in locals():
                evenNumbers = 0

            # check if there's a hyphen in position 26 - then its a range of numbers
            if line[25] == "-":
                logging.debug("Hyphen found! - its a range")
                exceptionFrom = line[21:24]
                exceptionFromSuffix = line[24]
                exceptionTo = line[26:29]
                exceptionToSuffix = line[29]
                exceptionValue = " ".join(line[31:61].split())

                # we have constructed our exception, lets push it
                newException = streetexception(
                    streetId=curStreet,
                    exceptionType=fieldtype,
                    exceptionValue=exceptionValue,
                    exceptionFrom=exceptionFrom,
                    exceptionFromSuffix=exceptionFromSuffix,
                    exceptionTo=exceptionTo,
                    exceptionToSuffix=exceptionToSuffix,
                    oddNumbers=oddNumbers,
                    evenNumbers=evenNumbers,
                )
                streetExceptions.append(newException)
            else:
                # no range, the value payload will have moved
                exceptionValue = " ".join(line[21:61].split())
                # we have constructed our exception, lets push it
                newException = streetexception(
                    streetId=curStreet,
                    exceptionType=fieldtype,
                    exceptionValue=exceptionValue,
                    oddNumbers=oddNumbers,
                    evenNumbers=evenNumbers,
                )
                streetExceptions.append(newException)

        else:
            value = " ".join(line[12:63].split())
            logging.debug("No exception, return the value " + value)
            return value


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

parser = argparse.ArgumentParser(
    prog="extract persons and streets from KMD .txt extract, for phonebook",
    description="Will extract persons and streets from the KMD mainframe extract, and store as csv files, for further phonebook formatting",
)
parser.add_argument("-i", "--input", help="Input filename. The KMD .txt file")
parser.add_argument("-p", "--person", help="CSV file for outputting the person data")
parser.add_argument("-s", "--street", help="CSV file for storing street names")

args = parser.parse_args()

try:
    if os.path.isfile(args.input):
        logging.info("Will read file " + args.input)
        logging.info("Will write persons to file " + args.person)
        logging.info("Will write streets to file " + args.street)

except:
    logging.critical(
        "No inFileName provided - first argument is input-file, second argument is output-file (csv)"
    )
    logging.critical("The util will append to the file without further questions")
    exit

inputfile = open(args.input, "r", encoding="ISO-8859-1")
personfile = open(args.person, "w", newline="")
personwriter = csv.writer(personfile)
streetfile = open(args.person, "w", newline="")
streetriter = csv.writer(streetfile)

Lines = inputfile.readlines()

parseStreets(Lines)
parsePersons(Lines)
