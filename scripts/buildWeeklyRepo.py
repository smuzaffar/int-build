from optparse import OptionParser

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-a", "--arch", target="architecture")
  opts, args = parser.parse_args()
  if not opts.architecture:
    parser.error("Please specify an architecture")
  if not len(args) == 1:
    parser.error("Please specify one and only one release cycle")
  
  
