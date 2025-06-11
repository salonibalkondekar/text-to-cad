// Predefined CAD Project Templates

const projects = {
    // BadCAD Examples
    badcadCross: `// BadCAD Cross Example
plus = square(3, 1, center=True) + square(1, 3, center=True)
p_lil = plus.offset(-0.4, 'round')
p_big = plus.offset(+0.4, 'round')
model = p_big.extrude_to(p_lil, 1)`,

    badcadSimpleBox: `// BadCAD Simple Box
box = square(20, 20, center=True)
model = box.extrude(10)`,

    badcadCylinder: `// BadCAD Cylinder with Hole
outer = circle(15)
inner = circle(5)
ring = outer - inner
model = ring.extrude(20)`,

    badcadGear: `// BadCAD Simple Gear
import math

# Basic gear parameters
teeth = 12
pitch_radius = 20
tooth_height = 3

# Create base circle
gear_base = circle(pitch_radius)

# Add teeth around the circumference
for i in range(teeth):
    angle = i * (2 * math.pi / teeth)
    x = (pitch_radius + tooth_height) * math.cos(angle)
    y = (pitch_radius + tooth_height) * math.sin(angle)
    tooth = square(2, tooth_height, center=True).translate(x, y)
    gear_base = gear_base + tooth

# Add center hole
center_hole = circle(5)
gear_2d = gear_base - center_hole

model = gear_2d.extrude(5)`,
    basicShapes: `// Basic shapes example - Larger for better visibility
const cube = cad.cube(3, 3, 3);
const sphere = cad.sphere(2);
sphere.mesh.position.x = 5;

const cylinder = cad.cylinder(1.5, 4);
cylinder.mesh.position.x = -5;

const model = cube.union(sphere).union(cylinder);`,

    coffeeMug: `// Professional coffee mug
const height = 3;
const radius = 1;
const wallThickness = 0.1;

const mugOuter = cad.cylinder(radius, height);
mugOuter.mesh.position.y = height / 2;

const mugInner = cad.cylinder(radius - wallThickness, height - wallThickness);
mugInner.mesh.position.y = height / 2 + wallThickness / 2;
mugInner.mesh.material.color.setHex(0x333333);
mugInner.mesh.material.transparent = true;
mugInner.mesh.material.opacity = 0.7;

const base = cad.cylinder(radius * 1.05, wallThickness * 2);
base.mesh.position.y = wallThickness;

// Professional handle
const handleRing = cad.torus(0.6, 0.06);
handleRing.mesh.position.x = radius + 0.4;
handleRing.mesh.position.y = height * 0.6;

const model = mugOuter.union(mugInner).union(base).union(handleRing);`,

    professionalGear: `// Professional gear with realistic teeth
const teeth = 12;
const pitchRadius = 2;
const module = (pitchRadius * 2) / teeth;
const outerRadius = pitchRadius + module;
const thickness = 0.5;

// Main gear body
const gearBody = cad.cylinder(outerRadius, thickness);

// Hub
const hub = cad.cylinder(pitchRadius * 0.6, thickness * 1.1);

// Center hole
const centerHole = cad.cylinder(pitchRadius * 0.25, thickness * 1.2);
centerHole.mesh.material.color.setHex(0x333333);
centerHole.mesh.material.transparent = true;
centerHole.mesh.material.opacity = 0.8;

let model = gearBody.union(hub).union(centerHole);

// Create realistic gear teeth
for (let i = 0; i < teeth; i++) {
    const angle = (i / teeth) * Math.PI * 2;
    
    // Tooth tip
    const toothTip = cad.cube(module * 0.6, module * 1.8, thickness);
    toothTip.mesh.position.x = Math.cos(angle) * (outerRadius - module * 0.3);
    toothTip.mesh.position.z = Math.sin(angle) * (outerRadius - module * 0.3);
    toothTip.mesh.rotation.y = angle;
    
    model = model.union(toothTip);
}`,

    mechanicalBearing: `// Professional CAD Example - Mechanical Bearing
const outerRing = cad.cylinder(2, 0.5);
const innerRing = cad.cylinder(1.2, 0.6);
innerRing.mesh.material.color.setHex(0x444444);

// Ball race grooves (approximated)
const groove1 = cad.torus(1.6, 0.1);
groove1.mesh.position.y = 0.15;
groove1.mesh.material.color.setHex(0x888888);

const groove2 = cad.torus(1.6, 0.1);
groove2.mesh.position.y = -0.15;
groove2.mesh.material.color.setHex(0x888888);

const model = outerRing.union(innerRing).union(groove1).union(groove2);`,

    simpleTable: `// Simple table with legs
const tabletop = cad.cube(4, 0.2, 2);
tabletop.mesh.position.y = 2.9;

const leg1 = cad.cube(0.2, 3, 0.2);
leg1.mesh.position.x = 1.7;
leg1.mesh.position.z = 0.7;
leg1.mesh.position.y = 1.4;

const leg2 = cad.cube(0.2, 3, 0.2);
leg2.mesh.position.x = -1.7;
leg2.mesh.position.z = 0.7;
leg2.mesh.position.y = 1.4;

const leg3 = cad.cube(0.2, 3, 0.2);
leg3.mesh.position.x = 1.7;
leg3.mesh.position.z = -0.7;
leg3.mesh.position.y = 1.4;

const leg4 = cad.cube(0.2, 3, 0.2);
leg4.mesh.position.x = -1.7;
leg4.mesh.position.z = -0.7;
leg4.mesh.position.y = 1.4;

const model = tabletop.union(leg1).union(leg2).union(leg3).union(leg4);`,

    hexBolt: `// Professional hex bolt
const length = 4;
const diameter = 0.5;
const headHeight = diameter * 0.6;
const headWidth = diameter * 1.5;

// Hex bolt head
const boltHead = cad.cylinder(headWidth / 2, headHeight);
boltHead.mesh.position.y = length / 2 + headHeight / 2;

// Smooth shank section
const shankLength = length * 0.3;
const shank = cad.cylinder(diameter / 2, shankLength);
shank.mesh.position.y = length / 2 - shankLength / 2;

// Threaded section
const threadedLength = length * 0.7;
const threadedSection = cad.cylinder(diameter / 2, threadedLength);
threadedSection.mesh.position.y = threadedLength / 2 - length / 2;

// Chamfered tip
const tipLength = diameter * 0.5;
const tip = cad.cylinder(diameter / 4, tipLength, 8);
tip.mesh.position.y = -length / 2 - tipLength / 2;

const model = boltHead.union(shank).union(threadedSection).union(tip);`
}; 