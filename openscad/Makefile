.PHONY: all clean

all: case.stl mounting_bracket.stl

pcb_dimensions.scad: generate.py ../kicad/Digital\ Audio\ Switch.kicad_pcb
	python3 $< > $@

%.stl: case.scad pcb_dimensions.scad
	openscad -o $@ -D MODE=\"$(basename $@)\" $<

clean:
	rm -f case.stl pcb_dimensions.scad
