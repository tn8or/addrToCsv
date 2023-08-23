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
                streetNo = line[8:11].strip()
                floor = line[15:17].lower().strip()
                door = line[20:22].lower().strip()
                streetNoSuffix = line[12].upper().strip()

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
                    streetId=int(streetId),
                    streetNo=int(streetNo),
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
                            streetId=int(curStreet),
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
        # write the last street to file, even though we're out of the loop
        streetObj = street(
            streetId=int(curStreet),
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

    def parseLineforExceptions(
        self, line: str, fields: list, curStreet: int, fieldtype: str
    ) -> any:
        if len(fields) >= 5:
            if fields[4] == "nr":
                logging.debug("exception found " + line)

                # set isRange to false, so we can reset it if the try-clause below fails
                isRange = False
                # is this even or uneven numbers?
                if line[12:17] == "Ulige":
                    pass
                elif line[12:16] == "Lige":
                    evenNumbers = True
                else:
                    logging.error("Wasn't an even or odd number, bailing out")
                    quit()

                # set even or odd numbers to zero if not defined
                if not "evenNumbers" in locals():
                    evenNumbers = False

                # check if there's a hyphen in position 26 - then its a range of numbers
                try:
                    if int("".join(line[21:24].split())) and int(
                        "".join(line[26:29].split())
                    ):
                        logging.debug(
                            "We have from- and to- streetnumbers - its a range!"
                        )
                        logging.debug(line)
                        exceptionFrom = int("".join(line[21:24].split()))
                        exceptionFromSuffix = line[24]
                        exceptionTo = int("".join(line[26:29].split()))
                        exceptionToSuffix = line[29]
                        exceptionValue = " ".join(line[31:61].split())

                        # we have constructed our exception, lets push it
                        newException = streetexception(
                            streetId=int(curStreet),
                            exceptionType=fieldtype,
                            exceptionValue=exceptionValue,
                            exceptionFrom=exceptionFrom,
                            exceptionFromSuffix=exceptionFromSuffix,
                            exceptionTo=exceptionTo,
                            exceptionToSuffix=exceptionToSuffix,
                            evenNumbers=evenNumbers,
                        )
                        self.streetExceptions.append(newException)
                        isRange = True
                except:
                    pass
                if isRange == False:
                    # no range, the value payload will have moved
                    exceptionValue = " ".join(line[21:61].split())
                    # we have constructed our exception, lets push it
                    newException = streetexception(
                        streetId=int(curStreet),
                        exceptionType=fieldtype,
                        exceptionValue=exceptionValue,
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
                "FraHusNummer",
                "FraHusNummerBogstav",
                "TilHusNummer",
                "TilHusNummerBogstav",
            ]
        )
        for exception in self.streetExceptions:
            logging.debug(exception)
            self.exceptionWriter.writerow(
                [
                    exception.streetId,
                    exception.exceptionType,
                    exception.exceptionValue,
                    exception.evenNumbers,
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
        self.personWriter.writerow(
            [
                "Efternavn",
                "Fornavne",
                "Beskæftigelse",
                "careOf",
                "Vejnavn",
                "Husnr",
                "etageDør",
                "PostnrBy",
                "Flække",
                "By",
                "sogn",
            ]
        )
        for person in self.persons:
            writePerson = {
                "lastName": person.lastName,
                "firstName": person.firstName,
                "occupation": person.occupation,
                "careOf": person.careOf,
                "streetNo": person.streetNo,
                "streetNoSuffix": person.streetNoSuffix,
                "floor": person.floor,
                "door": person.door,
            }
            self.findStreetAndException(person=person, writePerson=writePerson)
            logging.debug(person)
            logging.info(writePerson)
            if len(writePerson) < 5:
                logging.error("No street info found, exiting for person:")
                logging.error(writePerson)
                logging.error(person)
                quit()

            self.personWriter.writerow(
                [
                    writePerson["lastName"],
                    writePerson["firstName"],
                    writePerson["occupation"],
                    writePerson["careOf"],
                    writePerson["streetName"],
                    str(writePerson["streetNo"]) + str(writePerson["streetNoSuffix"]),
                    str(writePerson["floor"]) + str(writePerson["door"]),
                    writePerson["postCode"],
                    writePerson["district"],
                    writePerson["town"],
                    writePerson["parish"],
                ]
            )
        logging.info("wrote " + str(len(self.persons)) + " persons to file")

    def findStreetAndException(self, person, writePerson):
        if len(self.streetExceptions) == 0:
            self.parseStreets()
        for street in self.streets:
            if street == person.streetId:
                logging.debug("found street " + str(street))
                writePerson["streetName"] = street.streetName
                writePerson["postCode"] = street.postCode
                writePerson["town"] = street.town
                writePerson["parish"] = street.parish
                writePerson["district"] = street.district

        ## go searching through exceptions to see if we have an override
        for exception in self.streetExceptions:
            # Lets not declare exception before we've verified it
            exceptionMatch = False
            if exception == person.streetId:
                logging.info(
                    "maybe found exception? \n"
                    + str(exception)
                    + " vs person: \n"
                    + str(person)
                )
                # from here on, it gets kinda messy, to be honest.
                # Are we looking at an even streetNo?
                if (person.streetNo % 2) == 0:
                    evenNumber = True
                else:
                    evenNumber = False

                # Does the exception need a streetNo match?
                if exception.exceptionFrom == None and exception.exceptionTo == None:
                    # No need to match house numbers - check if the even-ness is the same:
                    if evenNumber == exception.evenNumbers:
                        exceptionMatch = True
                        logging.info("Exception Matched")

                else:
                    # we need to check house numbers
                    if (
                        person.streetNo <= exception.exceptionFrom
                        and person.streetNo >= exception.exceptionTo
                    ):
                        logging.info("We're in the right number range")
                if exceptionMatch == True:
                    # create variable based on the kind of exception
                    if exception.exceptionType == "parish":
                        logging.info("replaced parish from exception")
                        writePerson["parish"] = exception.exceptionValue
                    if exception.exceptionType == "district":
                        logging.info("replaced parish from exception")
                        writePerson["district"] = exception.exceptionValue
                    if exception.exceptionType == "postcode":
                        logging.info("replaced postcode from exception")
                        writePerson["postcode"] = exception.exceptionValue
                    if exception.exceptionType == "town":
                        logging.info("replaced town from exception")
                        writePerson["town"] = exception.exceptionValue


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
