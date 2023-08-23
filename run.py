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

    def __eq__(self, other):
        if other == self.streetId:
            return True
        return False


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

    def __eq__(self, other):
        if other == self.streetId:
            return True
        return False


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


class addressWriter:
    def __init__(self, input):
        logging.info("will read file: " + input)
        inputfile = open(input, "r", encoding="ISO-8859-1")
        self.lines = inputfile.readlines()
        self.streets = []
        self.streetExceptions = []
        self.persons = []

    def parsePersons(self):
        for line in self.lines:
            # split the line so we can see the control fields
            fields = line.split()

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
                self.persons.append(newPerson)

    def parseStreets(self):
        curStreet = 0
        postCode = 0
        count = 0
        for line in self.lines:
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
                        self.streets.append(streetObj)
                        streetName = None
                        parish = None
                        town = None
                        postcode = None
                        streetObj = None
                        district = None

                    # this starts a new street section
                    curStreet = fields[2]
                    streetName = " ".join(line[12:63].split())
                    logging.debug(
                        "streetName: " + streetName + " curstreet: " + curStreet
                    )

                # All the following cases may have exceptions (house no 1 -> 2, postcode X) -
                # so for each line, call parseLineForExceptions() which will store the exception in its own dataclass if required

                case "02":
                    # postcodes live here
                    if curStreet == fields[2]:
                        postCode = self.parseLineforExceptions(
                            line=line,
                            fields=fields,
                            curStreet=curStreet,
                            fieldtype="postCode",
                        )
                case "03":
                    # parish live here
                    if curStreet == fields[2]:
                        parish = self.parseLineforExceptions(
                            line=line,
                            fields=fields,
                            curStreet=curStreet,
                            fieldtype="parish",
                        )
                case "04":
                    # town live here
                    if curStreet == fields[2]:
                        town = self.parseLineforExceptions(
                            line=line,
                            fields=fields,
                            curStreet=curStreet,
                            fieldtype="town",
                        )
                case "05":
                    # district live here
                    if curStreet == fields[2]:
                        district = self.parseLineforExceptions(
                            line=line,
                            fields=fields,
                            curStreet=curStreet,
                            fieldtype="district",
                        )

    def parseLineforExceptions(
        self, line: str, fields: list, curStreet: int, fieldtype: str
    ) -> any:
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
                    oddNumbers = False
                if not "evenNumbers" in locals():
                    evenNumbers = False

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
                    self.streetExceptions.append(newException)
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
                    self.streetExceptions.append(newException)

            else:
                value = " ".join(line[12:63].split())
                logging.debug("No exception, return the value " + value)
                return value

    def writeStreetFile(self, file) -> any:
        streetfile = open(file, "w", newline="")
        self.streetWriter = csv.writer(streetfile, dialect="excel")

        if len(self.streets) == 0:
            self.parseStreets()
        self.streetWriter.writerow(
            ["ID", "Vejnavn", "Sogn", "Postdistrikt", "By", "Flække"]
        )
        for street in self.streets:
            self.streetWriter.writerow(
                [
                    street.streetId,
                    street.streetName,
                    street.parish,
                    street.postCode,
                    street.town,
                    street.district,
                ]
            )
        logging.info("wrote " + str(len(self.streets)) + " streets to file")

    def writeStreetExceptions(self, file) -> any:
        exceptionfile = open(file, "w", newline="")
        self.exceptionWriter = csv.writer(exceptionfile, dialect="excel")

        if len(self.streetExceptions) == 0:
            self.parseStreets()

        self.exceptionWriter.writerow(
            [
                "ID",
                "Undtagelse type",
                "Værdi til undtagelse",
                "Lige numre",
                "Ulige numre",
                "FraHusNummer",
                "FraHusNummerBogstav",
                "TilHusNummer",
                "TilHusNummerBogstav",
            ]
        )
        for exception in self.streetExceptions:
            print(exception)
            self.exceptionWriter.writerow(
                [
                    exception.streetId,
                    exception.exceptionType,
                    exception.exceptionValue,
                    exception.evenNumbers,
                    exception.oddNumbers,
                    exception.exceptionFrom,
                    exception.exceptionFromSuffix,
                    exception.exceptionTo,
                    exception.exceptionToSuffix,
                ]
            )
        logging.info("wrote " + str(len(self.streetExceptions)) + " exceptions to file")

    def writePersonsCsv(self, file) -> any:
        personfile = open(file, "w", newline="")
        self.personWriter = csv.writer(personfile, dialect="excel")
        if len(self.persons) == 0:
            self.parsePersons()


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

parser = argparse.ArgumentParser(
    prog="run.py",
    usage="The -i flag is required (input file). At least one output option is required as well.",
    description="Will extract persons and streets from the KMD mainframe extract, and store as csv files, for further phonebook formatting",
    add_help=True,
)
inputs = parser.add_argument_group("Input arguments", "Required for operation")

inputs.add_argument(
    "-i", "--input", help="Input filename. The KMD .txt file", required=True
)

outputs = parser.add_argument_group(
    "Output arguments", "Specify at least one, or you're not getting any output :-)"
)
outputs.add_argument("-p", "--person", help="CSV file for outputting the person data")
outputs.add_argument("-s", "--street", help="CSV file for storing street names")
outputs.add_argument(
    "-e",
    "--exceptions",
    help="CSV file for storing street exceptions (parish, town, etc)",
)

args = parser.parse_args()

try:
    if os.path.isfile(args.input):
        convert = addressWriter(args.input)

except:
    logging.critical(
        "No inFileName provided - first argument is input-file, second argument is output-file (csv)"
    )
    logging.critical("The util will append to the file without further questions")
    exit


if args.person:
    logging.info("Will write persons to file " + args.person)
    convert.writePersonsCsv(file=args.person)
    writes = True

if args.street:
    logging.info("Will write streets to file " + args.street)
    convert.writeStreetFile(file=args.street)
    writes = True
if args.exceptions:
    logging.info("Will write exceptions to file " + args.exceptions)
    convert.writeStreetExceptions(file=args.exceptions)
    writes = True

if not "writes" in locals():
    logging.error("No output file specified - probably not what you want")
