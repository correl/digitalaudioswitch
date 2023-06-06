.PHONY: all clean

all: case.stl

pcb.scad: generate.py ../kicad/Digital\ Audio\ Switch.kicad_pcb
	python3 $< > $@

case.stl: case.scad pcb.scad
	openscad -o $@ case.scad

clean:
	rm -f case.stl pcb.scad
