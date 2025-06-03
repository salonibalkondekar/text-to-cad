// Three.js Scene Setup and Management

class ThreeJSManager {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.axesHelper = null;
        this.animationEnabled = false;
        this.wireframeMode = false;
        this.modelBuilder = new ModelBuilder();
    }

    init(containerId) {
        try {
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0x0f1419);

            this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
            this.camera.position.set(6, 4, 6);
            this.camera.lookAt(0, 0, 0);

            this.renderer = new THREE.WebGLRenderer({ antialias: true });
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

            const viewport = document.getElementById(containerId);
            viewport.appendChild(this.renderer.domElement);

            this.setupLighting();
            this.setupControls();
            this.setupAxes();
            this.resizeRenderer();
            this.animate();

            // Expose Three.js objects globally for the playground
            Object.assign(window, { 
                THREE, 
                scene: this.scene, 
                camera: this.camera, 
                renderer: this.renderer,
                controls: { reset: () => this.resetView() }
            });

            console.log('🚀 Three.js initialized successfully');
            return true;
        } catch (error) {
            console.error('❌ Three.js initialization error:', error.message);
            return false;
        }
    }

    setupLighting() {
        // Enhanced lighting for better visibility
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.1;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -10;
        directionalLight.shadow.camera.right = 10;
        directionalLight.shadow.camera.top = 10;
        directionalLight.shadow.camera.bottom = -10;
        this.scene.add(directionalLight);

        const pointLight = new THREE.PointLight(0x667eea, 1.0, 100);
        pointLight.position.set(-10, 10, 10);
        this.scene.add(pointLight);

        const fillLight = new THREE.DirectionalLight(0x87ceeb, 0.6);
        fillLight.position.set(-5, -5, 5);
        this.scene.add(fillLight);

        // Rim light for better definition
        const rimLight = new THREE.DirectionalLight(0xffffff, 0.7);
        rimLight.position.set(0, 0, -10);
        this.scene.add(rimLight);

        // Add ground plane for reference - smaller and less prominent
        const groundGeometry = new THREE.PlaneGeometry(30, 30);
        const groundMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x333333,
            transparent: true,
            opacity: 0.2
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.01;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }

    setupControls() {
        let mouseDown = false;
        let mouseX = 0;
        let mouseY = 0;

        const canvas = this.renderer.domElement;

        canvas.addEventListener('mousedown', (event) => {
            mouseDown = true;
            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        canvas.addEventListener('mouseup', () => {
            mouseDown = false;
        });

        canvas.addEventListener('mousemove', (event) => {
            if (mouseDown) {
                const deltaX = event.clientX - mouseX;
                const deltaY = event.clientY - mouseY;

                const spherical = new THREE.Spherical();
                spherical.setFromVector3(this.camera.position);
                spherical.theta -= deltaX * 0.01;
                spherical.phi += deltaY * 0.01;
                spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));

                this.camera.position.setFromSpherical(spherical);
                this.camera.lookAt(0, 0, 0);

                mouseX = event.clientX;
                mouseY = event.clientY;
            }
        });

        canvas.addEventListener('wheel', (event) => {
            event.preventDefault();
            const distance = this.camera.position.distanceTo(new THREE.Vector3(0, 0, 0));
            const newDistance = distance + event.deltaY * 0.01;
            const clampedDistance = Math.max(1, Math.min(50, newDistance));
            
            this.camera.position.normalize().multiplyScalar(clampedDistance);
        });
    }

    setupAxes() {
        this.axesHelper = new THREE.AxesHelper(3);
        this.axesHelper.visible = false;
        this.scene.add(this.axesHelper);
    }

    resizeRenderer() {
        const viewport = this.renderer.domElement.parentElement;
        const width = viewport.clientWidth;
        const height = viewport.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        if (this.animationEnabled && this.modelBuilder.getCurrentModel()) {
            this.modelBuilder.getCurrentModel().rotation.y += 0.01;
        }

        this.renderer.render(this.scene, this.camera);
    }

    // Control methods
    resetView() {
        // Get current model to adjust view accordingly
        const currentModel = this.modelBuilder.getCurrentModel();
        if (currentModel) {
            const box = new THREE.Box3().setFromObject(currentModel);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxSize = Math.max(size.x, size.y, size.z);
            
            // Use same simple positioning logic as buildModel
            const cameraDistance = maxSize * 1.5 + 2;
            
            this.camera.position.set(
                cameraDistance * 0.7, 
                cameraDistance * 0.5, 
                cameraDistance * 0.7
            );
            this.camera.lookAt(center);
        } else {
            this.camera.position.set(6, 4, 6);
            this.camera.lookAt(0, 0, 0);
        }
    }

    toggleWireframe() {
        this.wireframeMode = !this.wireframeMode;
        this.modelBuilder.updateWireframe(this.wireframeMode);
        return this.wireframeMode;
    }

    toggleAnimation() {
        this.animationEnabled = !this.animationEnabled;
        return this.animationEnabled;
    }

    toggleAxes() {
        this.axesHelper.visible = !this.axesHelper.visible;
        return this.axesHelper.visible;
    }

    buildModel(code) {
        try {
            const result = this.modelBuilder.build(code, this.scene);
            
            if (result) {
                // Much simpler and more direct camera positioning
                const maxSize = Math.max(result.size.x, result.size.y, result.size.z);
                
                // Simple, direct camera distance calculation
                const cameraDistance = maxSize * 1.5 + 2; // Much closer!
                
                // Position camera closer with a good viewing angle
                this.camera.position.set(
                    cameraDistance * 0.7, 
                    cameraDistance * 0.5, 
                    cameraDistance * 0.7
                );
                this.camera.lookAt(result.center);
                
                // Update axes helper size
                this.axesHelper.scale.setScalar(Math.max(maxSize * 0.2, 0.5));
                
                this.modelBuilder.updateWireframe(this.wireframeMode);
                
                console.log(`📹 Camera at distance: ${cameraDistance.toFixed(2)}, model size: ${maxSize.toFixed(2)}`);
                console.log(`📍 Camera position: (${this.camera.position.x.toFixed(2)}, ${this.camera.position.y.toFixed(2)}, ${this.camera.position.z.toFixed(2)})`);
                
                return result;
            }
        } catch (error) {
            throw error;
        }
    }

    buildRawThreeJS(code) {
        try {
            console.log('🎮 Building raw Three.js code...');

            // FAST PATH: nuke the current scene so eval starts fresh
            while (this.scene.children.length) {
                const obj = this.scene.children.pop();
                obj.geometry?.dispose?.();
                obj.material?.dispose?.();
            }
            
            // Re-add the basic lighting and ground after clearing
            this.setupLighting();
            
            // Reset camera to default position
            this.resetView();

            // The one-liner that "opens the floodgates":
            try {
                new Function('THREE', 'scene', 'camera', 'renderer', 'controls', code)(
                    THREE, this.scene, this.camera, this.renderer, { reset: () => this.resetView() }
                );
                console.log('✅ Raw Three.js code executed successfully');
                return { success: true };
            } catch (execError) {
                console.error('❌ Raw Three.js Build Error:', execError.message);
                alert('Error in user code: ' + execError.message);
                throw execError;
            }

        } catch (error) {
            console.error('❌ Raw Three.js Build Error:', error.message);
            throw error;
        }
    }

    getScene() {
        return this.scene;
    }

    getCamera() {
        return this.camera;
    }

    getRenderer() {
        return this.renderer;
    }

    loadSTL(stlData) {
        try {
            console.log('📥 Parsing STL data...');
            
            // Parse STL data
            const geometry = this.parseSTL(stlData);
            
            // Create material
            const material = new THREE.MeshPhongMaterial({ 
                color: 0x667eea,
                transparent: false,
                opacity: 1.0,
                shininess: 100,
                side: THREE.DoubleSide
            });
            
            // Create mesh
            const mesh = new THREE.Mesh(geometry, material);
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            
            // Clear previous model
            if (this.modelBuilder.currentModel) {
                this.scene.remove(this.modelBuilder.currentModel);
            }
            
            // Add to scene
            this.scene.add(mesh);
            this.modelBuilder.currentModel = mesh;
            
            // Position camera to view the model
            const box = new THREE.Box3().setFromObject(mesh);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            const maxSize = Math.max(size.x, size.y, size.z);
            
            const cameraDistance = maxSize * 1.5 + 2;
            this.camera.position.set(
                cameraDistance * 0.7, 
                cameraDistance * 0.5, 
                cameraDistance * 0.7
            );
            this.camera.lookAt(center);
            
            console.log('✅ STL model loaded and positioned');
            return mesh;
            
        } catch (error) {
            console.error('❌ STL Loading Error:', error);
            throw error;
        }
    }

    parseSTL(stlData) {
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const normals = [];
        
        // Check if it's ASCII STL (starts with 'solid')
        if (typeof stlData === 'string' && stlData.trim().startsWith('solid')) {
            // Parse ASCII STL
            return this.parseASCIISTL(stlData, geometry, vertices, normals);
        } else {
            // Parse Binary STL
            return this.parseBinarySTL(stlData, geometry);
        }
    }

    parseASCIISTL(stlData, geometry, vertices, normals) {
        // Parse ASCII STL
        const lines = stlData.split('\n');
        let currentFacet = null;
        let vertexCount = 0;
        
        for (let line of lines) {
            line = line.trim();
            
            if (line.startsWith('facet normal')) {
                const parts = line.split(' ');
                if (parts.length < 5) {
                    throw new Error(`Invalid facet normal line: ${line}`);
                }
                currentFacet = {
                    normal: [parseFloat(parts[2]), parseFloat(parts[3]), parseFloat(parts[4])],
                    vertices: []
                };
            } else if (line.startsWith('vertex')) {
                if (!currentFacet) {
                    throw new Error(`Vertex found outside of facet: ${line}`);
                }
                const parts = line.split(' ');
                if (parts.length < 4) {
                    throw new Error(`Invalid vertex line: ${line}`);
                }
                currentFacet.vertices.push([
                    parseFloat(parts[1]), 
                    parseFloat(parts[2]), 
                    parseFloat(parts[3])
                ]);
            } else if (line.startsWith('endfacet')) {
                if (!currentFacet || currentFacet.vertices.length !== 3) {
                    throw new Error(`Invalid facet: expected 3 vertices, got ${currentFacet?.vertices?.length || 0}`);
                }
                // Add triangle to geometry
                for (let vertex of currentFacet.vertices) {
                    vertices.push(vertex[0], vertex[1], vertex[2]);
                    normals.push(currentFacet.normal[0], currentFacet.normal[1], currentFacet.normal[2]);
                }
                vertexCount += 3;
                currentFacet = null;
            }
        }
        
        if (vertices.length === 0) {
            throw new Error('No valid triangles found in ASCII STL data');
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
        geometry.computeBoundingBox();
        
        console.log(`📏 Parsed ASCII STL: ${vertexCount} vertices, ${vertexCount / 3} triangles`);
        return geometry;
    }

    parseBinarySTL(buffer, geometry) {
        // Parse Binary STL
        console.log('📥 Parsing binary STL data...');
        
        // Convert string to ArrayBuffer if needed
        let dataView;
        if (typeof buffer === 'string') {
            // Convert string to ArrayBuffer
            const encoder = new TextEncoder();
            const uint8Array = encoder.encode(buffer);
            dataView = new DataView(uint8Array.buffer);
        } else if (buffer instanceof ArrayBuffer) {
            dataView = new DataView(buffer);
        } else {
            throw new Error('Unsupported STL data format');
        }
        
        // Binary STL format:
        // 80-byte header + 4-byte triangle count + triangles
        if (dataView.byteLength < 84) {
            throw new Error('Binary STL file too small');
        }
        
        // Read triangle count (4 bytes at offset 80)
        const triangleCount = dataView.getUint32(80, true); // little endian
        console.log(`📏 Binary STL contains ${triangleCount} triangles`);
        
        const vertices = [];
        const normals = [];
        
        // Each triangle is 50 bytes: 12 bytes normal + 36 bytes vertices + 2 bytes attribute
        for (let i = 0; i < triangleCount; i++) {
            const offset = 84 + i * 50;
            
            // Read normal (3 floats)
            const nx = dataView.getFloat32(offset, true);
            const ny = dataView.getFloat32(offset + 4, true);
            const nz = dataView.getFloat32(offset + 8, true);
            
            // Read 3 vertices (9 floats total)
            for (let j = 0; j < 3; j++) {
                const vertexOffset = offset + 12 + j * 12;
                const x = dataView.getFloat32(vertexOffset, true);
                const y = dataView.getFloat32(vertexOffset + 4, true);
                const z = dataView.getFloat32(vertexOffset + 8, true);
                
                vertices.push(x, y, z);
                normals.push(nx, ny, nz);
            }
        }
        
        if (vertices.length === 0) {
            throw new Error('No valid triangles found in binary STL data');
        }
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
        geometry.computeBoundingBox();
        
        console.log(`📏 Parsed binary STL: ${vertices.length / 3} vertices, ${triangleCount} triangles`);
        return geometry;
    }
} 