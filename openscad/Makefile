.PHONY: all clean

all: case.stl

pcb_dimensions.scad: generate.py ../kicad/Digital\ Audio\ Switch.kicad_pcb
	python3 $< > $@

case.stl: case.scad pcb_dimensions.scad
	openscad -o $@ case.scad

clean:
	rm -f case.stl pcb_dimensions.scad
