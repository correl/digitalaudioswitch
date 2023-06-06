include <pcb_dimensions.scad>;

TOLERANCE=0.2;

h=10;
w=3;

module pcb_mount(w=w,h=h) {
  difference() {
    union() {
      posts(w=w,h=h);
      frame(w=w);
    }
    drill_hole_cutouts(h=h);
  }
}

module drill_hole_cutouts(h=h) {
  for (hole=drill_holes) {
    pos = hole[0];
    diameter = hole[1] + TOLERANCE;
    translate([pos.x, pos.y, -0.5]) {
      cylinder(d=diameter,h=h + 1);
    }
  }
}

module posts(w=w,h=h) {
  // Posts
  for (hole=drill_holes) {
    pos = hole[0];
    diameter = hole[1] + TOLERANCE;
    translate(pos) {
      difference() {
        cylinder(d=diameter + (w * 2), h=h);
        translate([0,0,-0.5])
          cylinder(d=diameter,h=h + 1);
      }
    }
  }
}

module frame(w=w) {
  min_x = min([for (hole=drill_holes) hole[0].x]);
  min_y = min([for (hole=drill_holes) hole[0].y]);
  max_x = max([for (hole=drill_holes) hole[0].x]);
  max_y = max([for (hole=drill_holes) hole[0].y]);
  max_diameter = max([for (hole=drill_holes) hole[1]]);

  translate([min_x - (w / 2), min_y - (w / 2)]) {
    difference() {
      cube([max_x - min_x + w, max_y - min_y + w, w]);
      translate([w, w, -0.5])
        cube([max_x - min_x - w, max_y - min_y - w, w + 1]);
    }
  }
}
