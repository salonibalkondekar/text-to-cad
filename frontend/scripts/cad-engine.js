// CAD Engine - 3D Object Creation and Operations

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
        if (typeof CSG === 'undefined') {
            throw new Error('CSG library not loaded. Ensure three-csg.js is included.');
        }
        // Perform CSG subtraction
        const resultMesh = CSG.subtract(this.mesh.clone(), other.mesh.clone());
        // Ensure result uses a standard material and shadows
        resultMesh.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
            }
        });
        return new CADObject(resultMesh);
    }

    intersect(other) {
        if (typeof CSG === 'undefined') {
            throw new Error('CSG library not loaded. Ensure three-csg.js is included.');
        }
        const resultMesh = CSG.intersect(this.mesh.clone(), other.mesh.clone());
        resultMesh.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
            }
        });
        return new CADObject(resultMesh);
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
        const material = new THREE.MeshPhongMaterial({ 
            color: 0x667eea,
            transparent: false,
            opacity: 1.0,
            shininess: 100
        });
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
        const material = new THREE.MeshPhongMaterial({ 
            color: 0x667eea,
            transparent: false,
            opacity: 1.0,  
            shininess: 100
        });
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
        const material = new THREE.MeshPhongMaterial({ 
            color: 0x667eea,
            transparent: false,
            opacity: 1.0,
            shininess: 100
        });
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
        const material = new THREE.MeshPhongMaterial({ 
            color: 0x667eea,
            shininess: 100
        });
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
        const material = new THREE.MeshPhongMaterial({ 
            color: 0x667eea,
            shininess: 100
        });
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
                // Ensure model is properly positioned and visible
                scene.add(this.currentModel);
                
                // Calculate bounding box to ensure model is in view
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