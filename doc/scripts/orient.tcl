package require Orient
namespace import Orient::orient

mol new protein.pdb 
animate delete beg 0 end -1  0
mol addfile protein.xtc type xtc waitfor all

for {set i 0} {$i < [molinfo top get numframes]} {incr i} {
    animate goto $i
    set sel [atomselect top "protein"]
    set mv  [atomselect top "all"]
    set I [draw principalaxes $sel]
    set A [orient $sel [lindex $I 2] {0 0 1}]
    $mv move $A
    set I [draw principalaxes $sel]
    set A [orient $sel [lindex $I 1] {0 1 0}]
    $mv move $A
    set I [draw principalaxes $sel]
}
#mol addfile protein.xtc type xtc first 0 last -1 step 1 waitfor all 0
