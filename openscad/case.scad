$fn = 50;

include <pcb_mount.scad>;

TOLERANCE=0.5;

wall_width = 3;
side_padding = 10;
case_width = pcb_width + (wall_width * 2) + (TOLERANCE * 2) + (side_padding * 2);
case_depth = pcb_height + (wall_width * 2) + (TOLERANCE * 2);
bottom_height = 30;
pcb_spacing = 10;
pcb_thickness = 1.6;

inside_offset = [wall_width + TOLERANCE + side_padding,wall_width + TOLERANCE,wall_width];

color("purple")
translate(inside_offset)
pcb_mount(w=wall_width,h=pcb_spacing);

color("green", 0.5)
translate(inside_offset + [0,0,pcb_spacing]) {
  difference() {
    cube([pcb_width, pcb_height, pcb_thickness]);
    translate([0,0,-0.5])
      drill_hole_cutouts(h=pcb_thickness + 1);
  }
}
module rounded_box(box, r) {
  hull() {
    cylinder(r=r,h=box.z);
    translate([0,box.y])
      cylinder(r=r,h=box.z);
    translate([box.x,0])
      cylinder(r=r,h=box.z);
    translate([box.x, box.y])
      cylinder(r=r,h=box.z);
  }
}

difference() {
  rounded_box(box=[case_width, case_depth, bottom_height], r=wall_width);
  translate([wall_width,wall_width,wall_width + 1])
    rounded_box(box=[pcb_width + (TOLERANCE * 2) + (side_padding * 2),
                     pcb_height + (TOLERANCE * 2),
                     bottom_height],
                r=wall_width);
  translate(inside_offset - [0,0,wall_width + 0.5]) {
    drill_hole_cutouts(h=pcb_spacing);
    posts(w=wall_width, h=wall_width/2 + 0.5);
  }
}
