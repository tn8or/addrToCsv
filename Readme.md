#util for converting a danish address extract into csv format; pretty internal stuff
##The address extract is from KMD, as an extract from the address registry. This is just for sanitizing the output a bit, to use it more programmatically


Input file could look like this - a sequence of control codes describing the street, and then residents on said street.
```
Column descriptions:
Column 0 variants:
    00: Street name
    02: Post code
    03: Parish
    04: Town name
    05: Area name ("Flække") in danish
    07: person

Column 1 variants:
    657: street

Column 2 is a street ID
Column 3-> is text of sorts

00 657 0268 Street
02 657 0268 0100  Postcode
03 657 0268 Parishy parish name
04 657 0268 Town
05 657 0268 Smalltown 1

Or it can look like this, with overrides based on house no:
00 657 0258 Other street
02 657 0258 Ulige nr 001 -069  0100 postcode 1
02 657 0258 Ulige nr 073 -077  0200 postcode 2
03 657 0258 Ulige nr 001 -073  Parish 1
03 657 0258 Ulige nr 075 -077  Parish 2
04 657 0258 Town
05 657 0258 Ulige nr 001 -069  Smalltown 2
05 657 0258 Ulige nr 073 -077  Smalltown 3


Person records look like this:

Column 0: 07 (person)
Column 1: Street ID
Column 2: house no
column 3 (opt): House suffix
From then we go to fixed length fields:
lastName = char 35:61
firstName(s) = char 61:99
occupation (opt) = char 99:114
c/o = char:115-150

07 0258 001 a                      Lastna                    Firstna
07 0258 012                        Lastname1                 Firstn          Middlen    S                         c/o Care Of Address
07 0258 011                        Surname                   First           Midd                  Occupation
```
