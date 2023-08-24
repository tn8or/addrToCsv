import os
import logging
import csv
import argparse
from dataclasses import dataclass


@dataclass
class Street:
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
class Person:
    streetId: int
    streetNo: int
    streetNoSuffix: str
    floor: str
    door: str
    firstName: str
    lastName: str
    occupation: str
    careOf: str


@dataclass
class fullPerson:
    streetId: int
    streetNo: int
    streetNoSuffix: str
    floor: str
    door: str
    firstName: str
    lastName: str
    occupation: str
    careOf: str
    streetName: str
    parish: str = None
    postCode: str = None
    town: str = None
    district: str = None


class addressWriter:
    def __init__(self, inputfile):
        logging.info("will read file: %s ", inputfile)
        inputfile = open(inputfile, "r", encoding="ISO-8859-1")
        self.lines = inputfile.readlines()
        self.streets = []
        self.streetExceptions = []
        self.persons = []
        self.fullpersons = []

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
                floor = line[14:16].lower().strip()
                door = line[19:21].lower().strip()
                streetNoSuffix = line[12].upper().strip()

                logging.debug(
                    "We've got a live one! streetid: %s, streetNo: %s, streetNoSuffix: %s, lastName: %s, firstName: %s, occupation: %s, careOf: %s",
                    streetId,
                    streetNo,
                    streetNoSuffix,
                    lastName,
                    firstName,
                    occupation,
                    careOf,
                )
                newPerson = Person(
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
        lineCount = 0
        for line in self.lines:
            lineCount += 1
            fields = line.split()

            logging.debug(
                "at line %s in the file. Field0 is %s", str(lineCount), fields[0]
            )

            match fields[0]:
                case "00":
                    count += 1
                    if count > 1:
                        # If this is not the first iteration, lets store the data.
                        # We start a new Street-gathering routine every time field 0 is "00",
                        # designating the start of a new object
                        # If there is something to store, we should store it now, before moving on
                        if streetName != None:
                            streetObj = Street(
                                streetId=int(curStreet),
                                streetName=streetName,
                                postCode=postCode,
                                parish=parish,
                                town=town,
                                district=district,
                            )
                            logging.debug("added Street %s", streetObj)

                            self.streets.append(streetObj)
                            streetName = None
                            parish = None
                            town = None
                            postCode = None
                            streetObj = None
                            district = None

                    # this starts a new Street section
                    curStreet = fields[2]
                    streetName = " ".join(line[12:63].split())
                    logging.debug("streetName: %s curstreet: %s", streetName, curStreet)

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
                    else:
                        logging.debug("there's a Street mismatch in this line, exiting")
                        logging.debug(line)
                        quit()
                case "03":
                    # parish lives here
                    if curStreet == fields[2]:
                        parish = self.parseLineforExceptions(
                            line=line,
                            fields=fields,
                            curStreet=curStreet,
                            fieldtype="parish",
                        )
                    else:
                        logging.debug("there's a Street mismatch in this line, exiting")
                        logging.debug(line)
                        quit()
                case "04":
                    # town lives here
                    logging.debug("this line is: %s", line)
                    if curStreet == fields[2]:
                        logging.debug("looking for exceptions")

                        town = self.parseLineforExceptions(
                            line=line,
                            fields=fields,
                            curStreet=curStreet,
                            fieldtype="town",
                        )
                    else:
                        logging.debug("there's a Street mismatch in this line, exiting")
                        logging.debug(line)
                        quit()

                case "05":
                    # district lives here
                    if curStreet == fields[2]:
                        district = self.parseLineforExceptions(
                            line=line,
                            fields=fields,
                            curStreet=curStreet,
                            fieldtype="district",
                        )
                    else:
                        logging.debug("there's a Street mismatch in this line, exiting")
                        logging.debug(line)
                        quit()
                case "07":
                    # we're down into persons - so lets store the Street and move on, if there is something to store:
                    if streetName is not None:
                        streetObj = Street(
                            streetId=int(curStreet),
                            streetName=streetName,
                            postCode=postCode,
                            parish=parish,
                            town=town,
                            district=district,
                        )
                        logging.debug("added Street %s", streetObj)

                        self.streets.append(streetObj)
                        streetName = None
                        parish = None
                        town = None
                        postCode = None
                        streetObj = None
                        district = None

        # write the last Street to file, even though we're out of the loop
        if streetName is not None:
            streetObj = Street(
                streetId=int(curStreet),
                streetName=streetName,
                postCode=postCode,
                parish=parish,
                town=town,
                district=district,
            )
            logging.debug("added Street %s", streetObj)

            self.streets.append(streetObj)
            streetName = None
            parish = None
            town = None
            postCode = None
            streetObj = None
            district = None

    def parseLineforExceptions(
        self, line: str, fields: list, curStreet: int, fieldtype: str
    ) -> any:
        if len(fields) >= 5:
            if fields[4] == "nr":
                isRange = None
                logging.debug("exception found %s", line)

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
                        isRange = True

                        logging.debug(line)
                        exceptionFrom = int("".join(line[21:24].split()))
                        exceptionFromSuffix = line[24].strip()
                        exceptionTo = int("".join(line[26:29].split()))
                        exceptionToSuffix = line[29].strip()
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
                        logging.debug("added exception %s", newException)
                except:
                    pass
                if isRange == False:
                    logging.debug("its not a range")
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
                    logging.debug("added exception %s", newException)

            else:
                value = " ".join(line[12:63].split())
                logging.debug("No exception, return the value %s", value)
                return value

        else:
            value = " ".join(line[12:63].split())
            logging.debug("No exception, return the value %s", value)
            return value

    def writeStreetFile(self, file) -> any:
        streetfile = open(file, "w", newline="", encoding="UTF-8")
        self.streetWriter = csv.writer(streetfile, dialect="excel")

        if len(self.streets) == 0:
            self.parseStreets()
        self.streetWriter.writerow(
            ["ID", "Vejnavn", "Sogn", "Postdistrikt", "By", "Flække"]
        )
        for Street in self.streets:
            self.streetWriter.writerow(
                [
                    Street.streetId,
                    Street.streetName,
                    Street.parish,
                    Street.postCode,
                    Street.town,
                    Street.district,
                ]
            )
        logging.info("wrote %s streets to file", len(self.streets))

    def writeStreetExceptions(self, file) -> any:
        exceptionfile = open(file, "w", newline="", encoding="UTF-8")
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
        logging.info("wrote %s exceptions to file", len(self.streetExceptions))

    def parseFullPersons(self) -> any:
        if len(self.persons) == 0:
            self.parsePersons()

        for Person in self.persons:
            writePerson = {}
            self.findStreetAndException(Person=Person, writePerson=writePerson)
            logging.debug(Person)
            logging.info(writePerson)
            if len(writePerson) < 2:
                logging.error("No Street info found, exiting for Person:")
                logging.error(writePerson)
                logging.error(Person)
                quit()

            personToSave = fullPerson(
                streetId=Person.streetId,
                lastName=Person.lastName,
                firstName=Person.firstName,
                occupation=Person.occupation,
                careOf=Person.careOf,
                streetNo=Person.streetNo,
                streetNoSuffix=Person.streetNoSuffix,
                floor=Person.floor,
                door=Person.door,
                streetName=writePerson["streetName"],
                parish=writePerson["parish"],
                postCode=writePerson["postCode"],
                town=writePerson["town"],
                district=writePerson["district"],
            )
            self.fullpersons.append(personToSave)

    def writePersonsCsv(self, file) -> any:
        personfile = open(file, "w", newline="", encoding="UTF-8")
        personWriter = csv.writer(personfile, dialect="excel")
        if len(self.fullpersons) == 0:
            self.parseFullPersons()
            personWriter.writerow(
                [
                    "gadeID",
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
            for writePerson in self.fullpersons:
                personWriter.writerow(
                    [
                        writePerson.streetId,
                        writePerson.lastName,
                        writePerson.firstName,
                        writePerson.occupation,
                        writePerson.careOf,
                        writePerson.streetName,
                        str(writePerson.streetNo) + str(writePerson.streetNoSuffix),
                        str(writePerson.floor) + " " + str(writePerson.door),
                        writePerson.postCode,
                        writePerson.district,
                        writePerson.town,
                        writePerson.parish,
                    ]
                )
            logging.info("wrote %s persons to file", len(self.fullpersons))

    def findStreetAndException(self, Person, writePerson):
        if len(self.streetExceptions) == 0:
            self.parseStreets()
        for Street in self.streets:
            if Street == Person.streetId:
                logging.debug("found Street %s", Street)
                writePerson["streetName"] = Street.streetName
                writePerson["postCode"] = Street.postCode
                writePerson["town"] = Street.town
                writePerson["parish"] = Street.parish
                writePerson["district"] = Street.district

        ## go searching through exceptions to see if we have an override
        for exception in self.streetExceptions:
            # Lets not declare exception before we've verified it
            exception_match = False
            if exception == Person.streetId:
                logging.info("maybe found exception? \n %s \n %s", exception, Person)
                # from here on, it gets kinda messy, to be honest.
                # Are we looking at an even streetNo?
                if (Person.streetNo % 2) == 0:
                    evenNumber = True
                else:
                    evenNumber = False

                # Does the exception need a streetNo match?
                if exception.exceptionFrom == None and exception.exceptionTo == None:
                    # No need to match house numbers - check if the even-ness is the same:
                    if evenNumber == exception.evenNumbers:
                        exception_match = True
                        logging.info("exception match on odd/even number")

                else:
                    # we need to check house numbers and suffices
                    if (
                        Person.streetNo >= exception.exceptionFrom
                        and Person.streetNo <= exception.exceptionTo
                    ):
                        # is this suffix-less?
                        if (
                            Person.streetNoSuffix == ""
                            or (
                                Person.streetNoSuffix >= exception.exceptionFromSuffix
                                and Person.streetNoSuffix <= exception.exceptionToSuffix
                            )
                            or (
                                exception.exceptionFromSuffix == ""
                                and exception.exceptionToSuffix == ""
                            )
                        ):
                            logging.info("exception match on streetNo")
                            exception_match = True

                if exception_match:
                    # create variable based on the kind of exception
                    if exception.exceptionType == "parish":
                        logging.info("replaced parish from exception")
                        writePerson["parish"] = exception.exceptionValue
                    elif exception.exceptionType == "district":
                        logging.info("replaced parish from exception")
                        writePerson["district"] = exception.exceptionValue
                    elif exception.exceptionType == "postCode":
                        logging.info("replaced postcode from exception")
                        writePerson["postCode"] = exception.exceptionValue
                    elif exception.exceptionType == "town":
                        logging.info("replaced town from exception")
                        writePerson["town"] = exception.exceptionValue
                    else:
                        logging.error("Exception matched, but not replaced!")
                        quit()


logging.basicConfig(
    filename="output.log",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

parser = argparse.ArgumentParser(
    prog="run.py",
    usage="The -i flag is required (input file). At least one output option is required as well.",
    description="Will extract persons and streets from the KMD mainframe extract, \n"
    + "and store as csv files, for further phonebook formatting",
    add_help=True,
)
inputs = parser.add_argument_group("Input arguments", "Required for operation")

inputs.add_argument(
    "-i", "--input", help="Input filename. The KMD .txt file", required=True
)

outputs = parser.add_argument_group(
    "Output arguments", "Specify at least one, or you're not getting any output :-)"
)
outputs.add_argument("-p", "--Person", help="CSV file for outputting the Person data")
outputs.add_argument("-s", "--Street", help="CSV file for storing Street names")
outputs.add_argument(
    "-e",
    "--exceptions",
    help="CSV file for storing Street exceptions (parish, town, etc)",
)

args = parser.parse_args()

try:
    if os.path.isfile(args.input):
        convert = addressWriter(args.input)

except:
    print(
        "No inFileName provided. First argument is input-file, second argument is output-file (csv)"
    )
    print("The util will append to the file without further questions")
    quit()

if args.Street:
    print("Will write streets to file " + args.Street)
    convert.writeStreetFile(file=args.Street)
    writes = True

if args.exceptions:
    print("Will write exceptions to file " + args.exceptions)
    convert.writeStreetExceptions(file=args.exceptions)
    writes = True

if args.Person:
    print("Will write persons to file " + args.Person)
    convert.writePersonsCsv(file=args.Person)
    writes = True


if not "writes" in locals():
    logging.error("No output file specified - probably not what you want")
