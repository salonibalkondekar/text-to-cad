// AI Model Generator - Natural Language Processing for CAD

class AICADGenerator {
    constructor() {
        this.patterns = {
            // Object types
            objects: {
                'mug|cup|coffee': 'mug',
                'gear|cog|wheel': 'gear',
                'bolt|screw': 'bolt',
                'nut': 'nut',
                'table|desk': 'table',
                'chair|seat': 'chair',
                'house|building|home': 'house',
                'box|cube|container': 'box',
                'sphere|ball|orb': 'sphere',
                'cylinder|tube|pipe': 'cylinder',
                'phone|smartphone|mobile': 'phone',
                'case|cover|shell': 'case',
                'vase|pot|vessel': 'vase',
                'stair|staircase|steps': 'staircase',
                'tower|pillar|column': 'tower',
                'bracket|mount|support': 'bracket'
            },
            
            // Dimensions and numbers
            numbers: /(\d+(?:\.\d+)?)/g,
            dimensions: /(width|height|depth|radius|diameter|size|thick|thin)/gi,
            
            // Features
            features: {
                'handle|grip': 'handle',
                'hole|opening|cavity': 'hole',
                'teeth|tooth|cog': 'teeth',
                'legs|supports|stands': 'legs',
                'roof|top|cap': 'roof',
                'walls|sides': 'walls',
                'rounded|smooth|curved': 'rounded',
                'sharp|angular|square': 'angular'
            }
        };
        
        this.templates = {
            mug: this.generateMug,
            gear: this.generateGear,
            bolt: this.generateBolt,
            nut: this.generateNut,
            table: this.generateTable,
            house: this.generateHouse,
            box: this.generateBox,
            sphere: this.generateSphere,
            cylinder: this.generateCylinder,
            case: this.generateCase,
            vase: this.generateVase,
            staircase: this.generateStaircase,
            tower: this.generateTower,
            bracket: this.generateBracket
        };
    }

    parsePrompt(prompt) {
        const parsed = {
            object: null,
            features: [],
            dimensions: [],
            style: 'default'
        };

        const lowerPrompt = prompt.toLowerCase();

        // Find object type
        for (const [pattern, objectType] of Object.entries(this.patterns.objects)) {
            const regex = new RegExp(pattern, 'i');
            if (regex.test(lowerPrompt)) {
                parsed.object = objectType;
                break;
            }
        }

        // Find features
        for (const [pattern, feature] of Object.entries(this.patterns.features)) {
            const regex = new RegExp(pattern, 'i');
            if (regex.test(lowerPrompt)) {
                parsed.features.push(feature);
            }
        }

        // Extract numbers (handle mm, cm units)
        const numberMatches = prompt.match(/(\d+(?:\.\d+)?)\s*(mm|cm|m)?/gi);
        if (numberMatches) {
            parsed.dimensions = numberMatches.map(match => {
                const [, number, unit] = match.match(/(\d+(?:\.\d+)?)\s*(mm|cm|m)?/i) || [];
                let value = parseFloat(number);
                
                // Convert to standard units (assume base unit is ~100mm scale)
                if (unit) {
                    switch (unit.toLowerCase()) {
                        case 'mm': value = value / 100; break;  // Convert mm to scene units
                        case 'cm': value = value / 10; break;   // Convert cm to scene units
                        case 'm': value = value * 10; break;    // Convert m to scene units
                    }
                }
                return value;
            });
        }

        return parsed;
    }

    async generate(prompt) {
        console.log(`🤖 Analyzing prompt: "${prompt}"`);
        
        // Add realistic delay for AI effect
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
        
        const parsed = this.parsePrompt(prompt);
        console.log(`🧠 Detected object: ${parsed.object || 'unknown'}`);
        
        if (parsed.features.length > 0) {
            console.log(`✨ Features: ${parsed.features.join(', ')}`);
        }

        if (!parsed.object) {
            // Fallback to basic shape
            parsed.object = 'box';
            console.log(`⚠️ Unknown object, creating basic box instead`);
        }

        const generator = this.templates[parsed.object];
        if (generator) {
            const code = generator.call(this, parsed);
            console.log(`✅ Generated CAD code successfully!`);
            return code;
        } else {
            throw new Error(`No generator found for object: ${parsed.object}`);
        }
    }

    // Template generators will be loaded from separate files
    generateMug(parsed) {
        const height = parsed.dimensions[0] || 3;
        const radius = parsed.dimensions[1] || 1;
        const hasHandle = parsed.features.includes('handle');
        const wallThickness = 0.1;

        return `// AI Generated: Professional Coffee Mug
const height = ${height};
const radius = ${radius};
const wallThickness = ${wallThickness};

// Main mug body with realistic proportions
const mugOuter = cad.cylinder(radius, height);
mugOuter.mesh.position.y = height / 2;

// Create hollow interior (for visualization, shown as darker cylinder)
const mugInner = cad.cylinder(radius - wallThickness, height - wallThickness);
mugInner.mesh.position.y = height / 2 + wallThickness / 2;
mugInner.mesh.material.color.setHex(0x333333);
mugInner.mesh.material.transparent = true;
mugInner.mesh.material.opacity = 0.7;

// Mug base with slight taper
const base = cad.cylinder(radius * 1.05, wallThickness * 2);
base.mesh.position.y = wallThickness;

// Rim reinforcement
const rim = cad.cylinder(radius * 1.02, wallThickness);
rim.mesh.position.y = height - wallThickness / 2;

let model = mugOuter.union(mugInner).union(base).union(rim);

${hasHandle ? `
// Professional handle design
const handleRing = cad.cylinder(${wallThickness * 0.6}, ${height * 0.6});
handleRing.mesh.position.x = ${radius + wallThickness * 4};
handleRing.mesh.position.y = ${height * 0.6};
handleRing.mesh.rotation.z = Math.PI / 2;

// Handle connection points
const handleConnect1 = cad.cube(${wallThickness * 2}, ${wallThickness * 2}, ${wallThickness * 2});
handleConnect1.mesh.position.x = ${radius + wallThickness};
handleConnect1.mesh.position.y = ${height * 0.75};

const handleConnect2 = cad.cube(${wallThickness * 2}, ${wallThickness * 2}, ${wallThickness * 2});
handleConnect2.mesh.position.x = ${radius + wallThickness};
handleConnect2.mesh.position.y = ${height * 0.45};

// Handle outer curve  
const handleOuter = cad.cylinder(${wallThickness * 0.8}, ${height * 0.5});
handleOuter.mesh.position.x = ${radius + wallThickness * 5};
handleOuter.mesh.position.y = ${height * 0.6};
handleOuter.mesh.rotation.z = Math.PI / 2;

model = model.union(handleRing).union(handleConnect1).union(handleConnect2).union(handleOuter);` : ''}`;
    }

    generateGear(parsed) {
        const teeth = parsed.dimensions[0] || 12;
        const pitchRadius = parsed.dimensions[1] || 2;
        const hasHole = parsed.features.includes('hole');
        
        // Calculate realistic gear dimensions
        const module = (pitchRadius * 2) / teeth; // Gear module
        const addendum = module * 1.0;
        const dedendum = module * 1.25;
        const outerRadius = pitchRadius + addendum;
        const rootRadius = pitchRadius - dedendum;
        const thickness = parsed.dimensions[2] || (module * 8);
        const holeRadius = hasHole ? pitchRadius * 0.3 : 0;

        return `// AI Generated: Professional Gear (${teeth} teeth, Module: ${module.toFixed(2)})
// Gear specifications: Pitch radius ${pitchRadius}, Outer radius ${outerRadius.toFixed(2)}

// Create gear body with realistic proportions
const gearBody = cad.cylinder(${outerRadius}, ${thickness});

// Create realistic gear teeth using involute approximation
let model = gearBody;
const teeth = ${teeth};
const pitchRadius = ${pitchRadius};
const outerRadius = ${outerRadius};
const rootRadius = ${rootRadius};
const thickness = ${thickness};

// Generate professional gear teeth
for (let i = 0; i < teeth; i++) {
    const baseAngle = (i / teeth) * Math.PI * 2;
    
    // Create tooth profile - more realistic than simple rectangles
    // Tooth tip (addendum)
    const toothTip = cad.cube(${module * 0.8}, ${addendum * 2}, thickness);
    toothTip.mesh.position.x = Math.cos(baseAngle) * ${outerRadius - addendum * 0.3};
    toothTip.mesh.position.z = Math.sin(baseAngle) * ${outerRadius - addendum * 0.3};
    toothTip.mesh.rotation.y = baseAngle;
    
    // Tooth flank (working surface)
    const toothFlank1 = cad.cube(${module * 0.6}, ${addendum * 1.8}, thickness);
    toothFlank1.mesh.position.x = Math.cos(baseAngle + ${Math.PI / teeth * 0.3}) * ${pitchRadius};
    toothFlank1.mesh.position.z = Math.sin(baseAngle + ${Math.PI / teeth * 0.3}) * ${pitchRadius};
    toothFlank1.mesh.rotation.y = baseAngle + ${Math.PI / teeth * 0.3};
    
    const toothFlank2 = cad.cube(${module * 0.6}, ${addendum * 1.8}, thickness);
    toothFlank2.mesh.position.x = Math.cos(baseAngle - ${Math.PI / teeth * 0.3}) * ${pitchRadius};
    toothFlank2.mesh.position.z = Math.sin(baseAngle - ${Math.PI / teeth * 0.3}) * ${pitchRadius};
    toothFlank2.mesh.rotation.y = baseAngle - ${Math.PI / teeth * 0.3};
    
    // Combine tooth parts
    const completeTooth = toothTip.union(toothFlank1).union(toothFlank2);
    model = model.union(completeTooth);
}

// Add hub and spokes for realism
const hub = cad.cylinder(${pitchRadius * 0.6}, ${thickness * 1.1});
model = model.union(hub);

// Add reinforcing spokes
for (let i = 0; i < Math.min(6, teeth/2); i++) {
    const spokeAngle = (i / Math.min(6, teeth/2)) * Math.PI * 2;
    const spoke = cad.cube(${module * 0.4}, ${pitchRadius * 0.8}, ${thickness * 0.8});
    spoke.mesh.position.x = Math.cos(spokeAngle) * ${pitchRadius * 0.35};
    spoke.mesh.position.z = Math.sin(spokeAngle) * ${pitchRadius * 0.35};
    spoke.mesh.rotation.y = spokeAngle;
    model = model.union(spoke);
}

${hasHole ? `
// Create center mounting hole
const centerHole = cad.cylinder(${holeRadius}, ${thickness * 1.2});
// In real CAD: model = model.subtract(centerHole);
// For visualization, we'll show the hole as a darker cylinder
centerHole.mesh.material.color.setHex(0x333333);
centerHole.mesh.material.transparent = true;
centerHole.mesh.material.opacity = 0.8;
model = model.union(centerHole);

// Add keyway for shaft connection
const keyway = cad.cube(${holeRadius * 0.3}, ${holeRadius * 2}, ${thickness * 1.1});
keyway.mesh.position.x = ${holeRadius * 0.65};
keyway.mesh.material.color.setHex(0x222222);
keyway.mesh.material.transparent = true;
keyway.mesh.material.opacity = 0.9;
model = model.union(keyway);
` : ''}`;
    }

    // Add other generator methods here...
    generateBox(parsed) {
        const width = parsed.dimensions[0] || 2;
        const height = parsed.dimensions[1] || 2;
        const depth = parsed.dimensions[2] || 2;

        return `// AI Generated: Box
const model = cad.cube(${width}, ${height}, ${depth});`;
    }

    generateSphere(parsed) {
        const radius = parsed.dimensions[0] || 1;
        return `// AI Generated: Sphere
const model = cad.sphere(${radius});`;
    }

    generateCylinder(parsed) {
        const radius = parsed.dimensions[0] || 1;
        const height = parsed.dimensions[1] || 2;
        return `// AI Generated: Cylinder
const model = cad.cylinder(${radius}, ${height});`;
    }

    // Placeholder methods for other generators
    generateBolt(parsed) { return this.generateCylinder(parsed); }
    generateNut(parsed) { return this.generateCylinder(parsed); }
    generateTable(parsed) { return this.generateBox(parsed); }
    generateHouse(parsed) { return this.generateBox(parsed); }
    generateCase(parsed) { return this.generateBox(parsed); }
    generateVase(parsed) { return this.generateCylinder(parsed); }
    generateStaircase(parsed) { return this.generateBox(parsed); }
    generateTower(parsed) { return this.generateCylinder(parsed); }
    generateBracket(parsed) { return this.generateBox(parsed); }
} 