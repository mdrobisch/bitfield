from bit_field import bitfield
reg = [
    { "name": "IPO",   "bits": 8, "attr": "RO" },
]

options = {
  "hspace": 888,
  "bits": 16,
  "lanes": 1
}

plot = bitfield.plotBitfield(reg, options)
print(plot)
file = open("testfile.svg","w") 
file.write(plot)
file.close()
