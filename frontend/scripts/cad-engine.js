// CAD Engine - 3D Object Creation and Operations

// Helper function to create Blender-style default material
function createBlenderMaterial(colorOverride = null) {
    return new THREE.MeshStandardMaterial({
        color: colorOverride || 0x8c8c8c,  // Blender's exact default gray
        metalness: 0.0,      // Non-metallic by default
        roughness: 0.5,      // Semi-matte finish like Blender
        envMapIntensity: 0.5, // Subtle environment reflection
        // Blender-style material properties
        transparent: false,
        opacity: 1.0,
        side: THREE.FrontSide
    });
}

// Make the function globally available
window.createBlenderMaterial = createBlenderMaterial;

// CAD Object class
class CADObject {
    constructor(mesh) {
        this.mesh = mesh;
    }

    union(other) {
        const group = new THREE.Group();
        group.add(this.mesh.clone());
        group.add(other.mesh.clone());
        return new CADObject(group);
    }

    subtract(other) {
        // CSG operations now handled by backend
        console.warn('CSG subtract operation - use BadCAD for proper boolean operations');
        const group = new THREE.Group();
        group.add(this.mesh.clone());
        return new CADObject(group);
    }

    intersect(other) {
        // CSG operations now handled by backend
        console.warn('CSG intersect operation - use BadCAD for proper boolean operations');
        const group = new THREE.Group();
        group.add(this.mesh.clone());
        return new CADObject(group);
    }

    build() {
        return this.mesh;
    }
}

// CAD Factory - Creates 3D primitives
const cad = {
    cube: function(widthOrOptions, height, depth) {
        let w, h, d;
        if (typeof widthOrOptions === 'object') {
            const opts = widthOrOptions;
            w = opts.w ?? opts.width ?? 1;
            h = opts.h ?? opts.height ?? w;
            d = opts.d ?? opts.depth ?? w;
        } else {
            w = widthOrOptions;
            h = height ?? widthOrOptions;
            d = depth ?? widthOrOptions;
        }
        const geometry = new THREE.BoxGeometry(w, h, d);
        const material = createBlenderMaterial();
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return new CADObject(mesh);
    },
    
    cylinder: function(radiusOrOptions, height, segments = 32) {
        let r, h, seg;
        if (typeof radiusOrOptions === 'object') {
            const opts = radiusOrOptions;
            r = opts.r ?? opts.radius ?? 1;
            h = opts.h ?? opts.height ?? 1;
            seg = opts.segments ?? segments;
        } else {
            r = radiusOrOptions;
            h = height;
            seg = segments;
        }
        const geometry = new THREE.CylinderGeometry(r, r, h, seg);
        const material = createBlenderMaterial();
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return new CADObject(mesh);
    },
    
    sphere: function(radiusOrOptions, segments = 32) {
        let r, seg;
        if (typeof radiusOrOptions === 'object') {
            const opts = radiusOrOptions;
            r = opts.r ?? opts.radius ?? 1;
            seg = opts.segments ?? segments;
        } else {
            r = radiusOrOptions;
            seg = segments;
        }
        const geometry = new THREE.SphereGeometry(r, seg, seg);
        const material = createBlenderMaterial();
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return new CADObject(mesh);
    },

    // Advanced shapes for more realistic models
    cone: function(optionsOrRadiusTop, radiusBottom, height, segments = 32) {
        let rTop, rBottom, h, seg;
        if (typeof optionsOrRadiusTop === 'object') {
            const opts = optionsOrRadiusTop;
            rTop = opts.radiusTop ?? 0;
            rBottom = opts.radiusBottom ?? opts.radius ?? 1;
            h = opts.h ?? opts.height ?? 1;
            seg = opts.segments ?? segments;
        } else {
            rTop = optionsOrRadiusTop;
            rBottom = radiusBottom;
            h = height;
            seg = segments;
        }
        const geometry = new THREE.ConeGeometry(rBottom, h, seg);
        const material = createBlenderMaterial();
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return new CADObject(mesh);
    },

    torus: function(radiusOrOptions, tube, radialSegments = 16, tubularSegments = 32) {
        let r, t, rSeg, tSeg;
        if (typeof radiusOrOptions === 'object') {
            const opts = radiusOrOptions;
            r = opts.majorRadius ?? opts.r ?? opts.radius ?? 1;
            t = opts.tubeRadius ?? opts.tube ?? 0.4;
            if (opts.segments) {
                rSeg = Array.isArray(opts.segments) ? opts.segments[0] : opts.segments;
                tSeg = Array.isArray(opts.segments) ? opts.segments[1] : tubularSegments;
            } else {
                rSeg = radialSegments;
                tSeg = tubularSegments;
            }
        } else {
            r = radiusOrOptions;
            t = tube;
            rSeg = radialSegments;
            tSeg = tubularSegments;
        }
        const geometry = new THREE.TorusGeometry(r, t, rSeg, tSeg);
        const material = createBlenderMaterial();
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        return new CADObject(mesh);
    }
};

// Model Builder - Executes CAD code and builds 3D models
class ModelBuilder {
    constructor() {
        this.currentModel = null;
    }

    build(code, scene) {
        try {
            console.log('🔨 Building model...');

            // Clear previous model
            if (this.currentModel) {
                scene.remove(this.currentModel);
                this.currentModel = null;
            }

            if (!code.trim()) {
                throw new Error('No code to build');
            }

            const executeCode = new Function('cad', 'THREE', 'Math', `
                try {
                    ${code}
                    if (typeof model !== 'undefined') {
                        return model.build();
                    } else {
                        throw new Error('No model variable found. Make sure your code defines a "model" variable.');
                    }
                } catch (err) {
                    throw err;
                }
            `);

            this.currentModel = executeCode(cad, THREE, Math);
            
            if (this.currentModel) {
                // Add to scene first
                scene.add(this.currentModel);
                
                // Calculate bounding box
                const box = new THREE.Box3().setFromObject(this.currentModel);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                
                console.log(`📏 Model size: ${size.x.toFixed(2)} x ${size.y.toFixed(2)} x ${size.z.toFixed(2)}`);
                console.log(`📍 Model center: (${center.x.toFixed(2)}, ${center.y.toFixed(2)}, ${center.z.toFixed(2)})`);
                
                return {
                    model: this.currentModel,
                    center: center,
                    size: size
                };
            } else {
                throw new Error('No model returned from code execution');
            }

        } catch (error) {
            console.error('❌ Build Error:', error.message);
            throw error;
        }
    }

    updateWireframe(wireframeMode) {
        if (this.currentModel) {
            this.currentModel.traverse((child) => {
                if (child instanceof THREE.Mesh && child.material) {
                    child.material.wireframe = wireframeMode;
                }
            });
        }
    }

    getCurrentModel() {
        return this.currentModel;
    }
}