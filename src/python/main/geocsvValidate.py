
import sys
import urllib2
import csv

def runit():
  #   http://geows.ds.iris.edu/geows-uf/wovodat/1/query?format=text&showNumberFormatExceptions=true
  URL = sys.argv[1]

  try:
    response = urllib2.urlopen(URL)
  except urllib2.HTTPError as e:
    print e.code
    print e.read()
    print "** failed on target: ", URL
    sys.exit()

  print ("** waiting for reply....")

  ##text = response.read()
  ##print ("**** text: " + text)

  totalCnt = 0;
  rowCnt = 0
  try:
    for line in response.readlines() :
      totalCnt = totalCnt + 1

      if len(line) == 0 :
        print ("** line of length 0")
        continue

      if line[0] == '#' :
        print "geocsv? or skip if after start: ", line,
        continue

      rowlist = []
      rowlist.append(line)
      rowiter = iter(rowlist)

      csvreadr = csv.reader(rowiter, delimiter='|')
      for row in csvreadr:
        rowCnt = rowCnt + 1

        if len(row) <= 0 :
          print "** row of length 0"
          continue

        print rowCnt, " l: ", len(row), "  r: ", "  <:>  ".join(row)

  finally:
    response.close()

  print "totalCnt: ", totalCnt, "  rowCnt; ", rowCnt

if __name__ == "__main__":
  runit()


