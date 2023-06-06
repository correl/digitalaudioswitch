$fn = 50;

use <pcb.scad>;

color("green", 0.5)
translate([0,0,10])
    pcb(1.6);

mounting_supports(h=10,r=4);
